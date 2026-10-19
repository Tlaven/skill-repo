# UPGRADE-REPORT — pptx skill 产品化升级对账单

> **任务**:把 pptx skill 从「个人工作流」提升到「可分享 / 可交付」级别(全程自主推进)。
> **日期**:2026-10-19 · **底稿**:[UPGRADE-PLAN.md](UPGRADE-PLAN.md)(先于改动落盘)
> **阅读顺序**:§1 缺口→处置 → §4/§5 硬条件结果 → §6 证据台账 → §7 未竟事项。
> **来源标签**:`【实测:路径】` / `【引用:URL】` / `【假设待测】`。

## 1. 缺口清单 → 处置(开工 11 项,全部处理)

| # | 缺口 | 处置 | 落点 |
|---|---|---|---|
| G1 | 重复(contain/fitInside ×2;Windows PowerShell 兜底 ×2) | 正典归位 `pptxgenjs.md`「图片分辨率与 DPI」;`lessons.md` 只留原则与指针;PS 兜底整体收进脚本 | SKILL.md / lessons.md / pptxgenjs.md |
| G2 | 矛盾(转换边界 vs 从零创建;pptxgenjs 内 contain 前后不一) | 「When to NOT Use」改写为「纯格式转换」;sizing 节加实测警告行 | SKILL.md L24–28;pptxgenjs.md L168–174 |
| G3 | 触发面全英文 | description 增 `PPT / 幻灯片 / 演示文稿 / 答辩` | SKILL.md frontmatter |
| G4 | 不可执行 QA | `qa_check.py`(C1–C9)+ `render_slides.ps1` + `normalize_pptx_order.py`;QA 节命令级接线 | scripts/ + SKILL.md L160–179 |
| G5 | 阈值缺来源 | 阈值表逐条带来源 | acceptance-checklist.md §2 |
| G6 | 中文排版无专项 | `typography.md`(字体 / 字号 / 行距 / 混排,全带来源) | typography.md |
| G7 | 无对外验收产物 | `acceptance-checklist.md`(分层 + 目检清单 + 签字项 + 盲区 + 外部工具) | acceptance-checklist.md |
| G8 | 环境与代码缺陷 | `soffice.py` / `thumbnail.py`:删「LibOffice」死拼写、补 scoop 路径与 `SOFFICE_PATH`;LibreOffice 26.8.1 实装并实测 | scripts/ |
| G9 | lessons 混杂 | §1/§2 去重为指针;§5.2 换脚本;§5.1 更新 | lessons.md |
| G10 | 无验证场景 | `tests/`:8 负控 + 干净基线 + 端到端 + 契约 + 一键复跑 + 证据留档 | tests/ |
| G11 | 依赖清单不全 | Dependencies 重写(python-pptx / sharp / react 组合 / WPS·LO·poppler / SOFFICE_PATH) | SKILL.md |

**过程中实测新发现(开工时未见)**:

- **F1 · pptxgenjs 4.0.1 的 schema 次序问题**:`<p:notesMasterIdLst>` 被写在 `<p:sldIdLst>` 之后,严格校验(validate.py)失败(PowerPoint/WPS 能打开)。→ 新增 `normalize_pptx_order.py`;修复前后对比见 `tests/evidence/normalize_check.log`。
- **F2 · 越界文本在导出端就被裁掉**:WPS 与 LibreOffice 的 PPTX→PDF 都会把越过画布边缘的行**从文本层移除**,纯"越界词框"检查(C7)抓不到。→ 新增 **C8 渲染保真**(段落必须在渲染 PDF 文本层中完整出现),双渲染器下均验证命中。
- **F3 · 夹具自身 bug**:柱状图 SVG 里颜色漏 `#` 前缀 → 渲染成纯黑,被独立目检抓住并修复(SVG 要 `#`,pptxgenjs 反而不要——两个域,正好是知识陷阱的注脚)。

## 2. 做了什么(交付物清单)

**新增**:

