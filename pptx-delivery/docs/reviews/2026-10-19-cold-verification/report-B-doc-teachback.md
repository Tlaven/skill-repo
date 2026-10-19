# Agent B 独立验证报告 — pptx-delivery 文档体系(实现级复核)

> 立场:独立验证者(teach-back 复核)。未参与设计讨论,看不到那些对话。
> 输入 = 本任务书 + `C:\Users\TL\skills-repo\pptx-delivery\` 内的文件。
> 约束遵守情况:只读该目录(未读仓库其他位置、未联网);**未执行任何脚本/命令**(核对全用"读");未修改任何文件;未派子代理。
> 结果文件:本文件(scratchpad/verify/agentB/REPORT.md)。

---

## 1. 复述(我的话,保留原文词)

待验证单元是 `pptx-delivery` 技能的文档体系,主审 **SKILL.md 及其直接引用的操作文档**(`editing.md` / `pptxgenjs.md` / `lessons.md` / `typography.md` / `acceptance-checklist.md` / `docs/scaffolds/visual-quality-essentials.md`);`UPGRADE-*` 是历史底稿,可读但不计入达标判断(我读过,只在"自述与正文互洽"里当旁证用)。

判定范围是**实现级**:达标线 = 一个新 agent 只凭这些文档,**能正确完成「从零制作一份中文 PPTX 并按验收清单交付」**,行为不跑偏、无需外部猜测。上轮阻断清单:**无(首跑)**。

判据是四条命中即 [阻断]:①两处规则矛盾;②失败/边界分支未定义(含对外表现);③同一文档可引出**行为不同**的多种实现;④写不出可跑的验收。**升格 [阻断] 要过两道关:①逐字引用原文;②行为分叉测试(两个工程师会不会做出行为不同的东西)。** 误伤与漏报同样严重,"按惯例/框架可定"的事不许打成 [阻断],**宁可标 [非阻断]**。

必做核对(与缺口清单分开记):①独立核对 ≥2 个可核对断言(C1–C9 vs `scripts/qa_check.py` 实现;命令参数 vs 脚本真实接口);②独立复算 ≥1 个精确例子(acceptance-checklist §0 的六十秒流程);③检查「已知盲区 / 危险实现清单」类自述与正文是否互洽。

交付:本报告 + 最后一条消息含 复述 / 缺口清单表 / 核对记录 / 判定。

---

## 2. 判定

**通过**(未达 [阻断] 线;9 条 [非阻断] 缺口,均为"可读、可绕、或纯表述精度"问题)。

依据:
- 判据①(规则矛盾):发现的最高级别冲突是"基准表 vs 本地实测值"的分层差异(字号体系、绝对坐标),两处都能从文档自身读出**适用域划分**(typography.md 自称"本地增量…base 的 Latin 排版建议见 SKILL.md";坐标来自带 `【实测】` 标签的样张),且两个分支都不破坏"从零做中文 PPTX 并按清单交付"这一目标——按"**宁可标 [非阻断]**"处理。
- 判据②(分支未定义):主路径(生成 → 归一化 → 渲染 → C1–C9 → 目检 → 修正)的所有失败分支在文档里有对外表现:无 LibreOffice → COM;两个渲染器都没有 → XML 层检查照跑;C7/C8 无 PDF → 脚本报 `skipped (no --pdf given)`。唯一未写清的是 `render/` 目录前置条件(R7),对外表现是一个带路径的报错,可当场修。
- 判据③(一文档多实现):未发现"同一规则可推出两个都合规但行为不同的成品"的情况(具体排除清单见 §7)。
- 判据④(可跑的验收):§0 三步 + §2 阈值表**能原样跑通**(逐步复算见 §5),渲染产物命名与 `--pdf` 取值一致(`render/deck.pdf`)。

---

## 3. 缺口清单(全部 [非阻断])

| # | 级别 | 我卡在哪 | 我当时想问你什么 | 证据(逐字/位置) |
|---|---|---|---|---|
| R1 | 非阻断 | C9 阈值写作"可调",但脚本没有任何可调入口;要按项目收紧时不知道改哪 | "这条'可调'指改源码常量,还是漏了 CLI 旗标?" | acceptance-checklist.md:45 `\| C9 可编辑性 \| 不得"整页图片 + 零文本"(覆盖率阈值 80%,可调) \|`;qa_check.py:497 `覆盖率阈值 80%【假设待测】(可调)。`;qa_check.py:519 `if has_pic and area_ratio >= 0.8 and not any(...)`(硬编码);qa_check.py:553-555 只有 `--min-font-pt` / `--aspect-tol` / `--expect-slides` |
| R2 | 非阻断 | 负控组数三处不一致,复跑时无法判断"跑没跑全" | "以哪个数为准,6 组还是 7 组?" | acceptance-checklist.md:77 `6 组负控 + 干净基线(误报闸门)`;tests/README.md:3 `5 组蓄意缺陷 deck(负控)+ 1 组真实中文 deck(端到端)`;run_tests.py:36 `CONTROL_DECKS = ["clean","c1_placeholder",…,"c7_badcolor"]`(clean + c1–c7);tests/evidence/run.log:268-275 实跑 8 行结果 |
| R3 | 非阻断 | C7 的"来源"栏打了【实测】,但项目自己的记录说没有夹具能触发它;§5「已知盲区」没收录这条 | "C7 的【实测】是指'检查器存在'还是'验过命中'?" | acceptance-checklist.md:43 `\| C7 页面越界 \| 渲染 PDF 中不得有词框越过页面边界 \| 【实测:tests/ (C7 检查器)】 \|`;UPGRADE-REPORT.md:91 `防御性检查;当前两个渲染器都在导出端裁切越界文本,暂无能触发 C7 的夹具`;tests/out/reports/c3_overflow.json:59-65 C7 仅 info,C8 才是 flag(与 acceptance-checklist.md:44 的 C8【实测】一致) |
| R4 | 非阻断 | C3 对"继承字号"(无显式 sz)的 run 不检查,§5 盲区清单未声明;用 master/placeholder 拼的页可能"字号全绿" | "继承字号的文字,交付前谁管?" | qa_check.py:250-253 `size = run.font.size` / `if size is None:` / `inherited += 1` / `continue`;qa_check.py:266 `below-min={hits}, inherited-size(not checked)={inherited}`;acceptance-checklist.md:67-73 §5 未提此条(同节却提了 C5 的"主题色继承") |
| R5 | 非阻断 | 中文 deck 的标题/正文字号存在两套数(SKILL.md 基准 vs typography.md 实测值),没有一句优先级 | "中文页标题按 36–44 还是按 28?" | SKILL.md:128 `\| Slide title \| 36-44pt bold \|`、:130 `\| Body text \| 14-16pt \|`、:145 `titles need 36pt+ to stand out from 14-16pt body`;typography.md:23 `base 建议区间:标题 36–44pt / 正文 14–16pt / 说明 10–12pt`、:47 `字号梯度(实拍样张):封面标题 40 / 页标题 28 / 卡片题 16 / 正文 14 / 说明 12–13`;visual-quality-essentials.md:30 `放映型…(标题 28 / 正文 18–24 / 行距 ≥1.5)` |
| R6 | 非阻断 | typography.md 给出的**绝对坐标**属 13.333×7.5 版面,主文档却把 10×5.625 写作 default;照抄坐标会落到画布外 | "这些坐标适用于哪个版面尺寸?" | typography.md:46 `样张落 y=6.25;封面 / 封底脚注另一档(y≈6.6)。【实测:tests/out/render/e2e_deck/】`;tests/lib.js:31 `pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in -> 960 x 540 pt`;pptxgenjs.md:22 `- \`LAYOUT_16x9\`: 10" × 5.625" (default)` |
| R7 | 非阻断 | §0 没写 `render/` 目录需先存在(COM 分支自建,LibreOffice 分支与 `--json` 写入不一定),也没提 COM 的 PNG 固定 1920×1080 | "走 LibreOffice 分支时我要先 `mkdir render` 吗?" | acceptance-checklist.md:12-19 §0 三步无 mkdir;render_slides.ps1:23 `if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory … }`;render_slides.ps1:15-16 `[int]$Width = 1920` / `[int]$Height = 1080`、:35-36 `("slide-{0:d2}.png" -f $i)` + `Export($target, "PNG", $Width, $Height)`;qa_check.py:609 `Path(args.json_path).write_text(` |
| R8 | 非阻断 | `docs/scaffolds/visual-quality-essentials.md` 自称"目检判读前先加载",但主文档没有一个链接指向它 | "这份脚手架算必读吗?挂 SKILL.md 哪一节?" | visual-quality-essentials.md:4 `做 PPTX 交付的视觉 QA / 风格收敛 / 目检判读前,先加载本文件对证`;SKILL.md:11-20 Quick Reference 无此条;全目录检索只有 UPGRADE-REPORT.md:39 提到它 |
| R9 | 非阻断 | 模板路径第一步(缩略图分析)依赖 LibreOffice+Poppler,而"Windows without LibreOffice"的兜底只覆盖 QA 链,没覆盖模板分析 | "没有 LibreOffice 时,模板结构分析走哪条路?" | SKILL.md:39 `python scripts/thumbnail.py presentation.pptx`、:271 `Windows 上无需 LibreOffice 也能完整跑 QA:用 scripts/render_slides.ps1…`(只讲 QA);editing.md:8-9 把 thumbnail.py 列为模板工作流第 1 步;thumbnail.py:203-217 调 soffice,失败即 `raise RuntimeError(f"PDF conversion failed: …")` → exit 1 |

