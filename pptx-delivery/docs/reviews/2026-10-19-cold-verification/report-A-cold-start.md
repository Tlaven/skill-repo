# 冷启动可用性测试报告 · 受试者 agentA

- 测试时间:2026-10-19 约 11:15–11:30(本机时钟;命令回显可证)
- 技能目录:`C:\Users\TL\skills-repo\pptx-delivery\`(**全程只读**;详见 §7 边界检查)
- 工作目录(唯一写入区):`C:\Users\TL\AppData\Local\Temp\commandcode\C--Users-TL-skills-repo-essentials\23d8f706-fe95-40d3-bb8a-f8c8cfc83279\scratchpad\verify\agentA\`(下文简写 `agentA\`)
- 任务:从零创建 4 页中文 deck《周报:数据管道上线复盘》+ 按技能文档跑完整 QA(≥ `qa_check.py --strict`;渲染→带 PDF 复跑)
- 上下文:冷启动,未参与任何前期讨论;本报告为收到的全部上下文之外的全部留痕

## 0. 状态:**DONE**

全流程一次降级(1 条命令被工具白名单拒绝 → 等价做法),两次 fix→verify 循环,最终 `qa_check --strict`(带 PDF)0 error / 0 flag,`validate.py` 全通过,渲染目检无残留问题。

## 1. 最终产物(全部在 agentA\ 内)

| 类别 | 路径 | 说明 |
|---|---|---|
| 交付 deck | `out\weekly-report.pptx` | 4 页;已过 normalize;qa 0 error/0 flag;L0 schema PASSED |
| 渲染 PNG | `render\slide-01..04.png` | WPS COM 导出,1920×1080 |
| 渲染 PDF | `render\weekly-report.pdf` | WPS COM `SaveAs(32)` |
| 整版拼图 | `render\contact-sheet.png` | 2×2 接触印相(自建脚本),用于整版目检 |
| QA JSON | `out\qa-report-xml.json` | 第 1 轮(XML 层,0/0) |
| QA JSON | `out\qa-report-pdf.json` | 第 1 轮(带 PDF,0/0) |
| QA JSON | `out\qa-report-round2-flagged.json` | 第 2 轮(**1 flag**,修复前的证据留存) |
| QA JSON | `out\qa-report-final.json` | 最终轮(带 PDF,0/0) |
| 证据快照 | `render\history\slide-02-round2-flagged.png` | 第 2 轮被 flag 状态的渲染 |
| 生成脚本 | `gen_deck.js` | pptxgenjs,含全部修复后的最终版 |
| 辅助脚本 | `contact_sheet.js` | sharp 拼 2×2 目检图 |

## 2. 命令清单(原样记录,按执行顺序)

> 说明:`$A` = 上文 agentA 绝对路径;标注 **[OK] / [被拒] / [降级]**。

**① 环境预检 [OK]**
```powershell
$ErrorActionPreference='Continue'; '--- node/npm ---'; node -v; '--- npm root -g ---'; npm root -g; '--- global pkgs ---'; npm ls -g --depth=0 2>$null | Select-String -Pattern "pptxgenjs|sharp|react"; '--- python ---'; python --version; python -c "import pptx, defusedxml; print('python-pptx+defusedxml OK')"; python -c "import PIL; print('Pillow OK')"; '--- pdftotext ---'; (Get-Command pdftotext -ErrorAction SilentlyContinue).Source; '--- COM check ---'; try { $t=[Type]::GetTypeFromProgID('PowerPoint.Application'); if($t){'PowerPoint.Application COM: registered'} else {'PowerPoint.Application COM: NOT registered'} } catch { 'COM check error: ' + $_.Exception.Message }
```
结果:node v22.23.2;`npm root -g` = `C:\nvm4w\nodejs\node_modules`;全局有 **pptxgenjs@4.0.1 + sharp@0.35.5**(react-icons/react/react-dom 未装);Python 3.12.4 + python-pptx/defusedxml/Pillow 齐全;`pdftotext` = `C:\poppler\poppler-24.08.0\Library\bin\pdftotext.exe`;PowerPoint.Application COM 已注册(WPS 提供)。

**② 首次运行命令(带 cwd=agentA)** → **[被拒(工具白名单)]**
调用原样:`powershell`(command: `$env:NODE_PATH = (npm root -g); node gen_deck.js; ...`,cwd= `…\scratchpad\verify\agentA`)
拒绝原文:`…agentA is outside workspace (allowed: C:\Users\TL\skills-repo\essentials, C:\Users\TL\skills-repo, C:\Users\TL\AppData\Local\Temp\commandcode\shellout)`
**[降级]** 按降级协议记录后改用等价做法:去掉 `cwd`,全部用绝对路径运行(脚本内 `__dirname` 决定产物目录,产物仍落 agentA)。后续同。

**③ 生成 deck [OK,降级写法]**
```powershell
$env:NODE_PATH = (npm root -g); node "C:\Users\TL\AppData\Local\Temp\commandcode\C--Users-TL-skills-repo-essentials\23d8f706-fe95-40d3-bb8a-f8c8cfc83279\scratchpad\verify\agentA\gen_deck.js"; "node_exit=$LASTEXITCODE"
```
→ `wrote …\out\weekly-report.pptx` / `slides: 4` / node_exit=0

**④ 归一化 + XML 层 qa_check --strict(第 1 轮) [OK]**
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; $A="…agentA"; "=== normalize ==="; python "C:\Users\TL\skills-repo\pptx-delivery\scripts\normalize_pptx_order.py" inplace "$A\out\weekly-report.pptx"; "normalize_exit=$LASTEXITCODE"; "=== qa_check (xml level) ==="; python "C:\Users\TL\skills-repo\pptx-delivery\scripts\qa_check.py" "$A\out\weekly-report.pptx" --strict --expect-slides 4 --json "$A\out\qa-report-xml.json"; "qa_exit=$LASTEXITCODE"
```
→ normalize:`moved notesMasterIdLst before sldIdLst`,exit 0;qa:`errors=0, flags=0`,exit 0(C5 checked=60)

