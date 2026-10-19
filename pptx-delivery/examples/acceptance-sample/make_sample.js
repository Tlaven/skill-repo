"use strict";
// acceptance-sample: 参考示例交付包的本体生成脚本。
// 约定与 tests/make_e2e_deck.js 同源(角色色 / 底锚线 / 标题对齐),但本文件 standalone——
// 只依赖全局 pptxgenjs + sharp,复制到任何项目可直接改内容使用。
//
// Run:  set NODE_PATH to `npm root -g`, then:  node make_sample.js
// Out:  deck.pptx + assets/chart-bars.png(同目录)

const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const HERE = __dirname;
const ASSETS = path.join(HERE, "assets");

// Palette: "Midnight Executive" + one accent (same convention as the skill's fixtures).
const C = {
  navy: "1E2761",
  ice: "CADCFC",
  white: "FFFFFF",
  ink: "222222",
  gray: "5F6B7C", // captions / descriptions; >= 4.5:1 on #FFFFFF / #F7F8FA / #F0F4FA
  light: "F7F8FA",
  card: "F0F4FA",
  coral: "E4574F", // large-text / shape accent only (3.64:1 on white -> use >= 18pt)
};
const FONT = "Microsoft YaHei";

function hexToRgb(hex) {
  return {
    r: parseInt(hex.slice(0, 2), 16),
    g: parseInt(hex.slice(2, 4), 16),
    b: parseInt(hex.slice(4, 6), 16),
    alpha: 1,
  };
}

// Bar-chart-like PNG (no embedded text; labels live in slide text). Aspect 2:1.
async function makeBarPng(file, w, h, bars) {
  const pad = Math.round(h * 0.08);
  const innerH = h - pad * 2;
  const n = bars.length;
  const slot = w / n;
  const barW = Math.round(slot * 0.45);
  let rects = "";
  bars.forEach((b, i) => {
    const bh = Math.round(innerH * b.frac);
    const x = Math.round(i * slot + (slot - barW) / 2);
    const y = h - pad - bh;
    rects += `<rect x="${x}" y="${y}" width="${barW}" height="${bh}" rx="${Math.round(barW * 0.06)}" fill="#${b.color}"/>`;
  });
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">` +
    `<rect width="${w}" height="${h}" fill="#FFFFFF"/>` +
    `<line x1="${pad}" y1="${h - pad}" x2="${w - pad}" y2="${h - pad}" stroke="#E2E8F0" stroke-width="3"/>` +
    rects +
    `</svg>`;
  await sharp(Buffer.from(svg)).png().toFile(file);
}