### 为什么这 9 条都不到 [阻断](逐条过两道关)

- **R1**:①可逐字引用 ✓;②行为分叉:只有"想收紧 C9 阈值"的工程师会分叉(一个去改源码、一个放弃),**默认路径两种做法产出同一个 deck**;且该"可调"在 −UPGRADE-REPORT.md:99 里本就登记为【假设待测】→ 表述精度问题,不是"行为不同"。
- **R2**:①✓;②数量是**描述性**的,不影响任何执行动作(`python tests/run_tests.py --which controls` 跑什么由代码决定)。
- **R3**:①✓;②来源标签错误不改变 agent 动作(仍会跑 C7);影响的是"零 flag"的证明力,不影响成品。
- **R4**:①✓;②主路径(pptxgenjs 教程里每个 `addText` 都带 `fontSize`)**不会**触发该盲区;只有走 master/placeholder 的人可能误信"字号全绿",且属漏检而非误判。
- **R5**:①✓;②分叉存在(28 vs 36–44),但 typography.md:3 已把自己定位为"本地增量",且把 SKILL.md 那一节称作"base 的 Latin 排版建议"——**适用域划分已写在文档里**,按"框架/惯例可定"降级。建议补一句优先级,不阻断。
- **R6**:①✓;②坐标是"样张实测值"不是规则;照抄到小版面会被 C7/C8 抓住(越界→丢字→flag),不是静默错误。
- **R7**:①✓;②失败对外表现明确(带路径的报错 / `pdftotext failed` flag 或 `FileNotFoundError`),当场可修;两个分支的 PDF 命名都落在 `render/deck.pdf`,与 §0 的 `--pdf` 取值一致。
- **R8**:①✓;②scaffold 是"观感级"增补,checklist §3 目检清单在它缺席时**自足**;缺的是发现路径,不是判据。
- **R9**:①✓;②失败是响亮的(`PDF conversion failed`),可绕(markitdown / 直接打开模板);且 Dependencies 表已把 LibreOffice 列为工具。

