#!/usr/bin/env python3
"""
macro-market-radar 数据拉取脚本

拉取全球主要市场指数快照 + 关键指数区间涨跌幅 + 可用的宏观指标,
输出结构化 JSON (默认) 或 Markdown 供 LLM 解读。

设计约束 (实测于 2026-09, 本机网络环境):
- 东财源可用但偶发 RemoteDisconnected -> 每只指数独立容错 + 重试
- 金十源 (macro_usa_* 等) 不稳定 -> 全部容错, 失败标记 skipped
- 本机 7890 本地代理会挡东财 -> 进程级清掉代理环境变量 (不动 trust_env,
  避免污染 akshare 内部 requests 行为)

用法:
    python fetch_macro_data.py [--format json|md] [--output PATH]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# 本机 Clash 等本地代理会挡掉东财行情接口 -> 清代理环境变量
for k in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(k, None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import warnings

warnings.filterwarnings("ignore")

try:
    import pandas as pd
    import akshare as ak
except ImportError:
    print("缺少依赖 pandas/akshare。请先: uv pip install --python <venv-python> akshare pandas", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------
# 核心指数: (名称, 历史接口 symbol)
# 名称均经 2026-09 实测可用 (东财 index_global_hist_em / stock_zh_index_daily_em)
# ---------------------------------------------------------------
CORE_INDICES = [
    # A股
    {"name": "上证指数", "symbol": "sh000001", "type": "cn"},
    {"name": "深证成指", "symbol": "sz399001", "type": "cn"},
    # 港股
    {"name": "恒生指数", "symbol": "恒生指数", "type": "global"},
    {"name": "国企指数", "symbol": "国企指数", "type": "global"},
    # 亚太
    {"name": "日经225", "symbol": "日经225", "type": "global"},
    # 欧洲
    {"name": "英国富时100", "symbol": "英国富时100", "type": "global"},
]
# 注: 美股三大指数不做历史请求 (减少东财请求量以降低封禁风险),
# 其当日涨跌由 global_spot 快照覆盖; 如需区间趋势用 web_search 补充。

# 宏观指标: (显示名, 拉取函数名)。全部容错, 失败标 skipped。
MACRO_INDICATORS = [
    ("中国官方制造业PMI", "macro_china_pmi"),
    ("中国GDP", "macro_china_gdp"),
]

# ---------------------------------------------------------------
# 历史指数本地缓存
# 指数日线一天只变一次, 缓存到本地 JSON, 避免每次运行都拉全量历史
# (全量历史请求是触发东财封禁的主因)。每天最多拉一次。
# ---------------------------------------------------------------
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
HIST_CACHE_FILE = os.path.join(CACHE_DIR, "index_history.json")
CACHE_MAX_ROWS = 400  # 只需保留够算 60 日涨跌幅的行数


def _load_history_cache():
    """加载历史缓存 {index_name: {date: close}}。"""
    if not os.path.exists(HIST_CACHE_FILE):
        return {}
    try:
        with open(HIST_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_history_cache(cache):
    """保存历史缓存。"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    tmp = HIST_CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    os.replace(tmp, HIST_CACHE_FILE)


def _cache_fresh(cache, name, today):
    """缓存今天是否已处理过该指数 (成功或失败)。

    _meta[name] == today       -> 今天已成功缓存
    _meta[name] == today:fail  -> 今天已尝试但失败 (冷却, 不再重试)
    """
    meta = cache.get("_meta", {})
    return meta.get(name) == today or meta.get(name) == f"{today}:fail"


def _cache_had_success(cache, name, today):
    """今天是否成功缓存过该指数 (区别于失败冷却)。"""
    return cache.get("_meta", {}).get(name) == today


def _mark_cache_failed(cache, name, today):
    """标记该指数今日尝试失败 (冷却到明天)。"""
    cache.setdefault("_meta", {})[name] = f"{today}:fail"
    _save_history_cache(cache)


def _set_cache_fresh(cache, name, today):
    cache.setdefault("_meta", {})[name] = today