**⑤ 渲染(WPS COM,PNG+PDF) [OK,降级写法(绝对路径 / 直接调用)]**
```powershell
& "C:\Users\TL\skills-repo\pptx-delivery\scripts\render_slides.ps1" -Pptx "$A\out\weekly-report.pptx" -OutDir "$A\render" -Pdf
```
→ `[render] slides: 4` + 4×png + 1×pdf,`[render] done`。(说明:SKILL.md 示例是 `powershell -File …`;我在 PowerShell 会话内用 `& 调用` 等价执行,避免嵌套进程。)

**⑥ 带 PDF 复跑 qa_check --strict(第 1 轮) [OK]**
```powershell
python "C:\Users\TL\skills-repo\pptx-delivery\scripts\qa_check.py" "$A\out\weekly-report.pptx" --pdf "$A\render\weekly-report.pdf" --strict --expect-slides 4 --json "$A\out\qa-report-pdf.json"; "qa_pdf_exit=$LASTEXITCODE"
```
→ `errors=0, flags=0`,exit 0;C7 `no words outside slide bounds across 4 page(s)`;C8 `all paragraphs present (4 PDF pages)`

**⑦ 目检(读图)** → 多文件读取不内联图片,改单文件逐个读;发现 slide-02 两处问题(见 §5)

**⑧ 修复 1+2(edit_file)** → 改 `gen_deck.js`:卡片文案消孤字;卡片 h 3.5→2.95 + 状态标签 + 底部结论条