async function build() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.author = "Command Code";
  pres.title = "交付示例:一份逐项可查的 PPTX";
  const S = pres.ShapeType || pres.shapes;

  // ---- S1 cover ---------------------------------------------------------------
  const s1 = pres.addSlide();
  s1.background = { color: C.navy };
  s1.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s1.addText("交付示例:一份逐项可查的 PPTX", {
    x: 0.8, y: 2.5, w: 11.7, h: 1.1, fontFace: FONT, fontSize: 40, bold: true, color: C.white, margin: 0,
  });
  s1.addText("生成 → 断言 → 渲染复验 → 验收清单,一步不落", {
    x: 0.8, y: 3.75, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 18, color: C.ice, margin: 0,
  });
  s1.addText("Command Code · pptx-delivery 示例交付包", {
    x: 0.8, y: 6.6, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });

  // ---- S2 stats ---------------------------------------------------------------
  const s2 = pres.addSlide();
  s2.background = { color: C.white };
  s2.addText("这份示例经过哪些检查", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy, margin: 0,
  });
  const stats = [
    ["9 项", "自动断言(C1–C9)全部执行"],
    ["2 轮", "独立复核:冷启动 + 视觉"],
    ["0 flag", "本样张的机器检查结果"],
  ];
  stats.forEach(([num, desc], i) => {
    const x = 0.8 + i * 4.05;
    s2.addShape(S.rect, { x, y: 2.1, w: 0.34, h: 0.34, fill: { color: C.coral } });
    s2.addText(num, {
      x, y: 2.55, w: 3.6, h: 0.9, fontFace: FONT, fontSize: 40, bold: true, color: C.navy, margin: 0,
    });
    s2.addText(desc, {
      x, y: 3.35, w: 3.6, h: 0.6, fontFace: FONT, fontSize: 13, color: C.gray, margin: 0,
    });
  });
  s2.addText("数值口径:qa_check.py 输出;复核记录见 docs/reviews/", {
    x: 0.8, y: 6.25, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
  });

  // ---- S3 process -------------------------------------------------------------
  const s3 = pres.addSlide();
  s3.background = { color: C.light };
  s3.addText("交付流程:四步走", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy, margin: 0,
  });
  const steps = [
    ["1", "生成", "从零产出 PPTX"],
    ["2", "断言", "qa_check --strict"],
    ["3", "渲染", "转 PNG / PDF"],
    ["4", "复验", "复跑 + 逐页目检"],
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
      x: x + 0.28, y: 3.72, w: 2.2, h: 1.0, fontFace: FONT, fontSize: 13, color: C.gray, valign: "top", margin: 0,
    });
  });
  s3.addText("对应脚本:make_sample.js / qa_check.py / render_slides.ps1", {
    x: 0.8, y: 6.25, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
  });

  // ---- S4 results table -------------------------------------------------------
  const s4 = pres.addSlide();
  s4.background = { color: C.white };
  s4.addText("本样张的抽检结果", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy, margin: 0,
  });
  const head = (t) => ({
    text: t,
    options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: FONT },
  });
  const cell = (t) => ({
    text: t,
    options: { fill: { color: C.white }, color: C.ink, fontSize: 12, fontFace: FONT },
  });
  s4.addTable(
    [
      [head("检查项"), head("结果"), head("证据文件")],
      [cell("C5 对比度"), cell("全部 ≥ 4.5:1"), cell("qa/deck-pdf.json")],
      [cell("C3 字号下限"), cell("最小字 12pt"), cell("qa/deck-pdf.json")],
      [cell("C6 图片比例"), cell("偏差 0.0%"), cell("qa/deck-pdf.json")],
      [cell("C8 渲染保真"), cell("无缺字"), cell("render/deck.pdf")],
      [cell("C9 可编辑性"), cell("有文本,可编辑"), cell("打开 deck.pptx")],
    ],
    {
      x: 0.8, y: 1.9, w: 11.7, colW: [4.5, 3.6, 3.6], rowH: 0.52,
      valign: "middle", border: { pt: 1, color: "D7DEE8" },
    }
  );
  s4.addText("证据文件随本包提供;逐项检查动作见 CHECK.md", {
    x: 0.8, y: 6.25, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
  });

  // ---- S5 output sample -------------------------------------------------------
  const s5 = pres.addSlide();
  s5.background = { color: C.white };
  s5.addText("机器输出的样子(示意)", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy, margin: 0,
  });
  s5.addText(
    [
      { text: "每条问题带页码与形状定位", options: { bullet: true, breakLine: true } },
      { text: "JSON 报告可接入 CI 门禁", options: { bullet: true, breakLine: true } },
      { text: "零 flag 才进入目检环节", options: { bullet: true, breakLine: true } },
      { text: "阈值可在上限内按项目收紧", options: { bullet: true } },
    ],
    { x: 0.8, y: 3.4, w: 4.3, h: 2.8, fontFace: FONT, fontSize: 14, color: C.ink, paraSpaceAfter: 6 }
  );
  s5.addImage({ path: path.join(ASSETS, "chart-bars.png"), x: 5.6, y: 2.25, w: 7.2, h: 3.6, altText: "柱状图示意:各检查项首轮命中数" });
  s5.addText("示意:各检查项首轮命中数", {
    x: 5.6, y: 6.0, w: 7.2, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, align: "center",
  });

  // ---- S6 closing -------------------------------------------------------------
  const s6 = pres.addSlide();
  s6.background = { color: C.navy };
  s6.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s6.addText("拿它当模板,或直接照流程走", {
    x: 0.8, y: 2.5, w: 11.7, h: 0.9, fontFace: FONT, fontSize: 36, bold: true, color: C.white, margin: 0,
  });
  s6.addText(
    [
      { text: "本包 = deck + 渲染图 + QA 证据 + 检查指引", options: { bullet: true, breakLine: true } },
      { text: "改内容重生成:node make_sample.js", options: { bullet: true, breakLine: true } },
      { text: "全量复跑:python tests/run_tests.py", options: { bullet: true } },
    ],
    { x: 0.8, y: 3.6, w: 11.7, h: 2.2, fontFace: FONT, fontSize: 16, color: C.ice, paraSpaceAfter: 8 }
  );
  s6.addText("pptx-delivery · examples/acceptance-sample", {
    x: 0.8, y: 6.6, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });

  const deck = path.join(HERE, "deck.pptx");
  await pres.writeFile({ fileName: deck });
  console.log("wrote " + deck);
}

(async () => {
  fs.mkdirSync(ASSETS, { recursive: true });
  await makeBarPng(path.join(ASSETS, "chart-bars.png"), 1600, 800, [
    { frac: 0.85, color: C.navy },
    { frac: 0.62, color: "3A4A8C" },
    { frac: 0.45, color: "6C7BBF" },
    { frac: 0.28, color: "AAB6E8" },
  ]);
  await build();
  console.log("acceptance sample done -> " + HERE);
})().catch((e) => {
  console.error("FAIL:", e);
  process.exit(1);
});
