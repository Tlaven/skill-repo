# 检查指引 — 亲手验收这份示例(15 页 · 12 种版式)

> 这是一份**参考示例交付包**(非测试夹具):`deck.pptx` + 渲染图 + QA 证据 + 本指引。
> 目的:让你亲手确认「生成 → 断言 → 渲染复验 → 验收清单」这条链是真的;版式判据见 `../../docs/scaffolds/slide-patterns-essentials.md`。

## 0. 这 15 页各自用的版式(按版式库脚手架的原型)

| 页 | 版式 | 看什么 |
|---|---|---|
| 1 | 封面(深底 + 点阵纹理 + 环形装饰) | 氛围层不承载信息、对比度合规 |
| 2 | 执行摘要(三栏:现状 → 做法 → 结果) | 每栏三句封顶、结论句标题 |
| 3 | 大数字(`0 flag` 140pt) | 一个焦点,不塞佐证 |
| 4 | 三支柱(几何图标 + 元信息) | 图标是形状组件、不是贴图;元信息成组 |
| 5 | 流程(chevron 箭形 + 产物标签) | 四步、顺序固定 |
| 6 | 时间线(阶段标签 / 主线 / 说明三层) | 终点高亮("当前") |
| 7 | 2×2 矩阵(频率 × 伤害) | 象限贴片、轴标签 |
| 8 | 仪表盘(5 KPI 贴片 + 迷你条 + 双面板) | 红色贴片只放"要盯的那一个" |
| 9 | 双栏对比(旧 vs 新) | 行对齐、方形标记 |
| 10 | 记分卡(表格 + ●/○ 计分) | 粗颗粒记分,不做假精度 |
| 11 | 引用 + 证据(深底) | 金句 + 数字必须配对 |
| 12 | 图 + 解读(圈选最高柱) | so-what 必须给结论 |
| 13 | 命令终端块(窗口 + 等宽) | 顺序 = 依赖关系 |
| 14 | 色卡(6 色 + 角色 + 对比度) | 一套颜色三个角色 |
| 15 | 收尾(深底 + 行动项) | 不写"谢谢" |

## 1. 打开来看(观感与可编辑性)

用 WPS / PowerPoint 打开 `deck.pptx`,逐页对照:

- [ ] 每页都能直接改文字、移动形状(不是整页图片)——对应 C9 可编辑性;
- [ ] 标题与正文左缘在同一条线上(0.8\"),内容页底部注脚同一高度(≈6.25\");封面 / 收尾页页脚在 6.6\" 档;
- [ ] 颜色只有规定角色(见第 14 页):标题 `1E2761` / 正文 `222222` / 说明 `5F6B7C`(深底页白 / `CADCFC`);
- [ ] 装饰件(点阵、环、箭形、迷你条)都是形状或图片,**不是文字**;
- [ ] 图片的"替代文字"是描述而不是本地路径(右键图片 → 查看替代文字)。

## 2. 看渲染图与 PDF(导出保真)

- [ ] 打开 `render/slide-01..15.png`(或 `render/deck.pdf`),与直接开 PPTX 的观感一致;
- [ ] 第 10 页记分卡的 ●/○ 字形导出后仍完整(对应 C8);
- [ ] 第 12 页柱图 2:1 无变形(对应 C6);第 1 / 12 页两张图片都在(对应 C1)。

## 3. 亲手跑机器断言(一条命令,预期全绿)

在 pptx-delivery 目录下:

```powershell
python scripts/qa_check.py examples/acceptance-sample/deck.pptx --pdf examples/acceptance-sample/render/deck.pdf --strict --expect-slides 15
```

预期:每个检查输出 info,`summary: errors=0, flags=0`,退出码 0(JSON 证据在 `qa/deck-pdf.json`)。

- [ ] **可选挑战(证明它真会红,不是恒绿)**:把 PPTX 里任意一个文本框字号改成 8pt,另存一份,再跑一遍——应出现 `C3-min-font` 的 FLAG 且退出码变 1;改回后恢复全绿。

## 4. 想全量复验?

`python tests/run_tests.py`(7 组负控 + 干净基线 + e2e;需 WPS / PowerPoint COM 与 `pdftotext`,见 `../../tests/README.md`)。

## 附

- 重新生成这份示例:`node make_sample.js`(需全局 pptxgenjs + sharp;`NODE_PATH`);
- 版式判据:`../../docs/scaffolds/slide-patterns-essentials.md`;观感判据:`../../docs/scaffolds/visual-quality-essentials.md`;
- 验收清单全文:`../../acceptance-checklist.md`;独立复核与证据档案:`../../docs/reviews/2026-10-19-cold-verification.md`。