**⑨ 全链路复跑(第 2 轮):regenerate→normalize→render→qa --pdf [OK,但 qa exit=1]**
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; $env:NODE_PATH = (npm root -g); $A="…agentA"; node "$A\gen_deck.js"; python "…normalize_pptx_order.py" inplace "$A\out\weekly-report.pptx"; & "…render_slides.ps1" -Pptx "$A\out\weekly-report.pptx" -OutDir "$A\render" -Pdf 6>$null; python "…qa_check.py" "$A\out\weekly-report.pptx" --pdf "$A\render\weekly-report.pdf" --strict --expect-slides 4 --json "$A\out\qa-report-final.json"; "qa_exit=$LASTEXITCODE"
```
→ `errors=0, flags=1`(**C5 FLAG**,修复引入的回归,见 §5),qa_exit=1

**⑩ 证据快照 [OK]**
```powershell
New-Item -ItemType Directory -Force "$A\render\history" | Out-Null; Copy-Item "$A\render\slide-02.png" "$A\render\history\slide-02-round2-flagged.png" -Force; Copy-Item "$A\out\qa-report-final.json" "$A\out\qa-report-round2-flagged.json" -Force
```

**⑪ 修复 3(edit_file)** → 结论条文本框补同色 `fill`(见 §5)

**⑫ 全链路复跑(第 3 轮)+ 附加检查 [OK]**
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; $env:NODE_PATH = (npm root -g); $A="…agentA"; node "$A\gen_deck.js"; python "…normalize_pptx_order.py" inplace "$A\out\weekly-report.pptx"; & "…render_slides.ps1" -Pptx "$A\out\weekly-report.pptx" -OutDir "$A\render" -Pdf 6>$null; python "…qa_check.py" "$A\out\weekly-report.pptx" --pdf "$A\render\weekly-report.pdf" --strict --expect-slides 4 --json "$A\out\qa-report-final.json"; "qa_exit=$LASTEXITCODE"; python "C:\Users\TL\skills-repo\pptx-delivery\scripts\office\validate.py" "$A\out\weekly-report.pptx"; python -m markitdown "$A\out\weekly-report.pptx"; python -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); print([n for n in z.namelist() if 'media' in n])" "$A\out\weekly-report.pptx"; node "$A\contact_sheet.js"
```
→ qa:`errors=0, flags=0`,exit 0;validate:`All validations PASSED!`;markitdown:4 页文字齐全、顺序正确;zip media:`['ppt/media/']`(空目录项,无真实媒体);contact sheet 生成

**⑬ 目检复验(contact-sheet.png + slide-02.png)** → 干净,无新问题

**⑭ 边界检查 [OK]** → `skills-repo` 下最新 `.pyc` 时间戳为当天 08:48–08:49(早于本次会话约 2.5h),会话内全程 `PYTHONDONTWRITEBYTECODE=1`;**skills-repo 未被写入**

## 3. 为确定下一步翻过的文档(全部只读)

| 文件 | 翻它的原因 |
|---|---|
| `SKILL.md`(全文) | 入口:确定流程(create-from-scratch → QA 命令序列)、依赖、Windows 渲染降级路径 |
| `pptxgenjs.md`(全文) | 从零创建指南:API、坑位清单(颜色/阴影/bullet/对象复用/顺序问题) |
| `acceptance-checklist.md`(全文) | L0–L3 分层、C1–C9 阈值表、§0 六十秒通道、§5 已知盲区 |
| `typography.md`(全文) | CJK 字体/字号/行距/标点规则 + 「本项目默认设定」(字号梯度、页脚锚线 y 值) |
| `lessons.md`(全文) | 操作经验(图片比例、NODE_PATH、scripts 运行路径、QA 工具链) |
| `scripts/qa_check.py`(全文源码) | 确认 C1–C9 判定逻辑(尤其 C5 的背景解析和 C8 的文本对账方式)与参数 |
| `scripts/render_slides.ps1`(全文) | 确认 COM 调用方式、-Pdf 行为、输出命名 |
| `scripts/normalize_pptx_order.py`(头部+usage) | 确认 inplace 用法与作用 |
| `scripts/office/validate.py`(头部 usage) | 判断 L0 校验可否直接跑(需 `from validators import`,以绝对路径运行成功) |
| `tests/make_e2e_deck.js` + `tests/lib.js`(全文) | 仓库自带实测样张:沿用其 LAYOUT_WIDE、页脚锚线、字号梯度等被验证过的版式常量 |
| (未读) `editing.md`、`UPGRADE-*.md`、`tests/README.md`、`expected.json` 等 | 与「从零创建」路径无关,未打开 |

## 4. QA 结果摘要

