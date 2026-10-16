---
name: video-decode
description: "把视频链接 (YouTube 等) 变成完整文字稿 + 结构化解读, 并可按需逐项事实核查 (claim-by-claim fact-check)。字幕优先于音频转录。Decode video URLs into clean transcripts, structured interpretation, and optional claim-level verification. TRIGGER: YouTube链接, 视频链接, 解读视频, 这个视频讲了什么, 视频总结, 帮我看看这个视频, 视频转写, 验证一下, 核查视频, 核实视频说法, fact-check video, video transcript, video summary, youtube analysis"
---

# Video Decode — 视频解读与核验

## 定位

**一句话**: 把一个视频链接变成一份"可查证的内容纪要" — 完整文字稿 + 忠实解读 + 观点/事实分家, 说"验证一下"就逐条对质权威信源。角色: 视频版的"记者 + 事实核查员" — 记者负责准确转述, 核查员负责拿作者的说法对质官方/权威信源。

输入一个视频 URL (YouTube 为主), 产出:
1. **完整文字稿** (字幕清洗版, 落盘)
2. **结构化解读** (复述事实 + 核心论点 + 关键数据 + 边界提示)
3. 用户说 "验证一下" 时追加: **逐项事实核查** (四类结论表: ✅属实/⚠️有出入/❌错误/⚖️无法验证, 每条附信源链接)

三条纪律: **观点 ≠ 事实** (作者判断永远标"观点", 不伪装成已核实事实); **不替用户站队** (核查只回答"对不对", 价值判断不打分); **不编造** (搜不到就如实说, 绝不编数据/来源)。

适用对象 (核查价值排序):
- **最佳**: 财经/时政/政策解读 (数据密集, 可核查 claim 多) ｜ 单人口播/深度解说
- **良好**: 多人谈话/播客/访谈 (按主题聚合, 区分亲历/转述/玩笑) ｜ 历史复盘/行业分析 (§7 观点分析价值区)
- **一般**: 教程/科普 (只转写) ｜ 新闻现场报道
- 最优时长 **10~90 分钟**; 过短不值得全流程, 过长建议分段
- **不适用**: 音乐 MV/混剪 (无内容可解) ｜ 刚发布 <1 天的热门视频 (字幕滞后+风控) ｜ 本地文件 (直接 ASR) ｜ 弹幕不算字幕 (bilibili)

## 何时用 / 不该用

用:
- 用户丢视频链接 + "解读/总结/看看/讲了什么" → Phase 1
- 用户接续说 "验证一下/核查/说得对吗" → Phase 2 (不重跑 Phase 1)
- 视频类 URL: youtube.com / youtu.be / bilibili 等 yt-dlp 支持的站点

不用:
- 本地媒体文件转写 → 直接跑 ASR (见 references/toolchain-notes.md)
- 用户只想下载视频 → 直接用 yt-dlp, 不必走本流程
- 图文网页 → 直接 webfetch

## Workflow

### Phase 1: 解读 (默认, 拿到链接就跑)

**Step 1 一键转写** (字幕快路径, 一条命令):

```bash
python scripts/yt_transcript.py --url "URL"
```

脚本自动完成: 装 yt-dlp (缺时) → 提取元数据 → 字幕择优 (官方 > 自动原声 > 翻译) → 下载 VTT → 清洗 (去时间戳/标签/滚动重复行, 按 500 字换行) → 落盘 `transcript.txt` + `meta.json` → 输出健康度。

**Step 2 健康度检查** (读脚本 stdout):
- `TRANSCRIPT:` / `META:` 路径拿到手
- `NO_SUBTITLES` (退出码 2) → **先看 `[meta] duration=` 是否 None**: 是 ⇒ 提取被风控降级 (字幕可能其实存在), 先用持久方案重跑 (`--cookies "%LOCALAPPDATA%\yt-cookies.txt" --player-client mweb`), 别急着 ASR; duration 正常且仍 exit 2 才是真无字幕 → 走 ASR 降级。**本机 (无 NVIDIA) 首选 GPU 快路径**: `python scripts/gpu_asr_constme.py --url "URL"` (AMD DirectCompute, 实测 4~7x 实时, medium 模型已缓存, 缺时自动下载并打印体量)。GPU 不可用时再用 CPU 方案: `python scripts/asr_transcribe.py --url "URL" --model small|medium`, **先告知成本再动手** (模型 0.5~1.5GB, CPU 约 0.5~1x 实时; 试跑 small, 要准 medium)
- `BOT_CHECK` (退出码 3) → YouTube 临时风控, **不是脚本问题**; **本机已装持久方案**: `--cookies "%LOCALAPPDATA%\yt-cookies.txt" --player-client mweb` (POT provider + 专用登录 profile; 详见 toolchain-notes.md, cookies 过期跑 `scripts/yt_cookies.py` 刷新), 不要反复硬试
- `chars_per_min` 异常 (不在 80~450) 或 chars 过短 → 字幕可能残缺, 在解读中如实标注

