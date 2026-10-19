# UPGRADE-PLAN — pptx-delivery 产品化升级:完成定义 + 缺口清单(工作底稿)

> **任务**:把 pptx-delivery skill 从「个人工作流」提升到「可分享 / 可交付」级别;全程自主推进。
> **开工**:2026-10-19 · **执行**:Command Code agent · **验收**:独立冷眼 agent(含负控抽查)。
> **本文件性质**:自主判断底稿——先于任何改动落盘;执行中增补(新增处标注日期)。
> **状态标记**:[待办] / [进行中] / [完成] / [放弃(附原因)]

## 一、完成定义(DoD)

- **D1 证据先行**:本次新增/修改的每条规则、阈值、命令必须带来源标签,三档制:
  `【实测:证据位置】` / `【引用:URL 或出处】` / `【假设待测】`。
  全文统计「假设待测」占比 ≤ 30%(目标 ≤ 10%),台账见 UPGRADE-REPORT.md。
- **D2 端到端**:走通一次真实任务(中文 deck)的「生成 → QA(自动检查 + 渲染 + 视觉)→ 修正 → 复验」全流程;
  命令与输出留档(pptx-delivery/tests/evidence/),任何人可按记录复跑。
- **D3 负控**:构造 ≥3 个蓄意缺陷 deck(计划 5 类:占位符残留 / 低对比度 / 文本溢出 / 图片拉伸 / 字号过小);
  QA 流程必须全部抓出;误报(干净 deck 跑全检查的 flag 数)与漏报逐项记录。
- **D4 静态缺陷收口**:已发现的矛盾(2 处)、重复(2 处)、拼写错误(2 文件)、触发面缺口(无中文触发词)、
  文档内贴 PowerShell 代码 → 全部处理。
- **D5 产品化层**:① 量化阈值表(带来源)② 中文排版专项(带来源)③ 交付验收清单(陌生团队可直接照用)
  ④ QA 工具链接入 SKILL.md(命令级、可执行)。
- **D6 仓库纪律**:提交风格沿用例(`feat(pptx): 中文摘要` + 要点 + Co-authored trailer);不膨胀
  (新增文件逐个说明必要性,SKILL.md 目标 ≤ 350 行);Anthropic 许可标记保留,base 层与本地层可区分。
- **D7 可复现**:pptx-delivery/tests/ 提供一键复跑说明;冷眼 reviewer 可独立执行负控抽查。

## 二、缺口清单(现状与证据)

- **G1 重复 → 漂移风险**
  - `contain` 不可靠 + `fitInside` 实现:lessons.md §1.1、§2 与 pptxgenjs.md「图片分辨率」节,2 份实现代码。
  - Windows 兜底 PowerShell:SKILL.md「Windows Fallback」与 lessons.md §5.2,两份高度重叠。
- **G2 内部矛盾**
  - SKILL.md「When to NOT Use」(排除 Markdown→PPTX 无模板)vs「Creating from Scratch」(无模板用 pptxgenjs)。
  - pptxgenjs.md 同文件内:前文称 `contain` 保比例,后文称 `contain` 不可靠。
- **G3 触发面**:description 仅英文触发词;中文实际话术(PPT / 幻灯片 / 答辩 / 演示文稿)未覆盖。
- **G4 缺可执行 QA**:QA 全靠文档 + 手贴 PowerShell;无工具化断言。markitdown 在本机未安装(pptx/Pillow/defusedxml/lxml 已有)。
- **G5 量化阈值缺来源**:边距 / 间距 / 字号 / 对比度等阈值分散,且无来源标记。
- **G6 中文排版无专项**:仅零散提到微软雅黑;无字号 / 行距 / 跨平台字体策略的成文规则与来源。
- **G7 无对外验收产物**:没有「陌生团队可照用」的验收清单。
- **G8 环境与代码缺陷**:`soffice.py` 与 `thumbnail.py` 各含 2 行 `"LibOffice"` 拼写错误(死条目);
  本机无 LibreOffice(无管理员权限;scoop 安装已启动);渲染通道缺失 → 已实测 **WPS COM 可用**(PNG + PDF)。
