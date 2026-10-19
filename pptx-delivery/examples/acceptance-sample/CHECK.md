# 检查指引 — 亲手验收这份示例

> 这是一份**参考示例交付包**(非测试夹具):`deck.pptx` + 渲染图 + QA 证据 + 本指引。
> 目的:让你亲手确认「生成 → 断言 → 渲染复验 → 验收清单」这条链是真的。

## 1. 打开来看(观感与可编辑性)

用 WPS / PowerPoint 打开 `deck.pptx`,逐页对照:

- [ ] 每页都能直接改文字、移动形状(不是整页图片)——对应 C9 可编辑性;
- [ ] 标题与正文左缘在同一条线上(0.8\"),内容页底部注脚落在同一高度(≈6.25\");
- [ ] 颜色只有三个角色:标题藏青 `1E2761` / 正文深灰 `222222` / 说明与注脚灰 `5F6B7C`(深底页用白 / `CADCFC`);
- [ ] 第 3 页四张卡片、第 4 页表格线、第 5 页柱图(2:1,无拉伸);
- [ ] 图片的"替代文字"是描述而不是本地路径(右键图片 → 查看替代文字)。

## 2. 看渲染图与 PDF(导出保真)

- [ ] 打开 `render/slide-01..06.png`(或 `render/deck.pdf`),与直接开 PPTX 的观感一致;
- [ ] 第 4 页表格无缺行、第 5 页柱图无变形(对应 C8 / C6)。

## 3. 亲手跑机器断言(一条命令,预期全绿)

在 pptx-delivery 目录下:

```powershell
python scripts/qa_check.py examples/acceptance-sample/deck.pptx --pdf examples/acceptance-sample/render/deck.pdf --strict --expect-slides 6
```

预期:每个检查输出 info,`summary: errors=0, flags=0`,退出码 0(JSON 证据在 `qa/deck-pdf.json`)。

- [ ] **可选挑战(证明它真会红,不是恒绿)**:把 PPTX 里任意一个文本框字号改成 8pt,另存一份,再跑一遍——应出现 `C3-min-font` 的 FLAG 且退出码变 1;改回后恢复全绿。

## 4. 想全量复验?

`python tests/run_tests.py`(7 组负控 + 干净基线 + e2e;需 WPS / PowerPoint COM 与 `pdftotext`,见 `../../tests/README.md`)。

## 附

- 重新生成这份示例:`node make_sample.js`(需全局 pptxgenjs + sharp;`NODE_PATH` 见 README);
- 验收清单全文:`../../acceptance-checklist.md`;独立复核与证据档案:`../../docs/reviews/2026-10-19-cold-verification.md`。