**Step 3 通读全文** — Read `transcript.txt` (已按 500 字换行, 不会触发单行 2000 字符截断)。长视频分段读完整, 不要只读开头就总结。

**Step 3.5 术语/专名失真处理** (通读时随手做; 数字留到 Phase 2):
- 疑似听错/识别错的术语、专名 → **只标注不静默改写**: 高置信写 "疑为 X", 低置信标 "此处可能失真"; 原稿 `transcript.txt` 永不修改
- 会进解读稿的高价值术语 (政策工具名/机构名/人名) 可按需联网仲裁, **三条件**同时满足才在解读中写 "实为 X (附来源)": ① 候选词在 T1/T2 来源真实存在 ② 原词在语境中不成立 (不成词/与史实矛盾) ③ 替换后语义自洽; 否则保留 "疑为 X" 或标存疑
- 检索无果 ≠ 原词错误 (弱证据); **宁可漏纠, 不可错纠** (漏纠会被官方原文自然纠正, 错纠是无痕注入新错误)

**Step 4 输出结构化解读** (模板):

```
## 基本信息
频道/发布日期/时长/主题 (来自 meta.json)
## 视频讲了什么 (逐点复述)
按内容顺序 3~7 点, 忠实复述
(多人谈话型: 按主题聚合而非时间线; 标注"字幕无说话人区分"; 区分亲历/转述/玩笑自嘲; 专名失真风险更高)
## 核心论点 (作者观点)
作者的判断/结论, 标注"作者观点"
## 关键数据
数字 + 出处 (视频引用), 提示"字幕自动识别, 个别数字可能有误"
## 备注
ASR 失真点 / 明显口误 / 视频中的特殊事件
```

**Step 5 收尾** — 告知文字稿路径; 主动问一句是否需要逐项核查 (Phase 2)。

### Phase 2: 核验 (用户触发 "验证一下" 时)

1. **抽 claims** — 从解读稿中抽出可核查项, 四类: 政策参数 / 数字 / 出处归属 (谁说/哪份文件) / 直接引用; **数字与专名必检索** (不凭印象放过), 术语纠错过三条件 (Step 3.5)
2. **逐项检索** — 批量 `web_search`; 信源分级与检索方法见 `references/factcheck-guide.md`
3. **输出四类结论表**:

| 视频说法 | 结论 | 依据 |
|---|---|---|
| ... | ✅属实 / ⚠️有出入 / ❌错误 / ⚖️无法验证(观点) | 官方文件/权威报道链接 |

4. **总评** — 错误是否影响主逻辑; 明确区分 "事实核查" 与 "观点不可验证"
5. **观点分析** (用户要求 "分析观点合理性" 时) — 拆论点 → **观点结构分层** (裸观点 A / 推理型 B / 混合型 C; 仅 B/C 评级且分维度) → 可验证性分类 → 核查硬事实 → 按 `references/factcheck-guide.md` §7 做论证质量评级 (案例选择性 / 因果跳跃 / 量级夸大 / 共识对照 / 立场识别)

## 入口与示例

入口: 平时只用第一个
- `scripts/yt_transcript.py` — 字幕快路径 (主力)
- `scripts/gpu_asr_constme.py` — 无字幕时的 GPU 快路径 (AMD DirectCompute; 本机首选, 退出码 2 时用)
- `scripts/asr_transcribe.py` — 无字幕时的 CPU ASR 降级 (GPU 不可用时用)
- `scripts/yt_cookies.py` — 刷新 YouTube cookies (BOT_CHECK 持久方案, 无头; 默认输出 `%LOCALAPPDATA%\yt-cookies.txt`)
- `scripts/yt_login_watch.py` — 专用 profile 首次登录监视 + 导出 cookies (默认输出同上)