- `scripts/qa_check.py`(547 行)—— C1 结构 / C2 占位 / C3 字号 / C4 颜色卫生 / C5 对比度(WCAG)/ C6 形变 / C7 越界 / C8 渲染保真 / C9 可编辑 + I1 字体清单;`--json` / `--strict`。
- `scripts/render_slides.ps1`(46 行)—— Windows COM(WPS / PowerPoint)渲染 PNG + PDF,实测。
- `scripts/normalize_pptx_order.py`(90 行)—— 修 F1,幂等。
- `tests/` —— `lib.js` / `make_controls.js`(7 缺陷)/ `make_badcolor.py` / `make_e2e_deck.js` / `run_tests.py` / `expected.json` / `README.md`;`evidence/`(run.log、逐 deck JSON、normalize_check.log)。
- `acceptance-checklist.md`(89 行)、`typography.md`(20 行)、`UPGRADE-PLAN.md`、本文件。
- `docs/scaffolds/visual-quality-essentials.md`(视觉质量脚手架 v0.1;2026-10-19 加入并于 §7 首用)——观感级判断层,补 C1–C9 与目检之间的判据。

**修改**:`SKILL.md`、`pptxgenjs.md`、`lessons.md`、`requirements.txt`(+python-pptx)、`scripts/office/soffice.py`、`scripts/thumbnail.py`(见 §1)。

**未动**:`editing.md`、`LICENSE.txt`、base 的 `schemas/` 与 `validators/`(只被消费)。

**不膨胀**:SKILL.md 298 行(目标 ≤350);新增均为「可执行断言 / 复跑夹具 / 带来源的决策文档」,无装饰性内容。

## 3. 证据在哪(复跑指南)

```powershell
# 前提:Python deps(pip install -r requirements.txt);Node 全局 pptxgenjs+sharp($env:NODE_PATH=(npm root -g));
# 渲染器(WPS/PowerPoint,或 LibreOffice);poppler(pdftotext)
python tests/run_tests.py          # 8 负控 + 端到端,一键复跑
```

- `tests/evidence/run.log` —— 全量记录(命令 + 输出)。
- `tests/evidence/reports/*.json` —— 逐 deck 机器可读报告。
- `tests/evidence/normalize_check.log` —— L0 修复前后对比(raw FAILED → normalized PASSED,含幂等案例)。
- 逐层命令(归一化 / 渲染 / 断言 / 校验)见 `acceptance-checklist.md` §0 与 SKILL.md QA 节。

## 4. 端到端结果(硬条件 2 · 生成 → QA → 修正 → 复验)

任务:`tests/make_e2e_deck.js` 生成 7 页中文 deck《AI 生成 PPTX 的交付验收》。

1. **轮 1**:生成 → L1 检查 0 error / 0 flag;独立目检(子代理、像素级量测)→ **1 严重 + 22 轻微**。
2. **修正 1**(高价值项 13 处):S2 说明折行、单位与装饰尺寸统一、两行文本块顶部对齐;S3 卡片比例与断行;C9 内容同步(统计 9 项 / 列表 / 阈值表);S6 图表资产颜色 bug + 图注居中 + 行距、S7 标题层级与间距。
3. **轮 2 复验**:L1 仍 0/0;独立复检 → **严重 0 / 轻微 0**(既定 a–d 项全部核验通过)。
4. **轮 3(L0)**:validate.py 抓出 F1 次序问题 → normalize 修复 → **All validations PASSED**;修后 L1 仍 0/0、渲染正常。
5. **内容 QA**:markitdown 抽取正常;占位/待办模式零命中(文中「占位残留」为主题词,非残留)。
6. **双渲染器交叉**:WPS 26.8.1 COM 与 LibreOffice 26.8.1 —— PDF 均 7 页 960×540pt;C8 在两个渲染器的产出上均命中(c3 控制组)。
7. **视觉收敛(2026-10-19)**:以视觉质量脚手架为尺收敛 §7 风格余项(S2 / S3 增底部锚线、S5 注脚同基线)——重建 → 渲染 → 断言 0/0,复看通过。

记录:`tests/evidence/run.log`(本报告为结论摘要,原始输出以日志为准)。

## 5. 负控结果(硬条件 3)

| deck | 蓄意缺陷 | 命中检查 | 说明 |
|---|---|---|---|
| `c1_placeholder` | 占位符残留 | C2 ×3 | XXXX / Click to edit / 单击此处 |
| `c2_lowcontrast` | 低对比度(1.36 / 1.16:1) | C5 ×2 | 两种底色场景 |
| `c3_overflow` | 文本溢出画布,尾行被裁 | **C8** | WPS/LO 双渲染器均命中 |
| `c4_stretched` | 图片拉伸(形变 50%) | C6 | |
| `c5_tinyfont` | 字号 7pt | C3 | |
| `c6_flatslide` | 整页图片、零文本 | C9 | 100% 覆盖 + 零文本 |
| `c7_badcolor` | 非法 hex(`#` 前缀注入) | C4(error)+ C5(连带) | C5 连带源于损坏色的解析回退,预期内 |
| `clean` | —(误报闸门) | 无 | **0 error / 0 flag** |