---

## 4. 必做核对 ①:可核对断言(读实现,不跑脚本)

### 4.1 C1–C9 ↔ `scripts/qa_check.py` 一一对应

| 文档条目(acceptance-checklist.md §2) | 实现位置 | 结论 |
|---|---|---|
| C1 结构:页数/媒体/图片清点;`--expect-slides` 可断言页数 | qa_check.py:204-215(`report.info`+ 页数不符时 `"flag"`),`--expect-slides` 见 :555 | ✅ 一致(severity=flag 与 §0:18 `--strict = 有任何 error/flag 即非零退出` 相容) |
| C2 占位残留:模式表 lorem/xxxx/click to edit/单击此处/待填/请输入/TBD… | qa_check.py:48-51 正则 `lorem\|ipsum\|x{4,}\|click to edit\|单击此处\|点击此处\|待填\|待补充\|请输入\|TBD\|TODO`(IGNORECASE) | ✅ 文档列的是子集,带"…",无假模式 |
| C3 字号下限 ≥10pt(默认,`--min-font-pt` 可调) | qa_check.py:242-267;:553 `default=10.0` | ✅ 参数存在且默认值一致 |
| C4 srgbClr 必须 6 位 hex、无 `#`;无负向 shadow dist | qa_check.py:270-288(`val` 非 6 位 hex 或含 `#` → error;`<a:outerShdw…dist="-` → error) | ✅ 逐项对上 |
| C5 普通 ≥4.5:1;大文本(≥18pt 或 ≥14pt 粗)≥3:1;不四舍五入 | qa_check.py:54-57(`CONTRAST_NORMAL=4.5`,`CONTRAST_LARGE=3.0`,`LARGE_TEXT_PT=18.0`,`LARGE_TEXT_BOLD_PT=14.0`)、:325-328(`ratio + 1e-9 < need`,不取整) | ✅ 一致 |
| C6 显示比例 vs 原始像素比例,偏差 ≤2% | qa_check.py:345-378;:554 `--aspect-tol default=0.02` | ✅ 阈值一致 |
| C7 渲染 PDF 中不得有词框越过页面边界 | qa_check.py:381-425(`pdftotext -bbox`,越界词 → flag) | ✅ 实现存在(但见 R3:无触发夹具) |
| C8 每个段落必须完整出现在渲染 PDF 文本层 | qa_check.py:428-488(逐段落 `_norm_text` 子串匹配,缺尾 → flag) | ✅ 一致,且与 :44【实测:c3 尾行被裁】的实跑记录吻合(c3_overflow.json:66-69 flag) |
| C9 不得"整页图片 + 零文本" | qa_check.py:491-529(`area_ratio >= 0.8` 且无文本 → flag) | ⚠️ 阈值 80% ✓,但"可调"✗(R1;:519 硬编码) |
| (typography.md:40 提到的)I1 字体清单 | qa_check.py:532-544(info 级,`:79 check_font_inventory`) | ✅ 存在且为信息项 |