```bash
# 例 1: 中文视频默认流程
python scripts/yt_transcript.py --url "https://www.youtube.com/watch?v=XXXX"

# 例 2: 英文视频 / 指定输出目录 (默认输出到 %TEMP%/video-decode/<id>)
python scripts/yt_transcript.py --url "https://youtu.be/XXXX" --langs en,zh --workdir "C:/path/out"

# 例 3: 无字幕 (退出码 2) -> GPU 快路径 (本机首选)
python scripts/gpu_asr_constme.py --url "URL"

# 例 3b: GPU 不可用 -> CPU 降级 (先告知成本, 让用户选模型)
python scripts/asr_transcribe.py --url "URL" --model medium --workdir "C:/path/out"

# 例 4: BOT_CHECK 持久方案 (本机已装): 登录态 cookies + mweb 客户端
python scripts/yt_transcript.py --url "URL" --cookies "%LOCALAPPDATA%\yt-cookies.txt" --player-client mweb
```

## 边界与反模式

- **字幕优先, 不要一上来下音频**: 体积/耗时/误差都更差; 只有无字幕时才降级 ASR
- **输出必须换行**: 纯文本按单行写, 超过 2000 字符会被 Read 工具截断 (实测坑)
- **不要在 PowerShell 里手拼 yt-dlp `--print "%(title)s"`**: `%` 会被吞; 脚本用 Python API 规避。手动兜底时用 `--dump-single-json` 管道给 python 且按 `utf-8-sig` 解码 (BOM 坑)
- **ASR/字幕必然有失真**: 数字、专名、金额尤其容易错 (如 "0.3%" 识别成 "零点三亿"); 解读中必须提示
- **观点 ≠ 事实**: 作者结论只标 "观点"; 核验时观点类 claim 写 "无法验证", 不要强行打分
- **搜不到就如实说**, 绝不编数据/编来源
- **长操作设 timeout**: 首次解析/下载可能 1~2 分钟, 下载命令 timeout 建议 ≥300000ms
- **不静默改写原稿术语**: 术语/专名失真只在外挂标注、解读、核查层处理, `transcript.txt` 保持原样 (唯一事实源); 纠错三条件与失败方向见 Step 3.5
- **不做 ASR 后处理三件套** (ITN 数字归一化 / 标点恢复 / 口语去噪): 对下游解读/核查无增益, 归一化/去噪反而有污染保真风险; 术语问题交给 "标注 + 检索仲裁"。若确需人读净化稿, 只做不覆盖原稿的可选轻清理层

## 参考 (一层深度)

- `references/toolchain-notes.md` — 本机环境事实 + PowerShell 坑 + **ASR 降级阶梯 / GPU 快路径** (踩坑/降级时读)
- `references/factcheck-guide.md` — claim 抽取、信源分级、四类结论定义与模板 (Phase 2 时读)

## 演化记录

