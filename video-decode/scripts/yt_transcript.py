#!/usr/bin/env python3
"""yt_transcript.py — 视频字幕一键转写 (video-decode skill 的确定性部分)

用法:
    python yt_transcript.py --url URL [--langs zh,en] [--workdir DIR]

输出:
    <workdir>/transcript.txt   清洗后的纯文本 (按 500 字换行, 防 Read 工具单行截断)
    <workdir>/meta.json        标题/时长/上传日期/频道/播放量等元数据

退出码:
    0 = 成功
    2 = 无可用字幕 -> 走 ASR 降级 (见 references/toolchain-notes.md)
    3 = YouTube 机器人验证 (BOT_CHECK) -> 冷却重试或传 cookies (见 toolchain-notes.md)
    1 = 其他错误 (网络/视频不可用/依赖安装失败等)
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile


def ensure_ytdlp():
    try:
        import yt_dlp  # noqa: F401
        return
    except ImportError:
        print("[setup] yt-dlp 未安装, 正在通过 pip 安装 ...")
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"])
        if r.returncode != 0:
            print("ERROR: yt-dlp 安装失败, 请手动执行: python -m pip install yt-dlp")
            sys.exit(1)


def pick_sub(info, langs):
    """字幕择优: 官方字幕 > 原声自动字幕 > 翻译字幕。返回 (kind, lang) 或 (None, None)。"""
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    for L in langs:
        if L in manual:
            return "manual", L
    for L in langs:
        for k in manual:
            if k.startswith(L):
                return "manual", k
    for L in langs:
        if L in auto:
            return "auto", L
    for L in langs:
        for k in auto:
            if k.startswith(L + "-"):
                return "auto", k
    if auto:
        for k in auto:
            if "-" not in k:
                return "auto", k
        return "auto", next(iter(auto))
    return None, None


def download_subs(url, workdir, kind, lang, base_opts):
    """用第二次 yt-dlp 提取下载字幕文件, 返回文件路径或 None。"""
    import yt_dlp

    opts = dict(base_opts)
    opts.update(
        {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "outtmpl": os.path.join(workdir, "video.%(ext)s"),
            "subtitleslangs": [lang],
            "subtitlesformat": "vtt",
        }
    )
    if kind == "manual":
        opts["writesubtitles"] = True
    else:
        opts["writeautomaticsub"] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    cands = glob.glob(os.path.join(workdir, "video.*.vtt"))
    return cands[0] if cands else None


_W = re.compile(r"[A-Za-z0-9\u00C0-\u024F]")
_CJK = re.compile(r"[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]")
_EN_NOSPACE_AFTER = set("-—–&/([{")
_CJK_END_PUNCT = set("、。，；：！？）】》…\"'")
_CJK_START_PUNCT = set("、。，；：！？）】》……「『\"'")


def _boundary_space(prev_char, next_char):
    """行级拼接时是否补空格: 西文↔西文补; CJK 边界不补。"""
    if _CJK.search(prev_char) or _CJK.search(next_char):
        return False
    if prev_char in _CJK_END_PUNCT and next_char not in _W.pattern:
        return False
    if prev_char in _EN_NOSPACE_AFTER:
        return False
    if _W.search(prev_char) and _W.search(next_char):
        return True
    # 英文句子标点后接西文 → 新句, 也要补空格
    if prev_char in ".,;:!?)]}\"'" and _W.search(next_char):
        return True
    if next_char in {",", ".", ";", ":", "!", "?", ")", "]", "}", "…"}:
        return False
    if next_char in _EN_NOSPACE_AFTER:
        return False
    if prev_char.isspace() or next_char.isspace():
        return False
    return _W.search(prev_char) is not None and _W.search(next_char)


def clean_vtt(path):
    """VTT -> 纯文本。去时间戳/标签/滚动重复行; 西文行间断行处补空格。返回 (全文, 换行版)。"""
    with open(path, encoding="utf-8-sig") as f:
        raw = f.read()
    out = []
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or "-->" in s:
            continue
        if s.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE", "REGION")):
            continue
        s = re.sub(r"<[^>]+>", "", s).strip()
        if not s:
            continue
        if out and out[-1] == s:
            continue
        if out and _boundary_space(out[-1][-1], s[0]):
            out.append(" ")
        out.append(s)
    text = "".join(out)
    wrapped = "\n".join(text[i : i + 500] for i in range(0, len(text), 500))
    return text, wrapped


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="视频字幕一键转写")
    ap.add_argument("--url", required=True)
    ap.add_argument("--langs", default="zh,zh-Hans,zh-Hant,en", help="语言优先清单, 逗号分隔")
    ap.add_argument("--workdir", default=None, help="输出目录 (默认临时目录/video-decode/<id>)")
    ap.add_argument("--cookies-from-browser", default=None, help="浏览器名 edge/chrome/firefox (BOT_CHECK 时用, 需先退出浏览器)")
    ap.add_argument("--cookies", default=None, help="cookies.txt 文件路径")
    ap.add_argument("--player-client", default=None, help="强制 youtube player_client (逗号分隔), 如 mweb (cookies 场景下 web 客户端会报 'page needs to be reloaded')")
    ap.add_argument("--js-runtimes", default=None, help="启用 JS 运行时 (逗号分隔), 如 node 或 node:C:\\path\\node.exe")
    ap.add_argument("--remote-components", default=None, help="允许的远程组件 (逗号分隔), 如 ejs:github (nsig 求解脚本)")
    args = ap.parse_args()
    langs = [x.strip() for x in args.langs.split(",") if x.strip()]

    ensure_ytdlp()
    import yt_dlp

    base_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "ignore_no_formats_error": True,
    }
    if args.cookies_from_browser:
        base_opts["cookiesfrombrowser"] = (args.cookies_from_browser,)
    if args.cookies:
        base_opts["cookiefile"] = args.cookies
    if args.player_client:
        base_opts.setdefault("extractor_args", {}).setdefault("youtube", {})["player_client"] = [
            x.strip() for x in args.player_client.split(",") if x.strip()
        ]
    if args.js_runtimes:
        jr = {}
        for x in args.js_runtimes.split(","):
            x = x.strip()
            if not x:
                continue
            parts = x.split(":", 1)
            jr[parts[0]] = {"path": parts[1] if len(parts) > 1 else None}
        base_opts["js_runtimes"] = jr
    if args.remote_components:
        base_opts["remote_components"] = [
            x.strip() for x in args.remote_components.split(",") if x.strip()
        ]

    try:
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            info = ydl.extract_info(args.url, download=False)
    except Exception as e:
        msg = str(e)
        if "not a bot" in msg or "Sign in to confirm" in msg:
            print("BOT_CHECK: YouTube 触发了机器人验证 (机房 IP 风控, 非脚本问题)。")
            print("  首选持久方案 (本机已装): 加 --cookies \"%LOCALAPPDATA%\\yt-cookies.txt\" --player-client mweb")
            print("  cookies 失效: python scripts/yt_cookies.py 刷新 (约 10 秒, 默认输出即上述路径)")
            print("  无持久方案时: 冷却几分钟~几小时后重试; cookies-from-browser 对现代 Chrome/Edge 已死 (ABE), 不要依赖")
            print("  详见 references/toolchain-notes.md")
            sys.exit(3)
        print(f"ERROR: 视频信息提取失败: {e}")
        sys.exit(1)

    vid = info.get("id") or "video"
    workdir = args.workdir or os.path.join(tempfile.gettempdir(), "video-decode", vid)
    os.makedirs(workdir, exist_ok=True)

    meta = {
        k: info.get(k)
        for k in ("id", "title", "duration", "upload_date", "channel", "view_count", "like_count", "webpage_url")
    }
    meta_path = os.path.join(workdir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[meta] {meta.get('title')}")
    print(f"[meta] duration={meta.get('duration')}s upload={meta.get('upload_date')} channel={meta.get('channel')}")

    kind, lang = pick_sub(info, langs)
    if not kind:
        print("NO_SUBTITLES: 该视频没有可下载的字幕, 请按 references/toolchain-notes.md 的 ASR 降级阶梯处理")
        sys.exit(2)

    vtt = download_subs(args.url, workdir, kind, lang, base_opts)
    if vtt is None and kind == "manual":
        kind = "auto"
        vtt = download_subs(args.url, workdir, kind, lang, base_opts)
    if vtt is None:
        print("NO_SUBTITLES: 字幕下载失败 (可能被限流), 可重试或走 ASR 降级")
        sys.exit(2)

    text, wrapped = clean_vtt(vtt)
    txt_path = os.path.join(workdir, "transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(wrapped)

    dur = meta.get("duration") or 0
    cpm = round(len(text) / (dur / 60), 1) if dur else None
    warn = []
    if dur and cpm is not None and not (80 <= cpm <= 450):
        warn.append(f"chars/min={cpm} 异常, 字幕可能不完整 (检查是否有滚动重复或大段音乐)")
    if len(text) < 100:
        warn.append("文本过短, 疑似字幕缺失")

    print(f"[sub] source={kind} lang={lang} file={os.path.basename(vtt)}")
    print(f"[out] chars={len(text)} chars_per_min={cpm}")
    print(f"[out] TRANSCRIPT: {txt_path}")
    print(f"[out] META: {meta_path}")
    if warn:
        print("[warn] " + "; ".join(warn))


if __name__ == "__main__":
    main()