| 轮次 | 检查 | 结果 |
|---|---|---|
| R1 | `normalize_pptx_order.py inplace` | moved notesMasterIdLst before sldIdLst(pptxgenjs 4.0.1 已知问题,文档预警准确) |
| R1 | `qa_check --strict`(XML 层) | **0 error / 0 flag**;C5 checked=60 below=0;exit 0 |
| R1 | 渲染 WPS COM → PNG×4 + PDF | 成功 |
| R1 | `qa_check --strict --pdf` | **0/0**;C7/C8 均过(4 页);exit 0 |
| R1 | 目检 4 张 PNG | **发现 2 处问题**(slide-02:孤字尾行、卡片下半空带)→ 修复 1+2 |
| R2 | 全链路复跑 + `qa_check --strict --pdf` | **1 flag**:C5 slide2「结论条」白字被判 1.06:1(bg 解析为页面底色 F7F8FA)→ exit 1 → 修复 3 |
| R3 | 全链路复跑 + `qa_check --strict --pdf` | **0 error / 0 flag**;C5 checked=64 below=0;C7/C8 4 页全过;exit 0 ✅ |
| R3 | `validate.py`(L0) | `All validations PASSED!` ✅ |
| R3 | `markitdown`(内容 QA) | 4 页文本齐全、顺序正确、无占位残留 ✅ |
| R3 | 目检(contact sheet + slide-02 单张) | 干净,无新问题 ✅ |

最终机器指标:C1 slides=4 / pictures=0;I1 字体清单 = Microsoft YaHei ×64;C2 无占位;C3 最小字号=12pt(≥10);C4 颜色卫生 OK;C5 64 run 全达标;C6 无形变;C7/C8 通过;C9 可编辑(全文本)。

## 5. 修复内容(fix→verify 两轮)

**修复 1(目检发现,slide-02)**:卡片 1 文案折行出现孤字尾行("…回滚窗" / "口。" 单独一行)。
- 改:`周二凌晨完成订单链路 100% 切流,旧管道降级为只读备份,保留 7 天回滚窗口。` → `周二凌晨完成链路 100% 切流,旧管道转只读备份,保留 7 天回滚窗口。`(缩短 2 字,折行为 2 行且尾行饱满)

**修复 2(目检发现,slide-02)**:卡片仅占上半,卡片内下半 + 卡片与页脚之间有大段空带(疏密失衡)。
- 改:卡片高度 3.5→2.95;卡片底部新增状态标签(已切流 / 观测通过 / 回归通过,浅底 E3EEF3 + 深蓝字);新增整宽结论条(`065A82` 底 + 白字 15pt:结论:核心链路连续 7 天零 P1 事故;遗留 2 项低风险待办,已排入下周计划。)

**修复 3(机器发现,slide-02,C5 回归)**:
- R2 报:`FLAG: slide 2: ratio 1.06 < 3.0 (large text) in 'Text 20': '结论:…' color=#FFFFFF bg=#F7F8FA`
- 根因:`qa_check.py` C5 对文字背景的解析顺序是 ①所在表格单元格填充 ②**文字框自身的填充** ③页面(或母版)底色 —— 不建模 z 序叠加。白字放在深色结论条上,但文字框是透明文本框,判定时落到了页面底色。
- 改:给结论条文本框补上与色条同色的 `fill: { color: "065A82" }`(视觉零差异);R3 判定 bg=065A82,白字 7.53:1 通过。

## 6. 摩擦清单(逐条:文档出处 + 当时的疑问)

