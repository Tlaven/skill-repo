# 中文(CJK)排版规范(演示文稿)

> 本文件是 pptx-delivery skill 的本地增量(base 的 Latin 排版建议见 SKILL.md「Typography」节)。
> 每条规则带来源标签:`【引用:URL】` / `【实测:位置】` / `【假设待测】`。
> 场景:Windows 制作 → 任意环境打开 / 放映的跨平台交付。

## 字体:跨平台可用性

| 字体 | 提供方 | 字重 | 跨平台结论 |
|---|---|---|---|
| 微软雅黑 Microsoft YaHei | Windows 7–11 内置;官方页未列 macOS | Light / Regular / Bold(3 档) | 只可依赖同机发布;mac 打开会被替换 |
| 苹方 PingFang SC | macOS 内置;Windows 字体资料未收录 | 6 档 | 同上,方向相反 |
| 思源黑体 Source Han Sans(= Noto Sans CJK) | 开源,**SIL OFL 1.1,允许分发/嵌入** | 7 档,5 个语言变体 | **唯一可直接依赖的跨平台选择** |

- 来源:雅黑 https://learn.microsoft.com/en-us/typography/font-list/microsoft-yahei ;苹方 https://support.apple.com/en-us/120414 ;思源 https://github.com/adobe-fonts/source-han-sans/blob/release/README.md
- 实操:本机(Windows)制作可放心用"Microsoft YaHei";但**交付到混合环境时,排版要留换行余量**(字体替换会改变断行,PPTLint 记录过"字体替换后标题换行、最后一行被截掉"的事故)。
- 伪粗体:软件合成的粗体/斜体在复杂汉字上会加重笔画粘连;用字族**自带**的 Bold/Medium,不要给 Light 字重叠"加粗"。【引用:https://fonts.google.com/knowledge/glossary/faux_fake_pseudo_synthesized】

## 字号

- 微软官方无障碍建议:演示文本 **"18pt or larger"**、无衬线、留足空白;避免全大写与过多斜体。【引用:https://support.microsoft.com/en-us/accessibility/powerpoint/make-your-powerpoint-presentations-accessible-to-people-with-disabilities】
- WCAG 的 18pt / 14pt(bold)是**对比度阈值切换的大文本分界**,不是最小字号;并明确 CJK 的等价尺寸应更大(未给数值)。【引用:https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html】
- 本项目现状:`qa_check.py` C3 硬下限 **10pt(默认,可调)**;base 建议区间:标题 36–44pt / 正文 14–16pt / 说明 10–12pt。
- 行业惯例(无权威文档):正文 18–24pt、线上演示 24pt+。【引用(一般博客):https://www.presentations.ai/zh/blog/what-font-size-is-best-for-presentations】
- 场景优先:本页梯度以**阅读型**交付为准;现场放映型按 Harvard(正文 18–24pt)。SKILL.md 的"标题 36–44pt"属放映型建议,阅读型页标题取 28pt(实测样张);同一文档内不混用两套。

## 行距与行长

- clreq(W3C 中文排版需求):单面装行距 **≥ 字号的一半**,双面装 ≥ 5/8;**全篇行距保持一致**。【引用:https://www.w3.org/TR/clreq/】
  - 落到 PPT:同一文档的正文段落使用同一 LnSpc 设定;避免 `lineSpacing` 与 bullet 混用(pptxgenjs 已知坑,见 pptxgenjs.md)。
- 行长:正文每行 10–48 字(横排,clreq);演示版式取更短更稳(每行 ≤ 30 字)【假设待测(设计惯例)】。

## 中英混排与标点

- 汉字与西文/数字之间留 **≤ 1/4 汉字宽**的字距/空白;行首行尾处不加。【引用 clreq】
- 标点:中文句内用全角;数字、单位、代码用半角;同一文档保持同一选择。
- 混排字体应同时覆盖 CJK + Latin(雅黑/思源黑体均可),避免 Latin 字体回退导致基线不齐。【假设待测】

## 检查手段

- 自动:`qa_check.py` C3(字号)/ C5(对比度)/ I1(字体清单)/ C8(渲染保真兜底丢字)。
- 人工:渲染后目检换行、标点与字重观感——机器判不了的部分见 [acceptance-checklist.md](acceptance-checklist.md) §3。

## 本项目的默认设定(实测通过,可作起点)

- 字族:`Microsoft YaHei`(本机场景);**文字角色**:标题 / 名称 `1E2761` 粗体(页标题 / 卡片题 / 条目名),正文 `222222`,说明与注脚 `5F6B7C`,深底页文字 白 / `CADCFC`——上述浅底色在 `FFFFFF` 与 `F7F8FA` 底上均 ≥ 4.5:1【实测:tests/out/reports/clean.json, e2e_deck.json】。
- 版式注脚:内容页的底部锚线(注脚 / 引用行)全篇同款同高,样张落 y=6.25;封面 / 封底脚注另一档(y≈6.6);坐标以 13.33×7.5in 宽版式计。【实测:tests/out/render/e2e_deck/】
- 字号梯度(实拍样张):封面标题 40 / 页标题 28 / 卡片题 16 / 正文 14 / 说明 12–13。
- 珊瑚色 `E4574F` 白字对比 3.64:1——只用于 **≥18pt 或 ≥14pt 粗**的大文本【实测:qa_check C5】。