def update_index_cache(item, today, force=False):
    """更新单只指数缓存, 返回升序 DataFrame(date/close) 或 None。

    成功: 今天缓存, 当天后续运行直接命中 (0 请求)。
    失败: 标记今日失败冷却, 当天不再重试 (避免在东财封禁时反复退避耗时)。
    """
    cache = _load_history_cache()
    name = item["name"]

    if not force and _cache_had_success(cache, name, today):
        rows = cache.get(name)
        if rows:
            df = pd.DataFrame(rows)
            df["date"] = df["date"].astype(str)
            return df.sort_values("date").reset_index(drop=True)

    if not force and _cache_fresh(cache, name, today) and not _cache_had_success(cache, name, today):
        # 今日已尝试但失败, 冷却中
        return None

    # 拉全量历史
    df = None
    if item["type"] == "cn":
        # A股指数: 东财优先, 失败自动切新浪 (独立通道, 东财封禁时可用)
        df = safe_call(ak.stock_zh_index_daily_em, symbol=item["symbol"])
        if df is None or df.empty:
            # 新浪接口用同样带市场前缀的代码
            df = safe_call(ak.stock_zh_index_daily, symbol=item["symbol"], retries=1)
            if df is not None and not df.empty:
                df = df.rename(columns={"date": "date", "close": "close"})
        if df is None or df.empty:
            _mark_cache_failed(cache, name, today)
            return None
        df = df[["date", "close"]]
    else:
        df = safe_call(ak.index_global_hist_em, symbol=item["symbol"])
        if df is None or df.empty:
            _mark_cache_failed(cache, name, today)
            return None
        # 东财全球指数历史列: 日期/代码/名称/今开/最新价/最高/最低/振幅
        df = df.rename(columns={"日期": "date", "最新价": "close"})
        df = df[["date", "close"]]

    df["date"] = df["date"].astype(str)
    df = df.sort_values("date").reset_index(drop=True)
    # 存最近 CACHE_MAX_ROWS 行 (足够算 60 日涨跌幅)
    rows = df.tail(CACHE_MAX_ROWS)
    cache[name] = rows.to_dict(orient="records")
    _set_cache_fresh(cache, name, today)
    _save_history_cache(cache)
    return rows.reset_index(drop=True)


_LAST_REQUEST_TIME = 0.0


def safe_call(fn, *args, retries=3, base_delay=2.0, **kwargs):
    """调用 akshare 接口并容错 + 指数退避重试。

    东财源对连续请求会 RemoteDisconnected 限流, 因此:
    - 每次请求前全局节流 (至少间隔 1.2s)
    - 失败后指数退避 (base_delay * 2^attempt)
    """
    global _LAST_REQUEST_TIME
    # 全局节流: 避免短时间密集请求触发东财限流
    elapsed = time.time() - _LAST_REQUEST_TIME
    if elapsed < 1.2:
        time.sleep(1.2 - elapsed)
    _LAST_REQUEST_TIME = time.time()

    for attempt in range(retries + 1):
        try:
            df = fn(*args, **kwargs)
            if df is None:
                return None
            return df
        except Exception:
            if attempt < retries:
                time.sleep(base_delay * (2 ** attempt))
    return None


def compute_returns(hist_df, date_col, close_col):
    """从历史日线 DataFrame 计算 1/5/20/60 日涨跌幅(%)。数据需升序。"""
    if hist_df is None or hist_df.empty:
        return None
    df = hist_df.sort_values(date_col).reset_index(drop=True)
    closes = df[close_col].astype(float)
    last = closes.iloc[-1]
    out = {"last_close": round(float(last), 2), "date": str(df[date_col].iloc[-1])}
    for label, n in [("d1", 1), ("d5", 5), ("d20", 20), ("d60", 60)]:
        out[f"ret_{label}"] = (
            round((last / closes.iloc[-1 - n] - 1) * 100, 2) if len(closes) > n else None
        )
    return out


def fetch_global_spot():
    """全球指数实时快照 (东财, 56 个)。"""
    df = safe_call(ak.index_global_spot_em)
    if df is None or df.empty:
        return None
    df = df.rename(columns={"代码": "code", "名称": "name", "最新价": "price",
                            "涨跌幅": "pct_chg", "涨跌额": "chg", "最新行情时间": "time"})
    return df


def fetch_core_indices(force_refresh=False):
    """核心指数的区间涨跌幅 (走本地缓存, 每天最多拉一次全量历史)。"""
    today = datetime.now().strftime("%Y-%m-%d")
    results = {}
    for item in CORE_INDICES:
        hist = update_index_cache(item, today, force=force_refresh)
        results[item["name"]] = compute_returns(hist, "date", "close") if hist is not None else None
    return results


def fetch_macro():
    """宏观指标, 返回 {name: {status, ...}}。"""
    out = {}
    for display, fn_name in MACRO_INDICATORS:
        fn = getattr(ak, fn_name, None)
        if fn is None:
            out[display] = {"status": "skipped", "reason": "no such interface"}
            continue
        df = safe_call(fn)
        if df is None or df.empty:
            out[display] = {"status": "failed", "reason": "fetch error"}
            continue
        try:
            head = df.head(3).to_dict(orient="records")
            out[display] = {"status": "ok", "columns": list(df.columns), "latest": head}
        except Exception as e:
            out[display] = {"status": "failed", "reason": str(e)[:100]}
    return out