1. **[环境/工具] `powershell` 工具不允许把 cwd 设为 scratchpad**:任务书说 scratchpad 是唯一可写区,但工具允许的 cwd 白名单只有 `skills-repo`、`skills-repo\essentials`、`shellout`。出处:任务书 / 环境(非技能文档)。疑问:技能文档的示例命令全部是相对路径(`-OutDir render/`、`python scripts/…`),在"cwd 受限,只能用绝对路径"的环境里照抄会失败——SKILL.md 是否值得给出"任意 cwd + 绝对路径"的等效命令块?→ 我的处理:全部绝对路径,已顺利跑通。
2. **[验收清单] 透明文本框叠在色块上的对比度是"会误报"而不是"仅目检"**:acceptance-checklist §5 写「透明叠加 —— 仅目检」,但实测 C5 并不跳过,而是按页面底色评估并 FLAG(白字/浅底 1.06:1)。出处:`acceptance-checklist.md` §5 + `scripts/qa_check.py` C5 实现。疑问:「深底色条 + 白字」的正确写法(文本框自带同色填充 / 文字内嵌形状)在任何文档里都没写,第一次做必然踩一次;建议补进 checklist 或 pptxgenjs.md 的坑位清单。
3. **[渲染脚本] render_slides.ps1 无显式成功信号**:脚本 `Write-Host` 输出在 agent 捕获里序列化成大段 CLIXML 噪音;`$LASTEXITCODE` 为空(脚本未设退出码),判断成败只能自己核对产物文件。出处:`scripts/render_slides.ps1`。疑问:是否需要 `exit 0/1` + 精简 stdout,便于 CI/agent 直读?
4. **[qa_check] C1 的 media 计数包含空目录项**:`media=1` 实为 zip 中 `ppt/media/` 空目录条目(无任何媒体文件),对无图片 deck 容易误读为"含 1 个媒体"。出处:`qa_check.py` `check_structure`(`x.startswith("ppt/media/")` 未排除目录项)。疑问:是否应计数 `ppt/media/` 下的实际文件?
5. **[流程] 子代理视觉 QA 无法执行**:SKILL.md「Visual QA」要求 USE SUBAGENTS("id: fresh eyes"),但本环境明确禁止派子代理 → 无法照做,降级为自查 + 2×2 接触印相 + 单张放大复查。出处:SKILL.md QA 节。疑问:无子代理环境下的替代协议(单人复检、隔天复检)未见说明。
6. **[依赖] 图标工作流依赖未装且不得重装**:pptxgenjs.md 的 Icons 一节需要 `react-icons`/`react`/`react-dom`(本机未装),而任务约束"依赖已装好,勿重装" → 放弃图标方案,改用形状(编号圆/方块)替代。出处:`pptxgenjs.md` Icons 节 + 环境。疑问:SKILL.md 的依赖表最好标注哪些是"核心必装"、哪些是"可选工作流",并给无图标依赖时的替代样式建议。
7. **[小口径不一致] scripts 运行目录**:lessons.md §6 说"在 `scripts/` 目录下执行";实测 `qa_check.py` / `normalize_pptx_order.py` 从任意 cwd 用绝对路径均可运行(无相对 import)。出处:`lessons.md` §6。疑问:表述可更新为"推荐 scripts/ 下运行,或任意 cwd 绝对路径"。
8. **[脚本行为] normalize 幂等性的实测补充(非问题)**:两次 pptxgenjs 4.0.1 产出都命中了 notesMasterIdLst 次序问题,`normalize` 每次输出 `moved …`;文档【实测】标签准确。

正面观察(供参考,不算摩擦):SKILL.md → acceptance-checklist → 脚本三者的命令闭环完全可执行;typography.md 的「本项目默认设定」(字体/字号梯度/页脚锚线 y=6.25 与 6.6)直接可用,首轮机器检查即 0 flag,主要归功于此;qa_check 的报错信息(定位到形状名、行内文本、前后景颜色、比值)非常利于定位。

## 7. 边界与诚实声明(未能验证 / 未做的部分)

- **皮肤替换风险未实测**:全篇仅用 Microsoft YaHei;在无该字体的环境(macOS/Linux)会回退,断行可能变化。文案均留了折行余量,但"字体替换后的实际渲染"未在其他环境验证(typography.md 已把该风险列为交付注意项)。
- **L3 人工签字项未做真实人手抽查**:可编辑性由 C9(非整页图)与 markitdown 文本层间接证明;元数据已设(pres.author/title);无讲者备注、无批注、无本地链接、无隐藏页(生成脚本可控)。"随机改一个字"的现场操作未执行。
- **子代理目检未做**(环境禁止),以自查替代,已在 §6-5 记录。
- **虚构内容声明**:deck 中的人名(李航)、日期(2026-07-10)、W26/W28 指标数字为演示用自拟数据,不代表真实业务。
- 未修改 skills-repo 内任何文件;所有临时产物都在 agentA\ 内(§2-⑭)。

## 8. 任务书要求对照

| 要求 | 状态 |
|---|---|
| 4 页中文 deck(标题/要点/表格或数据/收尾) | ✅ `out\weekly-report.pptx` |
| ≥ `qa_check.py --strict` | ✅ 共跑 4 次(XML×1、带 PDF×3),最终 0/0;R2 的 1 flag 已修复 |
| 渲染 → 带 PDF 复跑 | ✅ WPS COM 渲染 PNG+PDF,`--pdf` 复跑含 C7/C8 |
| 报错→修正→复跑 | ✅ 两轮 fix→verify(R1→R2→R3),修复 3 处 |
| 全程留痕 | ✅ 本报告 + `out\qa-report-*.json` ×4 + `render\history\` 证据快照 |
| 权限边界 | ✅ 读 skills-repo(未改);写仅 agentA;1 条命令被拒→已降级 |