- **G9 lessons.md 信息混杂**:§7 是 skill 维护元规则(非 PPT 操作);§5.1–5.2 与 SKILL.md 重复。
- **G10 无验证场景 / 回归夹具**:无 tests、无负控、无期望结果存档。
- **G11 依赖清单不全**:pptxgenjs.md 图标工作流需 react-icons / react / react-dom / sharp,Dependencies 节未列全。

## 三、执行计划(阶段与状态)

- **P0 环境落地** [完成 10-19]:WPS COM ✓(PNG+PDF 实测)、LibreOffice 26.8.1(scoop)✓、poppler ✓、
  pptxgenjs@4.0.1 + sharp@0.35.5 ✓、markitdown ✓、中文字体 ✓。
- **P1 底稿落盘** [完成(本文件)]。
- **P2 QA 工具链** [完成]:`scripts/qa_check.py`(C1–C9)+ `scripts/render_slides.ps1`(COM,实测);含
  `soffice.py` / `thumbnail.py` 的 Windows 路径修复(scoop + `SOFFICE_PATH`)。
- **P3 负控夹具** [完成]:6 组负控 + 干净基线,全部按 expected.json 命中;误报闸门 0。
- **P4 端到端真实任务** [完成]:7 页中文 deck,两轮「生成 → QA → 修正 → 复验」;两轮独立目检(子代理,像素级量测)。
- **P5 内容升级** [完成]:SKILL.md(中文触发词 / QA 接线 / 边界裁决 / 依赖与许可注记)、pptxgenjs.md、
  lessons.md(去重归位)、acceptance-checklist.md、typography.md。
- **P6 报告** [完成]:`UPGRADE-REPORT.md`(对账单:缺口 → 动作 → 证据 → e2e/负控结果 → 未竟事项与原因)。
- **P7 提交** [进行中]:按仓库风格提交;只 stage `pptx-delivery/`;pre-commit hook 通过。

## 四、证据纪律

- 三档标签沿用整个交付物;台账(逐条:断言 → 档位 → 证据位置)在 UPGRADE-REPORT.md。
- 原则:新规则优先落成「可执行断言」(脚本检查)或「可复跑记录」,少写文字声称。
- 「假设待测」红线:占比 > 30% = 未完成(DoD D1)。

## 五、风险与降级

- **R1** scoop 安装 LibreOffice 失败/超时 → 降级:WPS COM 为主渲染链;soffice 链标注「未在本机验证」,不作为新结论。
- **R2** markitdown 安装失败 → 文本抽取由 qa_check.py 自实现;markitdown 降级为可选依赖(文档同步)。
- **R3** pptxgenjs v4 与文档(v3 时代 API)差异 → 实测记录,文档标注版本。
- **R4** WPS 渲染与 PowerPoint 存在差异 → 文档注明「渲染检查为近似;最终以目标环境打开为准」。
- **R5** 预算约束 → 优先级 D1–D3 > D4/D5 > 其余;产物保持精简(「变胖不算进步」)。

## 六、状态日志

- `2026-10-19 00:0x` 环境盘点完成(详见 P0);WPS COM 渲染实测通;pptxgenjs v4 冒烟通。
- `2026-10-19 00:1x` 底稿落盘;`render_slides.ps1` 初版已写,复测中。
- `2026-10-19 01:1x` 负控 6/6 命中 + 干净基线零误报;e2e 两轮修正(S2 断行 / 图表 SVG 颜色 bug / C9 同步 /
  目检高价值项);LibreOffice 链与 thumbnail 实测通过;目检报告:1 严重 + 22 轻微(高价值已修,余项记录于报告)。