def fetch_cn_sectors():
    """A股行业板块强弱 (东财, 全市场 496 个板块)。

    返回结构化 dict: 领涨前 8 / 领跌前 5 / 板块总数 / 上涨下跌家数。
    全部容错, 失败返回 None。
    """
    df = safe_call(ak.stock_board_industry_name_em)
    if df is None or df.empty:
        return None
    try:
        # 统一列名
        df = df.rename(columns={
            "板块名称": "name", "涨跌幅": "pct_chg", "总市值": "mktcap",
            "上涨家数": "up_count", "下跌家数": "down_count",
            "领涨股票": "leader", "领涨股票-涨跌幅": "leader_pct",
            "换手率": "turnover",
        })
        up = df[df["pct_chg"] > 0]
        down = df[df["pct_chg"] < 0]
        top_gain = df.nlargest(8, "pct_chg")[["name", "pct_chg", "leader", "leader_pct"]]
        top_loss = df.nsmallest(5, "pct_chg")[["name", "pct_chg", "leader", "leader_pct"]]
        return {
            "total": len(df),
            "up_count": len(up),
            "down_count": len(down),
            "top_gainers": top_gain.to_dict(orient="records"),
            "top_losers": top_loss.to_dict(orient="records"),
        }
    except Exception as e:
        return {"error": str(e)[:120]}


def fetch_market_breadth():
    """A股市场宽度/赚钱效应 (乐咕源, 独立于东财, 稳定)。

    返回: 上涨/下跌/涨停/真实涨停/跌停/活跃度 等。失败返回 None。
    """
    df = safe_call(ak.stock_market_activity_legu, retries=2)
    if df is None or df.empty:
        return None
    try:
        kv = dict(zip(df["item"].astype(str), df["value"]))
        return {
            "up": kv.get("上涨"),
            "down": kv.get("下跌"),
            "flat": kv.get("平盘"),
            "limit_up": kv.get("涨停"),
            "real_limit_up": kv.get("真实涨停"),
            "limit_down": kv.get("跌停"),
            "real_limit_down": kv.get("真实跌停"),
            "activity": kv.get("活跃度"),
            "date": kv.get("统计日期"),
        }
    except Exception as e:
        return {"error": str(e)[:120]}


def fetch_hsgt_flow():
    """沪深港通南北向资金 (东财)。失败返回 None。"""
    df = safe_call(ak.stock_hsgt_fund_flow_summary_em, retries=2)
    if df is None or df.empty:
        return None
    try:
        # 只保留需要的列
        keep = [c for c in ["交易日", "类型", "板块", "资金方向", "成交净买额",
                            "资金净流入", "上涨数", "下跌数", "相关指数", "指数涨跌幅"] if c in df.columns]
        df = df[keep]
        return {"rows": df.to_dict(orient="records"), "cols": keep}
    except Exception as e:
        return {"error": str(e)[:120]}


def _summarize(payload):
    """数据健康度摘要: 哪些数据块成功/失败, 供 agent 决定是否搜索补充。"""
    health = {}
    spot = payload.get("global_spot")
    health["global_spot"] = "ok" if spot is not None and not spot.empty else "failed"
    core = payload.get("core_indices") or {}
    ok_core = [k for k, v in core.items() if v is not None]
    health["core_indices"] = f"{len(ok_core)}/{len(core)} ok" if core else "failed"
    sectors = payload.get("cn_sectors")
    health["cn_sectors"] = "ok" if sectors and not sectors.get("error") else "failed"
    breadth = payload.get("market_breadth")
    health["market_breadth"] = "ok" if breadth and not breadth.get("error") else "failed"
    hsgt = payload.get("hsgt_flow")
    health["hsgt_flow"] = "ok" if hsgt and not hsgt.get("error") else "failed"
    macro = payload.get("macro") or {}
    ok_macro = [k for k, v in macro.items() if v and v.get("status") == "ok"]
    health["macro"] = f"{len(ok_macro)}/{len(macro)} ok" if macro else "failed"
    return health


def build_payload():
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "global_spot": fetch_global_spot(),
        "core_indices": fetch_core_indices(),
        "cn_sectors": fetch_cn_sectors(),
        "market_breadth": fetch_market_breadth(),
        "hsgt_flow": fetch_hsgt_flow(),
        "macro": fetch_macro(),
    }
    payload["data_health"] = _summarize(payload)
    return payload


