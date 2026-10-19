"use strict";
// acceptance-sample: 参考示例交付包的本体生成脚本(11 页,每页一种版式)。
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
const MONO = "Consolas";

// Palette: "Midnight Executive" + one accent (same convention as the skill's fixtures).
const C = {
  navy: "1E2761",
  ice: "CADCFC",
  white: "FFFFFF",
  ink: "222222",
  gray: "5F6B7C", // captions / descriptions; >= 4.5:1 on #FFFFFF / #F7F8FA / #F0F4FA
  light: "F7F8FA",
  card: "F0F4FA",
  coral: "E4574F", // large-text / shape accent only (3.64:1 on white -> use >= 18pt, or 14pt+bold)
  border: "D7DEE8",
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

  const title = (s, t) =>
    s.addText(t, {
      x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy, margin: 0,
    });
  const anchor = (s, t) =>
    s.addText(t, {
      x: 0.8, y: 6.25, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });

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

  // ---- S2 parts grid (6 cards, 2 x 3) ------------------------------------------
  const s2 = pres.addSlide();
  s2.background = { color: C.white };
  title(s2, "这份技能由六个部件组成");
  const parts = [
    ["01", "断言引擎", "qa_check.py:C1–C9 自动断言"],
    ["02", "负控套件", "7 组必红夹具 + 干净基线"],
    ["03", "渲染链", "WPS COM / LibreOffice"],
    ["04", "验收清单", "L0–L3 分层判据逐项勾"],
    ["05", "视觉判据", "间距 / 角色 / 构成三条线"],
    ["06", "复核档案", "校准探针 + 证据复跑"],
  ];
  parts.forEach(([n, name, desc], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.8 + col * 4.0;
    const y = 2.0 + row * 1.88;
    s2.addShape(S.roundRect, { x, y, w: 3.6, h: 1.6, fill: { color: C.card } });
    s2.addText(n, {
      x: x + 0.25, y: y + 0.2, w: 0.8, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: C.coral, margin: 0,
    });
    s2.addText(name, {
      x: x + 0.25, y: y + 0.52, w: 3.1, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: C.navy, margin: 0,
    });
    s2.addText(desc, {
      x: x + 0.25, y: y + 0.98, w: 3.1, h: 0.5, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  anchor(s2, "第六件(复核档案)不在本 deck 里,在 docs/reviews/");

  // ---- S3 stats (4 up) --------------------------------------------------------
  const s3 = pres.addSlide();
  s3.background = { color: C.white };
  title(s3, "这份示例经过哪些检查");
  const stats = [
    ["9 项", "自动断言(C1–C9)"],
    ["7 组", "必红负控 + 基线"],
    ["2 轮", "独立复核(外眼)"],
    ["0 flag", "本样张的机器结果"],
  ];
  stats.forEach(([num, desc], i) => {
    const x = 0.8 + i * 3.0;
    s3.addShape(S.rect, { x, y: 2.1, w: 0.34, h: 0.34, fill: { color: C.coral } });
    s3.addText(num, {
      x, y: 2.55, w: 2.9, h: 0.9, fontFace: FONT, fontSize: 40, bold: true, color: C.navy, margin: 0,
    });
    s3.addText(desc, {
      x, y: 3.35, w: 2.9, h: 0.6, fontFace: FONT, fontSize: 13, color: C.gray, margin: 0,
    });
  });
  anchor(s3, "数值口径:qa_check.py 输出;复核记录见 docs/reviews/");

  // ---- S4 process (4 cards) ---------------------------------------------------
  const s4 = pres.addSlide();
  s4.background = { color: C.light };
  title(s4, "交付流程:四步走");
  const steps = [
    ["1", "生成", "从零产出 PPTX"],
    ["2", "断言", "qa_check --strict"],
    ["3", "渲染", "转 PNG / PDF"],
    ["4", "复验", "复跑 + 逐页目检"],
  ];
  steps.forEach(([n, name, desc], i) => {
    const x = 0.8 + i * 3.0;
    s4.addShape(S.roundRect, { x, y: 2.1, w: 2.7, h: 2.75, fill: { color: C.card } });
    s4.addText(n, {
      shape: S.ellipse, x: x + 0.28, y: 2.38, w: 0.62, h: 0.62,
      fontFace: FONT, fontSize: 20, bold: true, color: C.white,
      fill: { color: C.coral }, align: "center", valign: "middle",
    });
    s4.addText(name, {
      x: x + 0.28, y: 3.2, w: 2.2, h: 0.5, fontFace: FONT, fontSize: 16, bold: true, color: C.navy, margin: 0,
    });
    s4.addText(desc, {
      x: x + 0.28, y: 3.72, w: 2.2, h: 1.0, fontFace: FONT, fontSize: 13, color: C.gray, valign: "top", margin: 0,
    });
  });
  anchor(s4, "对应脚本:make_sample.js / qa_check.py / render_slides.ps1");

  // ---- S5 checks matrix (3 x 3 chips) ------------------------------------------
  const s5 = pres.addSlide();
  s5.background = { color: C.white };
  title(s5, "自动断言:九项,各有其责");
  const checks = [
    ["C1 结构", "页数 / 媒体清点"],
    ["C2 占位", "模板残留扫描"],
    ["C3 字号", "10pt 硬下限"],
    ["C4 颜色", "非法 hex / 负影"],
    ["C5 对比", "4.5:1 / 3:1 阈值"],
    ["C6 比例", "形变 ≤ 2%"],
    ["C7 越界", "跨缘词框"],
    ["C8 保真", "导出不丢字"],
    ["C9 编辑", "整页图预警"],
  ];
  checks.forEach(([name, desc], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.8 + col * 4.0;
    const y = 1.9 + row * 1.42;
    s5.addShape(S.roundRect, { x, y, w: 3.6, h: 1.2, fill: { color: C.card } });
    s5.addText(name, {
      x: x + 0.22, y: y + 0.18, w: 3.1, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
    });
    s5.addText(desc, {
      x: x + 0.22, y: y + 0.66, w: 3.1, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  anchor(s5, "每项都带位置与形状引用;JSON 可直接接 CI 门禁");

  // ---- S6 results table -------------------------------------------------------
  const s6 = pres.addSlide();
  s6.background = { color: C.white };
  title(s6, "本样张的抽检结果");
  const head = (t) => ({
    text: t,
    options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: FONT },
  });
  const cell = (t) => ({
    text: t,
    options: { fill: { color: C.white }, color: C.ink, fontSize: 12, fontFace: FONT },
  });
  s6.addTable(
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
      valign: "middle", border: { pt: 1, color: C.border },
    }
  );
  anchor(s6, "证据文件随本包提供;逐项检查动作见 CHECK.md");

  // ---- S7 command terminal block ----------------------------------------------
  const s7 = pres.addSlide();
  s7.background = { color: C.light };
  title(s7, "一条链跑下来:四类命令");
  s7.addShape(S.roundRect, { x: 0.8, y: 1.95, w: 7.4, h: 3.9, fill: { color: C.navy } });
  s7.addText("PowerShell · 在项目根目录顺序执行", {
    x: 1.15, y: 2.12, w: 6.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s7.addText(
    [
      { text: "$ node make_sample.js", options: { breakLine: true } },
      { text: "$ python scripts/normalize_pptx_order.py inplace deck.pptx", options: { breakLine: true } },
      { text: "$ python scripts/qa_check.py deck.pptx --pdf render/deck.pdf --strict", options: { breakLine: true } },
      { text: "$ scripts/render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf" },
    ],
    {
      x: 1.15, y: 2.55, w: 6.9, h: 3.0, fontFace: MONO, fontSize: 13,
      color: C.white, paraSpaceAfter: 12, margin: 0,
    }
  );
  s7.addText(
    [
      { text: "先归一化,再断言——顺序别乱", options: { bullet: true, breakLine: true } },
      { text: "带 PDF 才覆盖 C7 / C8", options: { bullet: true, breakLine: true } },
      { text: "零 flag 才进入渲染目检", options: { bullet: true } },
    ],
    { x: 8.55, y: 2.3, w: 4.05, h: 2.8, fontFace: FONT, fontSize: 14, color: C.ink, paraSpaceAfter: 10, margin: 0 }
  );
  anchor(s7, "完整说明见 SKILL.md 的 Quick Reference");

  // ---- S8 before / after panels -----------------------------------------------
  const s8 = pres.addSlide();
  s8.background = { color: C.white };
  title(s8, "同一件事,两种做法");
  const panel = (x, fill, heading, headingColor, items, markColor) => {
    s8.addShape(S.roundRect, { x, y: 1.9, w: 5.8, h: 4.0, fill: { color: fill } });
    s8.addText(heading, {
      x: x + 0.35, y: 2.1, w: 5.1, h: 0.45, fontFace: FONT, fontSize: 16, bold: true, color: headingColor, margin: 0,
    });
    items.forEach((t, i) => {
      const y = 2.75 + i * 0.62;
      s8.addShape(S.rect, { x: x + 0.38, y: y + 0.1, w: 0.14, h: 0.14, fill: { color: markColor } });
      s8.addText(t, {
        x: x + 0.66, y, w: 4.9, h: 0.4, fontFace: FONT, fontSize: 13, color: C.ink, margin: 0,
      });
    });
  };
  panel(0.8, C.light, "旧做法:靠感觉", C.gray, [
    "看起来差不多就交付",
    "导出丢字,交付后才发现",
    "每份 deck 各写各的样式",
    "返工靠人肉复看",
  ], C.coral);
  panel(6.73, C.card, "本技能:按清单", C.navy, [
    "逐项断言,零 flag 才放行",
    "C7 / C8 盯导出保真",
    "角色色与锚线有约定",
    "复核档案可回溯",
  ], C.navy);
  anchor(s8, "差别不在工具,在“每项都有人签过字”");

  // ---- S9 color roles ----------------------------------------------------------
  const s9 = pres.addSlide();
  s9.background = { color: C.white };
  title(s9, "一套颜色,三个角色");
  const swatches = [
    [C.navy, "1E2761", "标题 / 名称"],
    [C.ink, "222222", "正文"],
    [C.gray, "5F6B7C", "说明 / 注脚"],
    [C.coral, "E4574F", "点缀(大字)"],
    [C.light, "F7F8FA", "浅底"],
    [C.card, "F0F4FA", "卡片底"],
  ];
  swatches.forEach(([fill, hex, role], i) => {
    const x = 0.8 + i * 1.95;
    s9.addShape(S.rect, { x, y: 1.9, w: 1.65, h: 1.1, fill: { color: fill }, line: { color: C.border, width: 1 } });
    s9.addText(hex, {
      x, y: 3.08, w: 1.65, h: 0.3, fontFace: MONO, fontSize: 12, color: C.ink, margin: 0,
    });
    s9.addText(role, {
      x, y: 3.4, w: 1.65, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  s9.addText(
    [
      { text: "白字只做大字:珊瑚底白字 3.64:1,仅 ≥18pt 或 ≥14pt 粗", options: { bullet: true, breakLine: true } },
      { text: "两档灰(222222 / 5F6B7C)对三种浅底均 ≥ 4.5:1", options: { bullet: true, breakLine: true } },
      { text: "数值口径:WCAG 2.1,不四舍五入(qa_check C5 实测)", options: { bullet: true } },
    ],
    { x: 0.8, y: 4.15, w: 11.7, h: 1.6, fontFace: FONT, fontSize: 13, color: C.ink, paraSpaceAfter: 8, margin: 0 }
  );
  anchor(s9, "角色分工见 typography.md;本页是它的可视版");

  // ---- S10 output sample -------------------------------------------------------
  const s10 = pres.addSlide();
  s10.background = { color: C.white };
  title(s10, "机器输出的样子(示意)");
  s10.addText(
    [
      { text: "每条问题带页码与形状定位", options: { bullet: true, breakLine: true } },
      { text: "JSON 报告可接入 CI 门禁", options: { bullet: true, breakLine: true } },
      { text: "零 flag 才进入目检环节", options: { bullet: true, breakLine: true } },
      { text: "阈值可在上限内按项目收紧", options: { bullet: true } },
    ],
    { x: 0.8, y: 3.4, w: 4.3, h: 2.8, fontFace: FONT, fontSize: 14, color: C.ink, paraSpaceAfter: 6 }
  );
  s10.addImage({ path: path.join(ASSETS, "chart-bars.png"), x: 5.6, y: 2.25, w: 7.2, h: 3.6, altText: "柱状图示意:各检查项首轮命中数" });
  s10.addText("示意:各检查项首轮命中数", {
    x: 5.6, y: 6.0, w: 7.2, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, align: "center",
  });

  // ---- S11 closing -------------------------------------------------------------
  const s11 = pres.addSlide();
  s11.background = { color: C.navy };
  s11.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s11.addText("拿它当模板,或直接照流程走", {
    x: 0.8, y: 2.5, w: 11.7, h: 0.9, fontFace: FONT, fontSize: 36, bold: true, color: C.white, margin: 0,
  });
  s11.addText(
    [
      { text: "本包 = deck + 渲染图 + QA 证据 + 检查指引", options: { bullet: true, breakLine: true } },
      { text: "改内容重生成:node make_sample.js", options: { bullet: true, breakLine: true } },
      { text: "全量复跑:python tests/run_tests.py", options: { bullet: true } },
    ],
    { x: 0.8, y: 3.6, w: 11.7, h: 2.2, fontFace: FONT, fontSize: 16, color: C.ice, paraSpaceAfter: 8 }
  );
  s11.addText("pptx-delivery · examples/acceptance-sample", {
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