### 4.2 命令参数 ↔ 脚本真实接口

| 文档写法 | 真实接口 | 结论 |
|---|---|---|
| `qa_check.py output.pptx --pdf … --strict --json …`(SKILL.md:17/176;acceptance-checklist.md:19) | qa_check.py:549-556: positional `pptx`,`--json`,`--strict`,`--pdf`,`--min-font-pt`,`--aspect-tol`,`--expect-slides`;退出码 :614 `if args.strict and (err + flag) > 0: return 1`,:561 缺文件 return 2 | ✅ 全部存在;`--strict` 语义与 §0:18 注释一致 |
| `--expect-slides` / `--min-font-pt`(acceptance-checklist.md:37/39) | :553-555 | ✅ |
| `render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf`(SKILL.md:20;checklist:15) | render_slides.ps1:12-18 `param([string]$Pptx,[string]$OutDir,[int]$Width=1920,[int]$Height=1080,[switch]$Pdf)`;:40 输出 `<OutDir>/<baseName>.pdf` | ✅ 与 §0 第 3 步的 `--pdf render/deck.pdf` 取值一致 |
| `soffice.py --headless --convert-to pdf --outdir render deck.pptx`(checklist:16) | soffice.py:227-230 原样透传 `sys.argv[1:]`(Windows 走 PATH/Program Files/scoop 探测,:35-59) | ✅ 参数可用;`render/` 是否自建未定义(R7) |
| `normalize_pptx_order.py inplace deck.pptx`(SKILL.md:168;checklist:12) | normalize_pptx_order.py:64-70 `len(args)==2 and args[0]=="inplace"` → 原地重写;幂等(返回值 "no notesMasterIdLst"/"already in schema order") | ✅ 与文档一致 |
| `validate.py deck.pptx`(checklist:28) | validate.py:71-92 支持打包文件(解包到临时目录→`PPTXSchemaValidator`);`from validators import …` 依赖脚本目录入 sys.path(=scripts/office),故从仓库根可跑;schemas 齐(pml.xsd 等 39 个 .xsd 在 `scripts/office/schemas/`) | ✅ 可跑 |
| `thumbnail.py input.pptx [output_prefix] [--cols N]`(editing.md:92) | thumbnail.py:46-58;`DEFAULT_COLS=3`,`MAX_COLS=6`;:244 `max_per_grid = cols * (cols + 1)` → 默认 3 列 = 每格 12 张 | ✅ "默认 3 列、max 12 per grid" 对上 |
| `python scripts/qa_check.py…` 无渲染器时的覆盖(SKILL.md:271:"C1–C6、C9") | main() :566-579:无 `--pdf` 时 C7/C8 打 info `skipped (no --pdf given)`,其余 C1–C6 + C9 + I1 照跑 | ✅ 逐条对上 |
| `tests/run_tests.py --which controls` / `--no-build --no-render`(checklist:80;tests/README.md:14-15) | run_tests.py:126-128 三个参数都在 | ✅ |
| `pack.py unpacked/ output.pptx --original template.pptx`(editing.md:42) | pack.py:135-147;`--original`,`--validate true|false` | ✅ |