def _json_default(o):
    if hasattr(o, "item"):
        try:
            return o.item()
        except Exception:
            pass
    return str(o)


def to_json(payload):
    return json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default)


def _confidence_note(payload):
    """数据可信度自评: 告诉使用方本次结论建立在什么数据上。

    区分: 实时 (今日) / 缓存 (可能滞后, 标注日期) / 缺失 (需搜索)。
    这是"盲区声明"——让 agent 和用户知道哪些结论扎实、哪些是补的。
    """
    notes = []
    health = payload.get("data_health") or {}

    spot = payload.get("global_spot")
    if spot is not None and not spot.empty:
        notes.append("全球指数: 实时快照")
    else:
        notes.append("全球指数: **缺失, 需搜索**")

    core = payload.get("core_indices") or {}
    ok_core = {k: v for k, v in core.items() if v}
    if ok_core:
        dates = sorted({v.get("date", "?") for v in ok_core.values()})
        notes.append(f"核心指数历史: 缓存数据, 最新日期 {dates[-1] if dates else '?'} ({len(ok_core)}/{len(core)} 只有 {', '.join(ok_core.keys())})")
    else:
        notes.append("核心指数历史: **缺失, 需搜索**")

    sectors = payload.get("cn_sectors")
    notes.append(f"A股板块: {'实时' if sectors and not sectors.get('error') else '**缺失, 需搜索**'}")

    breadth = payload.get("market_breadth")
    if breadth and not breadth.get("error"):
        notes.append(f"市场宽度: 实时 (统计至 {breadth.get('date', '?')})")
    else:
        notes.append("市场宽度: **缺失, 需搜索**")

    hsgt = payload.get("hsgt_flow")
    notes.append(f"南北向资金: {'实时' if hsgt and not hsgt.get('error') else '**缺失, 需搜索**'}")

    macro = payload.get("macro") or {}
    ok_macro = [k for k, v in macro.items() if v and v.get("status") == "ok"]
    notes.append(f"宏观: {len(ok_macro)}/{len(macro)} 可用 (PMI/GDP 为月/季频, 注意时点)")

    return notes


