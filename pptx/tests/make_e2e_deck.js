"use strict";
// End-to-end fixture: a real Chinese deck (topic doubles as the delivery-acceptance
// material) used to walk the full creation -> QA -> fix -> re-verify loop.
//
// Run:  node tests/make_e2e_deck.js   (requires global pptxgenjs + sharp; set NODE_PATH)

const path = require("path");
const { ASSETS, OUT, C, FONT, ensureDirs, newDeck, shapes, save, makeBarPng } = require("./lib");

const G = "5F6B7C"; // caption gray; measured >= 4.5:1 on #FFFFFF and #F7F8FA (qa_check C5)

async function build() {
  const pres = newDeck();
  pres.author = "Command Code QA";
  pres.title = "AI 生成 PPTX 的交付验收";
  const S = shapes(pres);

  // ---- S1 cover -------------------------------------------------------------
  const s1 = pres.addSlide();
  s1.background = { color: C.navy };
  s1.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s1.addText("AI 生成 PPTX 的交付验收", {
    x: 0.8, y: 2.5, w: 11.7, h: 1.1, fontFace: FONT, fontSize: 40, bold: true, color: C.white, margin: 0,
  });
  s1.addText("把「看起来差不多」变成「逐项查过」—— 一份陌生团队也能直接照用的清单", {
    x: 0.8, y: 3.75, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 18, color: C.ice, margin: 0,
  });
  s1.addText("Command Code · pptx skill 产品化样本", {
    x: 0.8, y: 6.6, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });

  // ---- S2 why ---------------------------------------------------------------
  const s2 = pres.addSlide();
  s2.background = { color: C.white };
  s2.addText("为什么交付前必须检查", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  const stats = [
    ["5 类", [{ text: "高频缺陷:占位残留 / 低对比 / 越界", options: { breakLine: true } }, { text: "形变 / 字号过小" }]],
    ["9 项", "可自动检查的断言,由本 skill 的脚本执行"],
    ["0 项", "需要人工逐页重看的残留问题(目标值)"],
  ];
  stats.forEach(([num, desc], i) => {
    const x = 0.8 + i * 4.05;
    s2.addShape(S.rect, { x, y: 2.1, w: 0.34, h: 0.34, fill: { color: C.coral } });
    s2.addText(num, {
      x, y: 2.55, w: 3.6, h: 0.9, fontFace: FONT, fontSize: 40, bold: true, color: C.navy, margin: 0,
    });
    s2.addText(desc, {
      x, y: 3.35, w: 3.6, h: 1.6, fontFace: FONT, fontSize: 13, color: G, valign: "top", margin: 0,
    });
  });

  s2.addText("五类缺陷的检测详见 C1–C9 检查项", {
    x: 0.8, y: 6.25, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: G, margin: 0,
  });

  // ---- S3 process -----------------------------------------------------------
  const s3 = pres.addSlide();
  s3.background = { color: C.light };
  s3.addText("验收流程:四步走", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  const steps = [
    ["1", "生成", "从零或模板产出 PPTX"],
    ["2", "自动检查", "qa_check.py\n跑 9 项断言"],
    ["3", "渲染目检", "转图后逐页看,不靠脑补"],
    ["4", "修正复验", "改到零 flag 再交付"],
  ];
  steps.forEach(([n, name, desc], i) => {
    const x = 0.8 + i * 3.0;
    s3.addShape(S.roundRect, { x, y: 2.1, w: 2.7, h: 2.75, fill: { color: C.card } });
    s3.addText(n, {
      shape: S.ellipse, x: x + 0.28, y: 2.38, w: 0.62, h: 0.62,
      fontFace: FONT, fontSize: 20, bold: true, color: C.white,
      fill: { color: C.coral }, align: "center", valign: "middle",
    });
    s3.addText(name, {
      x: x + 0.28, y: 3.2, w: 2.2, h: 0.5, fontFace: FONT, fontSize: 16, bold: true, color: C.navy, margin: 0,
    });
    s3.addText(desc, {
      x: x + 0.28, y: 3.72, w: 2.2, h: 1.0, fontFace: FONT, fontSize: 13, color: G, valign: "top", margin: 0,
    });
  });

  s3.addText("对应工具:qa_check.py / render_slides.ps1", {
    x: 0.8, y: 6.25, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: G, margin: 0,
  });

  // ---- S4 checks list ---------------------------------------------------------
  const s4 = pres.addSlide();
  s4.background = { color: C.white };
  s4.addText("自动检查项(C1–C9)", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  const checks = [
    ["C1 结构", "页数 / 媒体 / 图片清点"],
    ["C2 占位残留", "扫描模板遗留与演示占位语"],
    ["C3 字号下限", "抓投影环境不可读的小字"],
    ["C4 颜色卫生", "非法 hex / 负向阴影等破坏项"],
    ["C5 对比度", "WCAG 4.5:1 / 3:1 阈值"],
    ["C6 图片比例", "拉伸形变超过 2% 即报"],
    ["C7 页面越界", "文字越过画布边界"],
    ["C8 渲染保真", "导出后不允许丢字"],
    ["C9 可编辑性", "整页图片化(不可再编辑)预警"],
  ];
  checks.forEach(([name, desc], i) => {
    const col = i < 5 ? 0 : 1;
    const row = i % 5;
    const x = 0.8 + col * 6.3;
    const y = 2.0 + row * 0.95;
    s4.addShape(S.ellipse, { x, y: y + 0.15, w: 0.18, h: 0.18, fill: { color: C.coral } });
    s4.addText(name, {
      x: x + 0.36, y, w: 2.6, h: 0.5, fontFace: FONT, fontSize: 14, bold: true, color: C.navy,
    });
    s4.addText(desc, {
      x: x + 0.36, y: y + 0.42, w: 5.4, h: 0.5, fontFace: FONT, fontSize: 12, color: G,
    });
  });

  // ---- S5 thresholds table ----------------------------------------------------
  const s5 = pres.addSlide();
  s5.background = { color: C.white };
  s5.addText("量化阈值(带来源)", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  const head = (t) => ({
    text: t,
    options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: FONT },
  });
  const cell = (t) => ({
    text: t,
    options: { fill: { color: C.white }, color: C.ink, fontSize: 12, fontFace: FONT },
  });
  s5.addTable(
    [
      [head("检查项"), head("阈值"), head("来源")],
      [cell("对比度(正文)"), cell("\u2265 4.5:1"), cell("WCAG 2.1 AA")],
      [cell("对比度(大字号)"), cell("\u2265 3:1"), cell("WCAG 2.1 AA")],
      [cell("正文字号"), cell("\u2265 10pt"), cell("本项目规范")],
      [cell("图片形变"), cell("\u2264 2%"), cell("实测容差(qa_check)")],
      [cell("渲染保真"), cell("无内容缺失"), cell("实测(C8 控制组)")],
      [cell("可编辑性"), cell("不得整页图片化"), cell("实测(C9 控制组)")],
    ],
    {
      x: 0.8, y: 1.9, w: 11.7, colW: [4.5, 3.6, 3.6], rowH: 0.52,
      valign: "middle", border: { pt: 1, color: "D7DEE8" },
    }
  );
  s5.addText("阈值与来源详见 pptx/acceptance-checklist.md", {
    x: 0.8, y: 6.25, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: G, margin: 0,
  });

  // ---- S6 output sample -------------------------------------------------------
  const s6 = pres.addSlide();
  s6.background = { color: C.white };
  s6.addText("自动检查的输出长什么样", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  s6.addText(
    [
      { text: "每条问题带页码与形状定位", options: { bullet: true, breakLine: true } },
      { text: "JSON 报告可接入 CI 门禁(--strict)", options: { bullet: true, breakLine: true } },
      { text: "零 flag 才进入渲染目检环节", options: { bullet: true, breakLine: true } },
      { text: "阈值可按项目在上限内收紧", options: { bullet: true } },
    ],
    { x: 0.8, y: 2.55, w: 4.6, h: 2.8, fontFace: FONT, fontSize: 14, color: C.ink, paraSpaceAfter: 6 }
  );
  s6.addImage({ path: path.join(ASSETS, "chart-bars.png"), x: 5.9, y: 1.9, w: 6.8, h: 3.4 });
  s6.addText("示意:各检查项在首轮发现的问题数量", {
    x: 5.9, y: 5.45, w: 6.8, h: 0.4, fontFace: FONT, fontSize: 12, color: G, align: "center",
  });

  // ---- S7 closing -------------------------------------------------------------
  const s7 = pres.addSlide();
  s7.background = { color: C.navy };
  s7.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s7.addText("把清单用在下一份交付上", {
    x: 0.8, y: 2.5, w: 11.7, h: 0.9, fontFace: FONT, fontSize: 36, bold: true, color: C.white, margin: 0,
  });
  s7.addText(
    [
      { text: "生成后先跑 qa_check.py,再进入视觉检查", options: { bullet: true, breakLine: true } },
      { text: "修正后复跑,直到零 flag", options: { bullet: true, breakLine: true } },
      { text: "拿不准的地方,以目标环境打开为准", options: { bullet: true } },
    ],
    { x: 0.8, y: 3.6, w: 11.7, h: 2.2, fontFace: FONT, fontSize: 16, color: C.ice, paraSpaceAfter: 8 }
  );
  s7.addText("pptx skill · acceptance-checklist.md", {
    x: 0.8, y: 6.6, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });

  await save(pres, "e2e_deck.pptx");
}

(async () => {
  ensureDirs();
  await makeBarPng(path.join(ASSETS, "chart-bars.png"), 1600, 800, [
    { frac: 0.85, color: C.navy },
    { frac: 0.62, color: "3A4A8C" },
    { frac: 0.45, color: "6C7BBF" },
    { frac: 0.28, color: "AAB6E8" },
  ]);
  await build();
  console.log("e2e deck done -> " + OUT);
})().catch((e) => {
  console.error("FAIL:", e);
  process.exit(1);
});