**附带发现(不进缺口表)**:tests/README.md:8-15 的命令块 cwd 混用——`pip install -r ../requirements.txt` 暗示 `cd tests/`,`python tests/run_tests.py` 暗示仓库根,**照抄整块必挂一条**;acceptance-checklist.md:80 自己给的那一行从仓库根可跑。

---

## 5. 必做核对 ②:§0「六十秒快速通道」逐步复算

原文(acceptance-checklist.md:12-19):

```bash
# 0) pptxgenjs 产出的文件先归一化(生成器已知问题,见 §5;其他工具产出可跳过):
python scripts/normalize_pptx_order.py inplace deck.pptx

# 1) 渲染(WPS/PowerPoint COM,或 LibreOffice 二选一):
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf
python scripts/office/soffice.py --headless --convert-to pdf --outdir render deck.pptx

# 2) 断言(C1–C9;--strict = 有任何 error/flag 即非零退出,可挂 CI):
python scripts/qa_check.py deck.pptx --pdf render/deck.pdf --strict --json render/qa.json
```

逐步推演(全部按读到的代码判,cwd = 仓库根):

1. **步 0**:`inplace` 分支命中(normalize_pptx_order.py:66);只动 `ppt/presentation.xml`(:25-27,41);原件被原地重写(tmp + `shutil.move`,:56-60)。**注意**:`inplace` 分支不检查源文件是否存在(:66-70 直接 `zipfile.ZipFile(src)`),给错文件名会抛 `FileNotFoundError` 追溯栈,而不是脚本 docstring 承诺的 "Exit codes: … 2 input problem"(:16)。— 推演出的小毛刺,不影响正常路径。
2. **步 1-A(COM 分支)**:参数名/开关与 `param()` 完全对上;`render/` 不存在会被 :23 建出来;导出 `slide-01.png…` 与 `render/deck.pdf`(`$baseName` 取自 pptx 文件名,:25,40)。→ 步 2 的 `--pdf render/deck.pdf` **路径成立**。
3. **步 1-B(LibreOffice 分支)**:soffice.py 原样转发参数;LibreOffice 输出名 = `deck.pdf` → 与步 2 的 `--pdf` **路径也成立**。**歧义点**:文档没说要先 `mkdir render`;该分支不保证目录存在(我只读不跑,无法确认 LibreOffice 是否自建 outdir)→ 见 R7。另外这一步与 1-A 是"二选一",两条都给 PDF,不冲突。
4. **步 2**:`deck.pptx --pdf render/deck.pdf --strict --json render/qa.json` 四项参数全部真实存在;`--strict` 的语义 = `errors + flags > 0` 即退出 1(:614),与括号注释一字不差;C7/C8 因给了 `--pdf` 会真跑(:573-575);报告写入需要 `render/` 已存在(:609),步 1-A 已创建 → **从零到结论可原样跑通**。
5. 结论:**流程可跑,类目齐全**(C1–C9 + I1;目检部分由 §3 接手,§0:22 明确"无自动结论的部分…走 §3 目检")。唯一歧义点 = `render/` 前置条件 + LibreOffice 分支的 outdir 行为(R7)。

### 附带独立复算(WCAG 数值,验证"精确例子"里的量化断言)

按 `qa_check.py:102-114` 的同一公式(`lin` 分段函数 + `(hi+0.05)/(lo+0.05)`)手算:

- typography.md:48 `珊瑚色 E4574F 白字对比 3.64:1` → 我算 **3.64:1**(L(coral)=0.2388;1.05/0.2888=3.636)✅ 与文档一致,且 ≥ C5 大文本阈值 3.0(18pt/14pt 粗)——文档对它的用法限制一致。
- typography.md:45 `说明与注脚 5F6B7C…在 FFFFFF 与 F7F8FA 底上均 ≥ 4.5:1` → 我算 **5.41:1 / 5.09:1** ✅;顺带注意 tests/lib.js:17 的另一个灰 `64748B` 在 `F7F8FA` 上只有 **4.48:1**(会恰好踩线被 C5 判 flag)——这解释了 e2e 样张为何单独定义 `G = "5F6B7C"`(make_e2e_deck.js:10),文档给的"默认设定"是**踩过点的那一个**。
- typography.md:45 的 `1E2761` 粗体标题 → 白底 **13.8:1**、`F7F8FA` 底 **13.0:1** ✅;`222222` 正文 → `F7F8FA` 底 **15.0:1** ✅。
- 与证据文件互证:`tests/out/reports/e2e_deck.json:42` `checked=80, below-threshold=0, unresolved(needs visual)=0`;`tests/evidence/run.log:276` `[PASS] e2e_deck: flags=0, errors=0` → 文档声称的 `【实测:tests/out/reports/clean.json, e2e_deck.json】` 落地文件在,内容支持该断言。

---

## 6. 必做核对 ③:「已知盲区 / 危险实现清单」自述 vs 正文

**(a) acceptance-checklist §5「已知盲区(诚实声明)」— 大部分互洽,两处漏项**

- ✅ `pptxgenjs 4.0.1 把 <p:notesMasterIdLst> 写在 <p:sldIdLst> 之后…normalize_pptx_order.py` 与 pptxgenjs.md:460-464、normalize_pptx_order.py:4-8、`tests/evidence/normalize_check.log:4-6`(raw `FAILED`)/:12(`All validations PASSED!`)三处一致。
- ✅ `对比度:渐变 / 图片背景、主题色继承、透明叠加 —— 仅目检` 与实现一致:C5 对继承色 `continue`(qa_check.py:307-309)、非纯色填充记 `non-solid-fill` 进 `unresolved`(:296-321、:339-342)。
- ✅ `CJK 的"等价大字号"…本工具按 18pt/14pt 罗马值执行,对中文属偏宽(可能少判,不会多判)` 与 :56-57 实现一致,且与 typography.md:22 的"等价尺寸应更大(未给数值)"**方向自洽**:若中文的等价大文本分界比 18pt 更大,则工具把 18–T 之间的中文 run 也算"大文本",只要求 3:1 → 只会**少判**,不会**多判**。逻辑闭环 ✅。
- ✅ `行距 / 字距美观、孤字控制:无自动判据` / `音视频、动画、图表内部:不在本清单` 与 C1–C9 + I1 的实际覆盖面一致(对照 §4.1 表)。
- ❌ 漏项一:C7 现状("暂无能触发 C7 的夹具")未收录(见 R3,旁证 UPGRADE-REPORT.md:91)。
- ❌ 漏项二:C3 对继承字号不检查未收录(见 R4,旁证 qa_check.py:266)。

**(b) visual-quality-essentials.md §四「失败模式(危险实现清单)」— 全部互洽**

逐条地把"挡它的"列指回本文件条目,7/7 都能解析:#1→通例1/事实1、#2→通例2/事实7、#3→通例3/事实5、#4→通例4/事实6、#5→通例5、#6→通例7/事实8、#7→通例8。§三.2(`指不回就不改`)、§三.3(`机器先行:先跑 C1–C9`,与 acceptance-checklist §2 的 C1–C9 同一套编号)、§七 版本记录(v0/v0.1 触发条件与正文一致)均无自相矛盾。§六 的 `【待补证据】GB/T 15834…(标准号待核 + 链接待补)` 是**如实标注的缺口**,不是缺陷。

**(c) 其它自述抽查**

- SKILL.md:271 的自述"C1–C6、C9;渲染无关"经实现核对成立(§4.2 末行)。
- acceptance-checklist.md:44 的 C8 `【实测:c3 尾行被裁 → 命中】` 与 c3_overflow.json:66-69(flag)+ run.log:271 一致 ✅。
- typography.md:46 的坐标自述与样张源码逐点吻合(封底 6.6 → make_e2e_deck.js:29/190;内容页 6.25 → :55/87/151),**但缺版面尺寸上下文**(R6)。
- SKILL.md:296 声称本地增量"claims are tagged 【实测】/【引用】/【假设待测】where they are made"——SKILL.md 自身的具体数值(0.5in 边距、0.3–0.5in、36–44pt 等)**未打标签**;这条属"自述略宽于实际",但说明书类文档的常规做法,不计缺口(仅记录)。
- 负控数量的三处不一致见 R2(此处不重复)。