def to_markdown(payload):
    lines = []
    lines.append("# 全球宏观市场雷达\n")
    lines.append(f"> 生成时间: {payload['generated_at']}")

    # 数据健康度摘要
    health = payload.get("data_health") or {}
    if health:
        lines.append(">")
        lines.append(f"> 数据状态: 全球指数快照={health.get('global_spot','?')} | "
                     f"核心指数历史={health.get('core_indices','?')} | "
                     f"A股板块={health.get('cn_sectors','?')} | "
                     f"市场宽度={health.get('market_breadth','?')} | "
                     f"南北向资金={health.get('hsgt_flow','?')} | "
                     f"宏观={health.get('macro','?')}")
        failed_parts = [k for k, v in health.items() if v == "failed" or (isinstance(v, str) and v.startswith("0/"))]
        if failed_parts:
            lines.append(f"> **⚠ 以下数据块拉取失败, 需用 web_search 联网补充**: {', '.join(failed_parts)}")
    lines.append("")

    spot = payload.get("global_spot")
    if spot is not None and not spot.empty:
        lines.append("## 全球主要指数快照")
        lines.append("")
        lines.append("| 名称 | 代码 | 最新价 | 涨跌幅% | 时间 |")
        lines.append("|---|---|---|---|---|")
        for _, r in spot.iterrows():
            lines.append(f"| {r.get('name','')} | {r.get('code','')} | {r.get('price','')} | {r.get('pct_chg','')} | {r.get('time','')} |")
        lines.append("")

    lines.append("## 核心指数区间涨跌幅 (%)")
    lines.append("")
    lines.append("| 指数 | 最新收盘 | 日期 | 1日 | 5日 | 20日 | 60日 |")
    lines.append("|---|---|---|---|---|---|---|")
    core = payload.get("core_indices") or {}
    for name, r in core.items():
        if r is None:
            lines.append(f"| {name} | - (搜索补充) | - | - | - | - | - |")
            continue
        lines.append(f"| {name} | {r['last_close']} | {r['date']} | {r.get('ret_d1')} | {r.get('ret_d5')} | {r.get('ret_d20')} | {r.get('ret_d60')} |")
    lines.append("")

    # A股板块强弱
    sectors = payload.get("cn_sectors")
    lines.append("## A股行业板块强弱")
    lines.append("")
    if sectors is None or sectors.get("error"):
        lines.append("(板块数据获取失败, 需用 web_search 搜索 'A股 板块 领涨领跌' 补充)")
    else:
        lines.append(f"- 板块总数 {sectors.get('total')} | 上涨 {sectors.get('up_count')} | 下跌 {sectors.get('down_count')}")
        lines.append("")
        lines.append("**领涨板块 (前8):**")
        lines.append("")
        lines.append("| 板块 | 涨跌幅% | 领涨股 | 领涨股涨幅% |")
        lines.append("|---|---|---|---|")
        for r in sectors.get("top_gainers", []):
            lines.append(f"| {r.get('name','')} | {r.get('pct_chg','')} | {r.get('leader','')} | {r.get('leader_pct','')} |")
        lines.append("")
        lines.append("**领跌板块 (前5):**")
        lines.append("")
        lines.append("| 板块 | 涨跌幅% | 领跌股 | 领跌股跌幅% |")
        lines.append("|---|---|---|---|")
        for r in sectors.get("top_losers", []):
            lines.append(f"| {r.get('name','')} | {r.get('pct_chg','')} | {r.get('leader','')} | {r.get('leader_pct','')} |")
        lines.append("")

    # 市场宽度/赚钱效应
    breadth = payload.get("market_breadth")
    lines.append("## A股市场宽度 (赚钱效应)")
    lines.append("")
    if breadth is None or breadth.get("error"):
        lines.append("(市场宽度获取失败, 需用 web_search 搜索 'A股 涨跌家数 涨停' 补充)")
    else:
        lines.append(f"- 统计日期: {breadth.get('date','')} | 活跃度: {breadth.get('activity','')}")
        lines.append(f"- 上涨 {breadth.get('up')} / 下跌 {breadth.get('down')} / 平盘 {breadth.get('flat')}")
        lines.append(f"- 涨停 {breadth.get('limit_up')} (真实 {breadth.get('real_limit_up')}) / "
                     f"跌停 {breadth.get('limit_down')} (真实 {breadth.get('real_limit_down')})")
        # 涨跌比 / 涨停跌停比 信号
        try:
            up = float(breadth.get("up") or 0)
            down = float(breadth.get("down") or 0)
            lu = float(breadth.get("limit_up") or 0)
            ld = float(breadth.get("limit_down") or 0)
            if up + down > 0:
                lines.append(f"- 涨跌比: {up/down:.2f}" if down > 0 else "- 涨跌比: n/a (无下跌)")
            lines.append(f"- 涨停/跌停比: {lu/ld:.1f}" if ld > 0 else f"- 涨停/跌停比: n/a (跌停={ld:.0f})")
        except Exception:
            pass
        lines.append("")

    # 南北向资金
    hsgt = payload.get("hsgt_flow")
    lines.append("## 沪深港通资金 (南北向)")
    lines.append("")
    if hsgt is None or hsgt.get("error"):
        lines.append("(南北向资金获取失败, 需用 web_search 搜索 '北向资金 南向资金 今日' 补充)")
    else:
        lines.append("| 类型 | 板块 | 方向 | 成交净买额(亿) | 资金净流入(亿) | 相关指数 | 指数涨跌幅% |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in hsgt.get("rows", []):
            lines.append(f"| {r.get('类型','')} | {r.get('板块','')} | {r.get('资金方向','')} | "
                         f"{r.get('成交净买额','')} | {r.get('资金净流入','')} | "
                         f"{r.get('相关指数','')} | {r.get('指数涨跌幅','')} |")
        lines.append("")

    lines.append("## 宏观指标 (最新)")
    lines.append("")
    macro = payload.get("macro") or {}
    for name, info in macro.items():
        if info is None:
            lines.append(f"- **{name}**: 无数据")
            continue
        status = info.get("status")
        if status != "ok":
            lines.append(f"- **{name}**: {status} ({info.get('reason','')})")
            continue
        lines.append(f"- **{name}**:")
        for row in info.get("latest", []):
            lines.append(f"  - {row}")
    lines.append("")

    # 数据可信度自评 (盲区声明)
    lines.append("## 数据可信度自评")
    lines.append("")
    for note in _confidence_note(payload):
        lines.append(f"- {note}")
    lines.append("")
    lines.append("---")
    lines.append("*由 macro-market-radar skill 生成, 数据仅供研究参考, 非投资建议。*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="全球宏观市场雷达数据")
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parser.add_argument("--output", default=None, help="输出文件路径, 默认 stdout")
    args = parser.parse_args()

    payload = build_payload()
    text = to_markdown(payload) if args.format == "md" else to_json(payload)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"written: {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
