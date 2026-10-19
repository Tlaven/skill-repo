"use strict";
// Negative controls + clean baseline for qa_check.py.
//
// Decks produced (into tests/out/):
//   clean.pptx             baseline; qa_check must report 0 errors / 0 flags
//   c1_placeholder.pptx    leftover placeholder text        -> C2 must fire
//   c2_lowcontrast.pptx    low-contrast text                -> C5 must fire
//   c3_overflow.pptx       text spilling off the slide edge -> C8 must fire
//   c4_stretched.pptx      image stretched out of aspect    -> C6 must fire
//   c5_tinyfont.pptx       below-minimum font size          -> C3 must fire
//   c6_flatslide.pptx      full-page image, no text (non-editable) -> C9 must fire
//
// Run:  node tests/make_controls.js   (requires global pptxgenjs + sharp; set NODE_PATH)

const path = require("path");
const {
  OUT, ASSETS, C, FONT, ensureDirs, newDeck, shapes, save,
  makeFlatPng, makeBarPng,
} = require("./lib");

async function buildClean() {
  const pres = newDeck();
  const S = shapes(pres);

  // s1 cover (dark)
  const s1 = pres.addSlide();
  s1.background = { color: C.navy };
  s1.addShape(S.rect, { x: 0.8, y: 2.15, w: 0.32, h: 0.32, fill: { color: C.coral } });
  s1.addText("交付验收 · 基线样张", {
    x: 0.8, y: 2.6, w: 11.7, h: 1.1, fontFace: FONT, fontSize: 40, bold: true, color: C.white,
  });
  s1.addText("qa_check.py 干净对照:预期 0 error / 0 flag", {
    x: 0.8, y: 3.8, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 18, color: C.ice,
  });

  // s2 content with image (exact aspect)
  const s2 = pres.addSlide();
  s2.background = { color: C.white };
  s2.addText("内容页:图文并排", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  s2.addText(
    [
      { text: "所有字号 >= 12pt,颜色对比达标", options: { bullet: true, breakLine: true } },
      { text: "图片按原始比例放置(1200x300 -> 4.8 x 1.2 in)", options: { bullet: true, breakLine: true } },
      { text: "边距 >= 0.5in,元素间距 >= 0.3in", options: { bullet: true } },
    ],
    { x: 0.8, y: 1.7, w: 6.2, h: 3.2, fontFace: FONT, fontSize: 14, color: C.ink }
  );
  s2.addImage({ path: path.join(ASSETS, "flat-1200x300.png"), x: 7.6, y: 1.7, w: 4.8, h: 1.2 });

  // s3 table
  const s3 = pres.addSlide();
  s3.background = { color: C.light };
  s3.addText("表格页", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  const head = (t) => ({ text: t, options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: FONT } });
  const cell = (t) => ({ text: t, options: { color: C.ink, fontSize: 12, fontFace: FONT } });
  s3.addTable(
    [
      [head("检查项"), head("阈值"), head("依据")],
      [cell("对比度"), cell("4.5:1"), cell("WCAG 2.1")],
      [cell("正文字号"), cell("\u2265 12pt"), cell("内部规范")],
      [cell("图片形变"), cell("\u2264 2%"), cell("实测容差")],
    ],
    { x: 0.8, y: 1.7, w: 11.7, colW: [3.9, 3.9, 3.9], rowH: 0.5, valign: "middle", border: { pt: 1, color: "D7DEE8" } }
  );

  await save(pres, "clean.pptx");
}

async function buildC1Placeholder() {
  const pres = newDeck();
  const s1 = pres.addSlide();
  s1.background = { color: C.white };
  s1.addText("占位符残留控制组", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  s1.addText("XXXX 这里是占位标题", {
    x: 0.8, y: 1.8, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 16, color: C.ink,
  });
  s1.addText("Click to edit 单击此处填写内容", {
    x: 0.8, y: 2.6, w: 11.7, h: 0.5, fontFace: FONT, fontSize: 14, color: C.ink,
  });
  s1.addText("其余内容正常,字号与对比度无问题。", {
    x: 0.8, y: 3.4, w: 11.7, h: 0.5, fontFace: FONT, fontSize: 14, color: C.ink,
  });
  await save(pres, "c1_placeholder.pptx");
}

async function buildC2LowContrast() {
  const pres = newDeck();

  const s1 = pres.addSlide();
  s1.background = { color: C.white };
  s1.addText("低对比度控制组 A", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  s1.addText("浅灰文字压在纯白底上(约 1.4:1)", {
    x: 0.8, y: 1.9, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 16, color: "DDDDDD",
  });

  const s2 = pres.addSlide();
  s2.background = { color: C.cream };
  s2.addText("低对比度控制组 B", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  s2.addText("近白文字压在奶油底上(约 1.1:1)", {
    x: 0.8, y: 1.9, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 16, color: "FCF6F5",
  });

  await save(pres, "c2_lowcontrast.pptx");
}

async function buildC3Overflow() {
  const pres = newDeck();
  const s1 = pres.addSlide();
  s1.background = { color: C.white };
  s1.addText("文本越界控制组", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  s1.addText(
    "这一整段文字被刻意放得又长又大,但没有缩排也没有自适应,于是它会一路溢出文本框、继续向下延伸," +
      "直到越过幻灯片的下边缘,最后几行将落在画面之外。这就是真实工作里最常见的溢出事故:" +
      "调大字号或补了一句之后没有重新排版,导出时就丢内容。",
    {
      x: 0.8, y: 5.35, w: 11.7, h: 0.9, fontFace: FONT, fontSize: 40, color: C.ink,
    }
  );
  await save(pres, "c3_overflow.pptx");
}

async function buildC4Stretched() {
  const pres = newDeck();
  const s1 = pres.addSlide();
  s1.background = { color: C.white };
  s1.addText("图片拉伸控制组", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  // wrong: native 800x200 (4:1) displayed as 6 x 3 in (2:1)
  s1.addImage({ path: path.join(ASSETS, "flat-800x200.png"), x: 0.8, y: 1.7, w: 6, h: 3 });
  s1.addText("左:被纵向拉伸(形变 50%)", {
    x: 0.8, y: 4.9, w: 6, h: 0.5, fontFace: FONT, fontSize: 12, color: C.gray,
  });
  // correct reference
  s1.addImage({ path: path.join(ASSETS, "flat-800x200.png"), x: 7.8, y: 1.7, w: 4, h: 1 });
  s1.addText("右:保持原始比例", {
    x: 7.8, y: 2.9, w: 4, h: 0.5, fontFace: FONT, fontSize: 12, color: C.gray,
  });
  await save(pres, "c4_stretched.pptx");
}

async function buildC5TinyFont() {
  const pres = newDeck();
  const s1 = pres.addSlide();
  s1.background = { color: C.white };
  s1.addText("字号过小控制组", {
    x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy,
  });
  s1.addText("正常段落:这一段是 14pt,符合下限要求。", {
    x: 0.8, y: 1.9, w: 11.7, h: 0.5, fontFace: FONT, fontSize: 14, color: C.ink,
  });
  s1.addText("这条备注只有 7pt,投影环境基本不可读,应当被检查抓出。", {
    x: 0.8, y: 2.7, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 7, color: C.ink,
  });
  await save(pres, "c5_tinyfont.pptx");
}

async function buildC6FlatSlide() {
  const pres = newDeck();
  const s1 = pres.addSlide();
  s1.background = { color: C.white };
  // Pre-rendered page: full-bleed image, zero text -> non-editable delivery failure (C9).
  s1.addImage({ path: path.join(ASSETS, "flat-1600x900.png"), x: 0, y: 0, w: 13.333, h: 7.5 });
  await save(pres, "c6_flatslide.pptx");
}

(async () => {
  ensureDirs();
  await makeFlatPng(path.join(ASSETS, "flat-1200x300.png"), 1200, 300, C.navy);
  await makeFlatPng(path.join(ASSETS, "flat-800x200.png"), 800, 200, C.coral);
  await makeFlatPng(path.join(ASSETS, "flat-1600x900.png"), 1600, 900, C.ice);
  await makeBarPng(path.join(ASSETS, "chart-bars.png"), 1600, 800, [
    { frac: 0.85, color: C.navy },
    { frac: 0.62, color: "3A4A8C" },
    { frac: 0.45, color: "6C7BBF" },
    { frac: 0.28, color: "AAB6E8" },
  ]);
  await buildClean();
  await buildC1Placeholder();
  await buildC2LowContrast();
  await buildC3Overflow();
  await buildC4Stretched();
  await buildC5TinyFont();
  await buildC6FlatSlide();
  console.log("controls done -> " + OUT);
})().catch((e) => {
  console.error("FAIL:", e);
  process.exit(1);
});