- v0.1 (2026-10-03): 从一次真实 YouTube 解读+核查会话 (40 分钟中文时政视频) 中提取。固化了当时实测的 5 个坑: py launcher 损坏需用 python shim / PS5.1 管道 BOM / `%` 被吞 / 单行截断 / 无字幕降级路径。初始版本刻意克制: 只覆盖"字幕快路径 + 解读 + 核查"这一条已验证主线。
- v0.1.1 (2026-10-03): 首次实战测试 (bilibili 18.5 分钟视频, 无字幕)。沉淀: 新增 `scripts/asr_transcribe.py` (内置 av19 兼容 shim + Python-API 下载音频); 确认 bilibili 通常只有弹幕无字幕; `%` 模板在 cmd 语义下会丢 URL 参数; medium 模型 ≈0.75x 实时、中文可能输出繁体。
- v0.1.2 (2026-10-03): 首次观点分析实战 (同一 bilibili 视频)。沉淀: factcheck-guide 新增 §7 "观点分析 (合理性+可验证性)" — 论点拆解/可验证性三分类/论证质量四检查/文献对照。实测经验: 作者自举案例常自带反例; 硬事实准确率高但因果概括易夸大。
- v0.1.3 (2026-10-03): 第二次观点分析 (YouTube E265 中国经济视频)。沉淀: §7 增补"共识对照"检查 (对"到头了/没空间/倒计时"类判断, 检索同期专家论坛/官员表态) 与"错误方向检查" (事实错误未必削弱论证, 需判断方向)。
- v0.1.4 (2026-10-03): 第三次观点分析 (YouTube 耶律律视频)。沉淀: §7 检查项细化 — "案例选择性"含**数据终点选择性** (截断在支持结论的时点), "因果跳跃"含**遗漏变量** (略过文献公认主导因素, 如彩礼话题略过性别比失衡)。
- v0.1.5 (2026-10-03): 第四次实战 (83 分钟多人谈话视频, 发布仅 1 天) 遇长时间 BOT_CHECK。沉淀: toolchain-notes 新增"无 cookies 备用路径"清单 (webfetch/oEmbed/Invidious 空字幕/Piped/Cobalt/转录服务逐一实测) + **rssyes.com 播客镜像**路线 + 确认 cookies-from-browser 对现代 Chromium 已死 (App-Bound Encryption, yt-dlp 无解)。实战结论: 极新视频的自动路径普遍滞后 ~1 天, 遇风控时"冷却等待"仍是最可靠主线。
- v0.1.6 (2026-10-03): 第五次实战 (同上视频), 从"等待冷却"升级为**持久解决方案**: bgutil POT provider (script 模式, node 22) + 专用登录 Chrome profile (CDP 铸造 cookies, 不碰用户日常浏览器)。新增 `scripts/yt_login_watch.py` (登录监视+导出) 与 `scripts/yt_cookies.py` (无头刷新); toolchain-notes 记录根因 (FlClash 机房 IP) 与全部死路 (visitor cookies / OAuth 已废弃 / ABE 无法解 / profile 副本清库 / 默认 profile 禁调试)。
- v0.1.7 (2026-10-03): 方法论补强 (用户提问触发)。§7 新增**观点结构分层**: A 裸观点 (价值/预测/修辞) 只标性质**不打分**; B 推理型观点才做分维度合理性评级 (前提/推理/抗反例/结论溢出); C 混合型先分离事实前提与价值前提。纪律: 避免把"不可验证"当"不合理"、避免按立场调分。
- v0.1.8 (2026-10-03): 风控解决方案**全链路验证成功** (E212 官方字幕 25119 字一次拿下)。yt_transcript.py 增强: `--player-client` / `--js-runtimes` / `--remote-components` 透传 + 内置 `ignore_no_formats_error` (无格式时继续出字幕)。已验证组合: cookies + mweb 客户端。
- v0.1.9 (2026-10-03): 多人谈话型首次全流程 (E212 三個水槍手, 83 分钟): Phase 1 按主题聚合 + Phase 2 十五例通报原文逐一核实 (准确率极高, 错误集中在年份口误)。§7 新增**因果方向/时序检查** (制度修订类解释: 实践可能先于制度, 因果倒置)。首次实战应用 A/B/C 观点结构分层。
- v0.1.10 (2026-10-03): 收尾优化。SKILL 主流程直接给出 BOT_CHECK 持久命令 (不再只指向 notes); 新脚本 (`yt_cookies.py` / `yt_login_watch.py`) 注册到入口; 验证媒体格式路径 (cookies + mweb + `--js-runtimes node --remote-components ejs:github`, 格式全出, ASR 降级可用); toolchain-notes 补字幕默认输出路径与 cookies 安全提示; factcheck-guide §1 补多人谈话抽 claim 要点与"字幕错字 vs 发言"区分。
- v0.1.11 (2026-10-04): 健康检查修复 (纯审计发现, 3 处)。① yt_transcript.py 的 BOT_CHECK 兜底提示仍在推荐 cookies-from-browser, 与 notes "该路已死 (ABE)" 结论矛盾 → 改为持久方案优先; ② `yt_cookies.py` 默认输出原为 CWD 下 cookies.txt, 在仓库目录运行会把 Google 登录态写进 repo 且 gitignore 未覆盖 → 改默认输出 `%LOCALAPPDATA%\yt-cookies.txt` + 输出到非常规位置时打印安全提示 + gitignore 加 `cookies.txt`; ③ yt_cookies / yt_login_watch 裸 `sys.argv` 改 argparse (顺带修掉 `--help` 被当成文件名误写 cookies 的事故), 缺 `websocket-client` 时给出 pip 安装提示; ④ 首次入库 (此前一直 untracked)。
- v0.1.12 (2026-10-04): 测试驱动演化。**clean_vtt 行级拼接吃空格** (英文断行词粘连 "rulesand") → 新增 `_boundary_space` 判定补空格: 西文↔西文/数字补, CJK 边界不补, 英文句标点后接新句补, 前联标点不补。测试时踩坑: 测试断言先写反 (句点后以为不补, 实为英文新句要补), 用逐条件复盘纠出; `--help` 实测误触发了 cookies 导出, 印证 ③ argparse 修复的必要性。全流程回归: 离线测试 + bilibili 退出码 2 + YouTube 快路径 + cookies 刷新 (无头, logged_in=True) 通过。
- v0.1.13 (2026-10-04): 首次完整 Phase 1+2 实机测试 (小Lin说 8BN8p5xDkzw 日元干预, 15.7 分钟, 官方 zh 字幕 5205 字)。发现新陷阱: **假 NO_SUBTITLES** — 无 cookies 首跑 exit 2 + `duration=None` (提取被风控降级, 字幕其实存在), 持久方案重跑即成功; 判定规则固化进 SKILL Step 2 与 notes (exit 2 先查 duration)。Phase 2 核查 19 项: 17✅ / 2⚠️ (单周涨幅最高级未证实、"收入1/3"口径待核) / 0❌; "今年超25万亿干预"估算被 MOF 官方数据 (11.73+15.40=27.1兆) 证实。经验: 官方手工字幕的引语可逐字对上报✅ (三村"超过心理层面"原话吻合)。
- v0.1.14 (2026-10-04): 定位补全 (用户协作打磨)。"定位"段从 6 行扩为完整版: 一句话定位 (视频版"记者+事实核查员") + 三件套输出 + 三条纪律 + **适用对象画像** (按核查价值: 财经时政最佳 > 多人谈话/历史复盘 > 教程科普 > 新闻; 时长 10~90 分钟; 不适用: MV/新发布<1天/本地文件/弹幕)。与"何时用/不该用"分工: 定位管"是什么/给谁用", 该节管"何时触发"。
- v0.1.15 (2026-10-05): 实战 (bilibili BV1P8eK62EQt 人口贩卖, 7.3 分钟无字幕) 暴露**陈旧音频误转**: asr_transcribe.py 原用固定 `audio.%(ext)s` + 共享 asr 目录, 目录里残留昨日 55 分钟视频的 `audio.m4a`, yt-dlp 未真正重下, medium 把旧音频整段转完 (15 分钟 timeout 截断后查 raw 内容才发现与目标视频无关)。修复: `--url` 默认 workdir → `<tmp>/video-decode/<id>` (与 yt_transcript 对齐), 音频命名 `audio.<id>.<ext>`, 下载前打印 `[meta] id/duration/title`; notes 增补"ASR 前核对 duration/开头内容"检查。修复后重跑: 436s 音频 454s 转完 (≈1.04x 实时, 比旧实测 0.75x 快), 2790 字 cpm=384。另: URL 带 `&trackid=...` 跟踪参数会被本环境 shell 拆命令, 用干净 URL。
- v0.1.16 (2026-10-05): 同一视频首次完整 Phase 1+2 (bilibili 科普频道"赛雷三分钟", 数据密集型)。Phase 2 抽 20 项: **0 ❌** / 6 ⚠️ (ILO 150亿与2360亿口径拼接、IOM 80%绝对化、农场案"上千名"夸大、芬兰"一分钱不给"简化、王星"遭虐待"系推断、巴勒莫定义说成近年改动) / 2 ⚖️ 检索无果 ("黑奴最猖獗800万同时被奴役"、"鱼奴月薪3000美元"幌子)。经验: 此类中文科普频道**数字大体精确** (4960万/缅12万柬10万/78人/20美分/22年等均可对上官方来源), 失分集中在转述加工的三种模式 → 已沉淀 factcheck-guide §6 两条反模式 (同机构多期数字拼接、估计值绝对化)。专名 ASR 修正清单: 电炸→电诈、王兴→王星、福社→辐射、赛列→赛雷。
- v0.1.17 (2026-10-07): E265 (FearNation "救市三箭", 官方 zh 字幕, 40 分钟) 完整 Phase 1+2。核查 30+ 项 (22✅/6⚠️/3❌/其余⚖️): 政策参数与工具细节全对; 3 处次要错误 (六张网出处归属、两新分担 "6:4/5:5" 应为 85/90/95、"2024 科技再贷款初始 4000 亿" 应为 5000 亿); 1 处高估 (PSL 余额 "约 2 万亿" 实际 6308 亿 — 方向强化其结论, 已入 factcheck-guide §7 错误方向示例)。两轮方法论沉淀 (用户提问触发): ① **术语失真纪律** — 只标注不静默改写原稿; 高价值术语按需联网仲裁, 三条件 (候选词 T1/T2 存在 / 原词语境不成立 / 替换后语义自洽) 满足才升级 "实为 X (附来源)"; 检索无果≠错误; 宁可漏纠不可错纠 → 写入 SKILL Step 3.5 + factcheck-guide §1。② **明确不做 ASR 后处理三件套** (ITN/标点/去噪), 决策与边界写入反模式段 (防未来范围蔓延)。
- v0.1.18 (2026-10-09): 首次 AMD GPU ASR 落地 + "存档号旧稿"实战 (YouTube 老蛮频道 vMN8e_eX1f8, 10 分钟无字幕, Phase 1+2 完整)。沉淀: ① 本机无 NVIDIA (CTranslate2 `get_cuda_device_count()==0`), faster-whisper 用不了 GPU → 新增 `scripts/gpu_asr_constme.py` (Const-me/Whisper 1.12.0 DirectCompute: 自动定位/下载工具与模型、自动选适配器、产物转 transcript.txt/raw; medium 实测 4~7x 实时, 工具/模型缓存于 `%LOCALAPPDATA%\video-decode\const-whisper\`); ② 新坑两项: cookies+mweb 遇 **SABR-only 实验** 时 `bestaudio` 无 URL, 仅 format 18 可用 → 下载格式兜底 `bestaudio/best[ext=mp4]/18`; main.exe stdout 中文乱码但 `-otxt` 产物为 UTF-8 BOM, 模型无语言自动检测必须显式 `-l`; ③ Step 2 降级决策改为 "GPU 快路径优先, CPU 阶梯备胎"; ④ 实战副产品 (未入正文): **"旧稿重发号"识别法** — 上传日期≠成稿日期 (抽样导出日期 + 镜像节目表 + 评论线索), 对解读"当下数据"类内容有直接价值 (此例中视频时间是 2026, 内容锚点却全部指向更早年份)。
- v0.1.19 (2026-10-09): 真无字幕全链路 + 数据扩展分析实战 (YouTube Geo社会观察 zsa4rIXAEg4, 32.6 分钟教育时政, Phase 1+2 完整)。沉淀: ① **真无字幕判定链完整走通**: 无 cookies exit 2 + duration=None → 持久方案重跑 duration=1957 仍 exit 2 → `gpu_asr_constme.py` 一条命令端到端 (下载 86MB/8s + 转写 273s/1957s ≈ **7.2x 实时**, 与用户"约7倍"口径吻合); 手动路径与脚本路径产出经空白归一化比对**完全一致** (8375 字, similarity 1.0) — 脚本可信; ② 手动路径踩坑: 自拼 `bestaudio[ext=m4a]/bestaudio` 在 SABR-only 下误报 "Requested format is not available", 而脚本兜底 `bestaudio/best[ext=mp4]/18` 在 mweb 下实测可选中 format 18 → **验证脚本行为必须用脚本原样参数, 勿用更窄的手动选择器下结论** (曾据此差点误判脚本有 bug); ③ Phase 2 抽 20+ 项: **0❌** / 4⚠️ (非升即走"淘汰率90%以上"个案普遍化、高校"取消事业编制"绝对化、硕博"只能拿三五百"忽略国家助学金、鲁迅引语转述措辞出入), 新反模式两条入 factcheck-guide §6; ④ 用户追加两轮数据扩展 (学生缩减幅度队列外推 + 教师岗位变化), 队列法自校准: 幼儿园 2025 预测 3220 vs 实际 3225.52 万 (误差 0.2%); ⑤ 元观察: 本会话 skill 工具加载的 SKILL.md 滞后于磁盘工作区 (缺 v0.1.18 与 GPU 入口, 疑似进程启动时缓存) — 疑似缺内容时以 Read 磁盘为准。