**误报 / 漏报记录**:

- **真实漏报(已修)**:c3 首版未被抓住 —— WPS 把越界行裁出 PDF 文本层,C7 看不到任何越界词;新增 C8 后命中,并在 LO 下复核同样命中。这是"必须真实跑"的核心价值。
- **真实误报(已修)**:clean 首版 C5 误报表格表头(未解析 cell 填充,回退到 slide 背景)→ 修正背景解析顺序(cell → shape → slide)→ 此后 clean 全绿。
- **C7 现状(如实记录)**:防御性检查;当前两个渲染器都在导出端裁切越界文本,暂无能触发 C7 的夹具。若换渲染器(如 MS PowerPoint 本体)建议复跑 c3 观察。

## 6. 证据分级台账(硬条件 1)

**统计**(本次新增 / 修改的规则与阈值):【实测】11 条 /【引用】10 条 /【假设待测】3 条 ≈ **12.5%**,低于 30% 红线。

**假设待测清单(3 条,如何证伪)**:

1. C9 覆盖率阈值 80%(可调参数)——用更多"半页图 + 少量文字"的真实 deck 校准;
2. 演示版式行长 ≤30 字(设计惯例)——A/B 版式可读性测试;
3. 中英混排用雅黑/思源即可覆盖的假设——收集 Latin 回退实例。

**主要来源(节选,完整表见 acceptance-checklist §2 与 typography.md)**:

| 断言 | 档位 | 证据 |
|---|---|---|
| 对比度 4.5:1 / 3:1、大文本 18/14pt、不四舍五入 | 【引用】 | W3C WCAG 2.1/2.2 SC 1.4.3 |
| 字号下限 10pt(C3 默认) | 【引用】本项目规范(可调);微软演示建议 18pt+ | SKILL.md Typography;support.microsoft.com |
| 形变容差 ≤2% | 【实测】 | clean 0.0% vs c4 50%(tests/evidence/reports) |
| 占位模式表 | 【实测】 | c1 命中 / clean 零命中 |
| C8 渲染保真 | 【实测】 | c3(双渲染器);normalize_check.log |
| C9 可编辑性 | 【实测】检测 + 【假设待测】阈值 | c6 命中 |
| pptxgenjs 次序问题 | 【实测】 | normalize_check.log |
| 中文行距 / 混排间距 | 【引用】clreq(W3C) | typography.md |

## 7. 仍未完成 / 已知限制(及原因)

- **目检余项(风格级)——已收敛(2026-10-19,首用 [docs/scaffolds/visual-quality-essentials.md](docs/scaffolds/visual-quality-essentials.md) 当尺)**:① 底部留白节奏 → **修复**:S2 / S3 补底部锚线、S5 注脚对齐,内容页收口统一到 y=6.25 一带;② 三种灰阶的角色化使用 → **保留并写实**:文字角色表补进 [typography.md](typography.md)(标题 / 名称 `1E2761` 粗体、正文 `222222`、说明 / 注脚 `5F6B7C`);③ 标点全 / 半角混用 → **保留**(作者文风,自此为明示决策);④ 5:4 列表不对称 → **保留**(刻意不对称合法,对齐基准未动);⑤ S6 要点 / S4 名称颜色角色 → **保留并写实**(名称 = 标题色、要点 = 正文色,属两个角色)。复验:重建 → 渲染 → C1–C9 0 error / 0 flag,渲染图复看通过。
- **C7 无触发夹具**(见 §5 现状)。
- **测试场景集中在 Windows + 中文**;Linux/macOS 渲染链逻辑保留(soffice.py)但未实测。
- **未安装 MS PowerPoint 本体**,用 WPS 兼容接口代偿(PowerPoint 渲染差异属已知风险,文档已注明"以目标环境打开为准")。
- **环境依赖已装但属机器级动作**(LibreOffice via scoop、poppler、Node 全局包);换机需按 Dependencies 重装。
- **复核提示**:c7 的 C5 连带命中、c3 的 C8 命中依赖渲染器行为——换渲染器请复跑负控。