---

## 7. 我判定为「不构成缺口」的疑点(显式记录,避免误伤)

1. **SKILL.md 字号表 vs typography.md 实测值**:见 R5 的降级理由(本地增量已声明适用域)。同理 **"正文 14–16"(SKILL.md)vs "放映型正文 18–24"(visual-quality-essentials.md:30/事实8)** 也不计缺口:后者写明"先判场景",而本技能的项目默认场景由 typography.md:23/47 的实测值给定。
2. **`NEVER use accent lines under titles`(SKILL.md:152)vs `thick single-side borders`(SKILL.md:73)vs pptxgenjs.md:449-458 的竖向 accent bar**:三处是两个不同图形(标题下横线 vs 单侧竖条),不冲突。
3. **`color: "#FF0000"` 禁忌(pptxgenjs.md:418)与夹具里 SVG 必须带 `#`(lib.js:79)**:两个域,UPGRADE-REPORT.md:28 已把它点成"知识陷阱的注脚",不是矛盾。
4. **`lineSpacing` 用法**:pptxgenjs.md:434("Avoid `lineSpacing` with bullets…use `paraSpaceAfter`")与 lessons.md:38("`lineSpacingMultiple` 不是有效属性,用 `lineSpacing`")语境不同,不冲突。
5. **`pm`/`m` 级文档分工**:scaffold(观感级)↔ checklist(C1–C9 硬阈值)↔ typography(中文微排版)三层在各自开篇句里互相引用,层级清晰(scaffold 的缺席只是发现路径问题,R8)。
6. **COM 渲染 PNG 固定 1920×1080**(render_slides.ps1:15-16)对非 16:9 版面会把图拉变形:主路径(教程默认 16:9)不受影响,且属"渲染器参数"而非常规判据——并入 R7 记录,不单列。
7. **判定为"按惯例可定"、不打 [阻断] 的**:`node deck.js` 的执行方式(pptxgenjs.md 只给代码块,lessons.md:112 `写 JS 脚本一次性生成` 补齐)、`--json` 的 JSON 结构、`--strict` 在 CI 里的接法——惯例层面唯一解或可自证。

---

## 8. 我无法核对 / 超出只读范围的事项(如实列出)

- **pptxgenjs 库事实**:`lineSpacingMultiple` 是否真的"不是有效属性"(lessons.md:38)、`sizing.contain` 是否真的"仍会拉伸"(pptxgenjs.md:170/230)、`charSpacing` vs `letterSpacing`(:38-39)——库不在此目录,未联网核对;未发现与正文冲突,不计缺口,列为未核项。
- **不执行命令**的约束:所以 LibreOffice 的 `--outdir` 是否自建目录、WPS COM 的实际可用性,都是读码推断,已在 R7 标注不确定性。
- **UPGRADE-PLAN/REPORT 的行数与文件数**(如 UPGRADE-REPORT.md:34 `qa_check.py(547 行)` vs 实际 620 行;:38 `typography.md(20 行)` vs 实际 48 行)与现状漂移——按派发参数**历史底稿、不计入达标判断**。
- 未做:任何写操作、任何脚本执行、任何仓库外读取(scratchpad 报告除外)。

---

## 9. 若还要再迭代,建议优先补 3 处(不影响本次判定)

1. **R1**:要么给 qa_check.py 加 `--min-image-coverage`(名字与 `--min-font-pt` 对齐),要么把 acceptance-checklist.md:45 的"可调"删掉、并把该行来源改成 `【假设待测(阈值)】`——与 UPGRADE-REPORT.md:99 的登记对齐。
2. **R3+R4**:§5「已知盲区」补两条:"C7 当前无触发夹具(两渲染器均把越界文本裁出文本层)"、"C3 不检查继承字号(记 `inherited-size(not checked)`)";顺手把 C7 那行的来源从 `【实测:tests/ (C7 检查器)】` 改成"检查器已实现,未获触发夹具"。
3. **R5+R6+R8**:三句话即可——(i) typography.md 顶部加"字号/坐标以本文件为准,SKILL.md Typography 表为 Latin 基准";(ii) 坐标段补"(13.333×7.5 版面)";(iii) SKILL.md 的 QA/Visual QA 节加一行链接指向 `docs/scaffolds/visual-quality-essentials.md`。
