"use strict";
// acceptance-sample: 参考示例交付包的本体生成脚本(15 页,12 种原型;见 docs/scaffolds/slide-patterns-essentials.md)。
// 约定与 tests/make_e2e_deck.js 同源(角色色 / 底锚线 / 标题对齐),但本文件 standalone——
// 只依赖全局 pptxgenjs + sharp,复制到任何项目可直接改内容使用。
//
// Run:  set NODE_PATH to `npm root -g`, then:  node make_sample.js
// Out:  deck.pptx + assets/chart-bars.png + assets/dot-grid.png(同目录)

const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const HERE = __dirname;
const ASSETS = path.join(HERE, "assets");
const MONO = "Consolas";

const C = {
  navy: "1E2761",
  ice: "CADCFC",
  white: "FFFFFF",
  ink: "222222",
  gray: "5F6B7C",
  light: "F7F8FA",
  card: "F0F4FA",
  coral: "E4574F",
  border: "D7DEE8",
  slate: "3A4A8C",
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

// Subtle dot grid over the dark cover (atmosphere layer; carries no information).
async function makeDotGridPng(file, w, h) {
  const pitch = Math.round(w / 44);
  const r = Math.max(1, Math.round(pitch / 14));
  let dots = "";
  for (let y = pitch; y < h; y += pitch) {
    for (let x = pitch; x < w; x += pitch) {
      dots += `<circle cx="${x}" cy="${y}" r="${r}" fill="#FFFFFF" opacity="0.07"/>`;
    }
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">${dots}</svg>`;
  await sharp(Buffer.from(svg)).png().toFile(file);
}

async function build() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
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
  const noFill = { color: C.white, transparency: 100 };

  // ---- P1 cover ---------------------------------------------------------------
  const s1 = pres.addSlide();
  s1.background = { color: C.navy };
  s1.addImage({ path: path.join(ASSETS, "dot-grid.png"), x: 0, y: 0, w: 13.333, h: 7.5, altText: "装饰性点阵底纹" });
  s1.addShape(S.ellipse, {
    x: 9.1, y: 0.9, w: 3.7, h: 3.7, fill: noFill, line: { color: C.slate, width: 1.25 },
  });
  s1.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s1.addText("交付示例:一份逐项可查的 PPTX", {
    x: 0.8, y: 2.5, w: 11.7, h: 1.1, fontFace: FONT, fontSize: 40, bold: true, color: C.white, margin: 0,
  });
  s1.addText("生成 → 断言 → 渲染复验 → 验收清单,一步不落", {
    x: 0.8, y: 3.75, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 18, color: C.ice, margin: 0,
  });
  s1.addText("Command Code · pptx-delivery 示例交付包 · v1.1", {
    x: 0.8, y: 6.6, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });

  // ---- P2 executive summary (3 columns) --------------------------------------
  const s2 = pres.addSlide();
  s2.background = { color: C.white };
  title(s2, "验收链已被拆成 9 条可执行断言");
  const cols = [
    ["现状", ["AI 产出快,交付常翻车", "占位、低对比、导出丢字", "问题多在导出后才暴露"]],
    ["做法", ["9 条断言覆盖五类高频缺陷", "负控套件先证明检查会红", "渲染后带 PDF 复检"]],
    ["结果", ["本样张 0 error / 0 flag", "15 页全部通过 C7 / C8", "证据文件随包可复查"]],
  ];
  cols.forEach(([head, items], i) => {
    const x = 0.8 + i * 4.0;
    s2.addShape(S.rect, { x, y: 1.95, w: 1.4, h: 0.06, fill: { color: C.coral } });
    s2.addText(head, {
      x, y: 2.12, w: 3.5, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
    });
    s2.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })), {
      x, y: 2.62, w: 3.5, h: 2.4, fontFace: FONT, fontSize: 13, color: C.ink, paraSpaceAfter: 8, margin: 0,
    });
  });
  anchor(s2, "结构:现状 → 做法 → 结果;每栏三句封顶");

  // ---- P3 big number ----------------------------------------------------------
  const s3 = pres.addSlide();
  s3.background = { color: C.white };
  s3.addShape(S.rect, { x: 0.8, y: 2.15, w: 1.4, h: 0.08, fill: { color: C.coral } });
  s3.addText("0 flag", {
    x: 0.8, y: 2.35, w: 11.7, h: 2.3, fontFace: FONT, fontSize: 140, bold: true, color: C.navy, margin: 0,
  });
  s3.addText("本样张跑完 C1–C9 九项断言:零错误、零警告 —— 有 JSON 可查,不是口头结论。", {
    x: 0.8, y: 4.85, w: 11.0, h: 0.8, fontFace: FONT, fontSize: 20, color: C.ink, margin: 0,
  });
  anchor(s3, "口径:qa_check.py --strict --pdf(15 页全量)");

  // ---- P4 three pillars with geometric icons ---------------------------------
  const s4 = pres.addSlide();
  s4.background = { color: C.white };
  title(s4, "交付级靠三根支柱:断言、渲染、复核");
  const pillars = [
    ["断言", "9 条断言挡住五类高频缺陷", ["对应:tests/ 7 组负控", "产物:qa 报告 .json"]],
    ["渲染", "转图与 PDF,导出后仍保真", ["对应:render_slides.ps1", "产物:PNG + PDF"]],
    ["复核", "外部眼睛 + 校准探针", ["证据:docs/reviews/ 档案", "要求:探针先红后绿"]],
  ];
  pillars.forEach(([name, desc, meta], i) => {
    const x = 0.8 + i * 4.0;
    s4.addShape(S.roundRect, { x, y: 1.95, w: 0.95, h: 0.95, fill: { color: C.navy } });
    if (i === 0) {
      [0.32, 0.5, 0.68].forEach((hh, k) => {
        s4.addShape(S.rect, { x: x + 0.22 + k * 0.18, y: 1.95 + 0.75 - hh, w: 0.1, h: hh, fill: { color: C.white } });
      });
    } else if (i === 1) {
      s4.addShape(S.rect, { x: x + 0.18, y: 2.16, w: 0.44, h: 0.44, fill: { color: C.navy }, line: { color: C.white, width: 1.5 } });
      s4.addShape(S.triangle, { x: x + 0.42, y: 2.34, w: 0.26, h: 0.26, rotate: 90, fill: { color: C.white } });
    } else {
      s4.addShape(S.ellipse, { x: x + 0.18, y: 2.12, w: 0.42, h: 0.42, fill: { color: C.navy }, line: { color: C.white, width: 1.5 } });
      s4.addShape(S.rect, { x: x + 0.54, y: 2.5, w: 0.26, h: 0.07, rotate: 45, fill: { color: C.white } });
    }
    s4.addText(name, {
      x, y: 3.15, w: 3.4, h: 0.45, fontFace: FONT, fontSize: 18, bold: true, color: C.navy, margin: 0,
    });
    s4.addText(desc, {
      x, y: 3.7, w: 3.4, h: 1.0, fontFace: FONT, fontSize: 13, color: C.gray, margin: 0,
    });
    s4.addShape(S.rect, { x, y: 4.3, w: 3.4, h: 0.03, fill: { color: C.border } });
    s4.addText(
      [{ text: meta[0], options: { breakLine: true } }, { text: meta[1] }],
      { x, y: 4.45, w: 3.4, h: 0.9, fontFace: FONT, fontSize: 12, color: C.gray, paraSpaceAfter: 4, margin: 0 }
    );
  });
  anchor(s4, "三根支柱各有验收;缺一根,交付就靠运气");

  // ---- P5 process flow (chevrons) --------------------------------------------
  const s5 = pres.addSlide();
  s5.background = { color: C.white };
  title(s5, "每份 deck 走同一条四步流水线");
  const steps = [
    ["生成", "make_sample.js", "deck.pptx"],
    ["断言", "qa_check --strict", "qa/*.json"],
    ["渲染", "WPS / LO → PNG·PDF", "render/"],
    ["复验", "带 PDF 复跑 + 目检", "复核记录"],
  ];
  steps.forEach(([name, desc, out], i) => {
    const x = 0.8 + i * 2.95;
    s5.addShape(S.chevron, { x, y: 1.95, w: 2.65, h: 0.95, fill: { color: C.navy }, line: { color: C.white, width: 1 } });
    s5.addText(name, {
      x: x + 0.62, y: 2.2, w: 1.7, h: 0.5, fontFace: FONT, fontSize: 16, bold: true, color: C.white, margin: 0,
    });
    s5.addText(desc, {
      x: x + 0.28, y: 3.15, w: 2.2, h: 0.6, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
    s5.addShape(S.roundRect, { x: x + 0.28, y: 3.9, w: 2.05, h: 0.5, fill: { color: C.card } });
    s5.addText(out, {
      x: x + 0.4, y: 3.99, w: 1.85, h: 0.35, fontFace: FONT, fontSize: 12, color: C.ink, margin: 0,
    });
  });
  anchor(s5, "四步固定顺序;跳步 = 返工");

  // ---- P6 timeline (3 layers) -------------------------------------------------
  const s6 = pres.addSlide();
  s6.background = { color: C.white };
  title(s6, "复核从“看一眼”演进到校准探针");
  s6.addShape(S.rect, { x: 1.0, y: 3.42, w: 11.3, h: 0.06, fill: { color: C.border } });
  const phases = [
    ["靠人", "人工目检", "看一眼就走,结论不可复现"],
    ["靠脚本", "机器断言", "9 项可复跑,先红后绿"],
    ["靠外眼", "独立评审", "外部眼睛,不受自评偏差影响"],
    ["靠证据", "校准探针", "评审者先证明自己会红"],
  ];
  phases.forEach(([phase, name, desc], i) => {
    const x = 1.6 + i * 3.0;
    const last = i === phases.length - 1;
    s6.addShape(S.roundRect, { x: x - 0.7, y: 2.3, w: 1.7, h: 0.36, fill: { color: C.light } });
    s6.addText(phase, {
      x: x - 0.7, y: 2.36, w: 1.7, h: 0.28, fontFace: FONT, fontSize: 12, color: C.gray, align: "center", margin: 0,
    });
    if (last) {
      s6.addShape(S.ellipse, { x: x - 0.15, y: 3.3, w: 0.3, h: 0.3, fill: { color: C.coral } });
      s6.addShape(S.rect, { x: x - 0.6, y: 4.7, w: 0.16, h: 0.16, fill: { color: C.coral } });
      s6.addText("当前", {
        x: x - 0.36, y: 4.62, w: 1.2, h: 0.3, fontFace: FONT, fontSize: 12, bold: true, color: C.navy, margin: 0,
      });
    } else {
      s6.addShape(S.ellipse, { x: x - 0.11, y: 3.34, w: 0.22, h: 0.22, fill: { color: C.navy } });
    }
    s6.addText(name, {
      x: x - 0.7, y: 3.75, w: 2.4, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
    });
    s6.addText(desc, {
      x: x - 0.7, y: 4.2, w: 2.4, h: 0.8, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  anchor(s6, "终点高亮:现在站的位置是“证据可复现”");

  // ---- P7 2x2 matrix ----------------------------------------------------------
  const s7 = pres.addSlide();
  s7.background = { color: C.white };
  title(s7, "缺陷按频率 × 伤害落位,先打右上角");
  s7.addShape(S.rect, { x: 6.3, y: 1.95, w: 0.05, h: 3.7, fill: { color: C.border } });
  s7.addShape(S.rect, { x: 1.2, y: 3.78, w: 11.0, h: 0.05, fill: { color: C.border } });
  s7.addText("伤害高", { x: 6.42, y: 1.68, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  s7.addText("伤害低", { x: 6.42, y: 5.78, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  s7.addText("频率低", { x: 0.8, y: 3.9, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  s7.addText("频率高", { x: 11.3, y: 3.9, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  const quads = [
    [2.1, 2.2, C.light, C.ink, "C7 越界 · C8 丢字"],
    [8.3, 2.2, C.navy, C.white, "C5 低对比 · C2 占位"],
    [2.1, 4.3, C.light, C.ink, "C4 颜色破坏"],
    [8.3, 4.3, C.light, C.ink, "C3 小字 · C6 拉伸"],
  ];
  quads.forEach(([x, y, fill, color, t]) => {
    s7.addShape(S.roundRect, { x, y, w: 2.9, h: 0.72, fill: { color: fill } });
    s7.addText(t, {
      x: x + 0.22, y: y + 0.15, w: 2.5, h: 0.42, fontFace: FONT, fontSize: 13, color, margin: 0,
    });
  });
  anchor(s7, "右上优先:高频高伤;左上低频但致命,也要拦");

  // ---- P8 dashboard -----------------------------------------------------------
  const s8 = pres.addSlide();
  s8.background = { color: C.white };
  title(s8, "五个指标里只有一个还需要盯");
  const kpis = [
    ["E2E flags", "0", false],
    ["C7 夹具", "缺 1", true],
    ["C5 检查点", "137", false],
    ["负控命中", "7/7", false],
    ["自动断言", "9 项", false],
  ];
  kpis.forEach(([label, value, hot], i) => {
    const x = 0.8 + i * 2.3;
    s8.addShape(S.roundRect, {
      x, y: 1.95, w: 2.1, h: 1.75, fill: { color: C.white },
      line: { color: hot ? C.coral : C.border, width: hot ? 1.75 : 1 },
    });
    if (hot) s8.addShape(S.ellipse, { x: x + 1.82, y: 2.08, w: 0.14, h: 0.14, fill: { color: C.coral } });
    s8.addText(label, {
      x: x + 0.18, y: 2.1, w: 1.7, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
    s8.addText(value, {
      x: x + 0.18, y: 2.42, w: 1.9, h: 0.6, fontFace: FONT, fontSize: 26, bold: true, color: C.navy, margin: 0,
    });
    [0.12, 0.22, 0.17, 0.3].forEach((hh, k) => {
      s8.addShape(S.rect, {
        x: x + 0.18 + k * 0.24, y: 3.5 - hh, w: 0.12, h: hh,
        fill: { color: hot ? C.coral : C.navy },
      });
    });
  });
  const panel = (x, w, heading, items) => {
    s8.addShape(S.roundRect, { x, y: 4.05, w, h: 1.9, fill: { color: C.light } });
    s8.addText(heading, {
      x: x + 0.3, y: 4.2, w: w - 0.6, h: 0.35, fontFace: FONT, fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s8.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })), {
      x: x + 0.3, y: 4.62, w: w - 0.6, h: 1.2, fontFace: FONT, fontSize: 12.5, color: C.ink, paraSpaceAfter: 6, margin: 0,
    });
  };
  panel(0.8, 5.7, "本轮完成", ["15 页样张重建 + 两层断言 0/0", "C5 叠层解析修复并自测锁定"]);
  panel(6.7, 5.85, "下一步", ["补 C7 触发夹具(需换渲染器环境)", "拿真实 deck 走一遍全流程"]);
  anchor(s8, "红色贴片是邀请:这一项要不要现在补?");

  // ---- P9 two-column comparison ----------------------------------------------
  const s9 = pres.addSlide();
  s9.background = { color: C.white };
  title(s9, "清单把“靠感觉”换成“逐项勾”");
  const panel2 = (x, fill, heading, headingColor, items, markColor) => {
    s9.addShape(S.roundRect, { x, y: 1.9, w: 5.8, h: 4.0, fill: { color: fill } });
    s9.addText(heading, {
      x: x + 0.35, y: 2.1, w: 5.1, h: 0.45, fontFace: FONT, fontSize: 16, bold: true, color: headingColor, margin: 0,
    });
    items.forEach((t, i) => {
      const y = 2.75 + i * 0.62;
      s9.addShape(S.rect, { x: x + 0.38, y: y + 0.1, w: 0.14, h: 0.14, fill: { color: markColor } });
      s9.addText(t, {
        x: x + 0.66, y, w: 4.9, h: 0.4, fontFace: FONT, fontSize: 13, color: C.ink, margin: 0,
      });
    });
  };
  panel2(0.8, C.light, "旧做法:靠感觉", C.gray, [
    "看起来差不多就交付",
    "导出丢字,交付后才发现",
    "每份 deck 各写各的样式",
    "返工靠人肉复看",
  ], C.coral);
  panel2(6.73, C.card, "本技能:按清单", C.navy, [
    "逐项断言,零 flag 才放行",
    "C7 / C8 盯导出保真",
    "角色色与锚线有约定",
    "复核档案可回溯",
  ], C.navy);
  anchor(s9, "差别不在工具,在“每项都有人签过字”");

  // ---- P10 scorecard (table with meters) --------------------------------------
  const s10 = pres.addSlide();
  s10.background = { color: C.white };
  title(s10, "九项断言记分卡:八项满分,一项欠夹具");
  const head = (t) => ({
    text: t,
    options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: FONT },
  });
  const meter = (n) => ({
    text: [
      { text: "●".repeat(n), options: { color: C.navy, fontSize: 12, fontFace: FONT } },
      { text: "○".repeat(3 - n), options: { color: C.gray, fontSize: 12, fontFace: FONT } },
    ],
  });
  const row = (name, n, note) => [
    { text: name, options: { fill: { color: C.white }, color: C.ink, fontSize: 12, fontFace: FONT } },
    { ...meter(n), options: { fill: { color: C.white }, align: "center" } },
    { text: note, options: { fill: { color: C.white }, color: C.ink, fontSize: 12, fontFace: FONT } },
  ];
  s10.addTable(
    [
      [head("断言"), head("记分"), head("说明")],
      row("C1 结构", 3, "页数 / 媒体清点"),
      row("C2 占位", 3, "模板残留扫描"),
      row("C3 字号", 3, "10pt 硬下限"),
      row("C4 颜色", 3, "非法 hex / 负影"),
      row("C5 对比", 3, "4.5:1 / 3:1,137 处"),
      row("C6 比例", 3, "形变 ≤ 2%"),
      row("C7 越界", 1, "无触发夹具(防御性检查)"),
      row("C8 保真", 3, "导出不丢字"),
      row("C9 编辑", 3, "整页图预警"),
    ],
    {
      x: 0.8, y: 1.9, w: 11.7, colW: [3.4, 2.2, 6.1], rowH: 0.4,
      valign: "middle", border: { pt: 1, color: C.border },
    }
  );
  anchor(s10, "记分卡给粗颗粒:三档足够,别做假精度");

  // ---- P11 quote + evidence (dark) -------------------------------------------
  const s11 = pres.addSlide();
  s11.background = { color: C.navy };
  s11.addText("“", {
    x: 0.75, y: 1.5, w: 2.0, h: 1.6, fontFace: FONT, fontSize: 120, bold: true, color: C.ice, margin: 0,
  });
  s11.addText("检查不是最后一步,\n是每一步。", {
    x: 0.8, y: 2.55, w: 8.0, h: 1.7, fontFace: FONT, fontSize: 32, bold: true, color: C.white, lineSpacing: 44, margin: 0,
  });
  s11.addText("— pptx-delivery 设计原则", {
    x: 0.8, y: 4.45, w: 6.0, h: 0.4, fontFace: FONT, fontSize: 13, color: C.ice, margin: 0,
  });
  s11.addShape(S.rect, { x: 9.3, y: 2.35, w: 0.06, h: 2.6, fill: { color: C.slate } });
  s11.addText("137", {
    x: 9.6, y: 2.3, w: 2.8, h: 0.7, fontFace: FONT, fontSize: 30, bold: true, color: C.ice, margin: 0,
  });
  s11.addText("处对比度检查,全部通过", {
    x: 9.6, y: 3.0, w: 2.8, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s11.addText("9/9", {
    x: 9.6, y: 3.75, w: 2.8, h: 0.7, fontFace: FONT, fontSize: 30, bold: true, color: C.ice, margin: 0,
  });
  s11.addText("断言通过;7/7 负控命中", {
    x: 9.6, y: 4.45, w: 2.8, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s11.addText("pptx-delivery · examples/acceptance-sample", {
    x: 0.8, y: 6.6, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });

  // ---- P12 chart + insight callout --------------------------------------------
  const s12 = pres.addSlide();
  s12.background = { color: C.white };
  title(s12, "首轮命中集中在对比度与导出保真");
  s12.addImage({ path: path.join(ASSETS, "chart-bars.png"), x: 0.8, y: 1.95, w: 6.4, h: 3.2, altText: "柱状图示意:各检查项首轮命中数" });
  s12.addShape(S.ellipse, {
    x: 1.18, y: 2.36, w: 0.95, h: 0.5, fill: noFill, line: { color: C.coral, width: 2 },
  });
  s12.addText("首轮最高", {
    x: 2.24, y: 2.44, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.navy, margin: 0,
  });
  s12.addShape(S.roundRect, { x: 7.6, y: 1.95, w: 4.9, h: 2.6, fill: { color: C.light } });
  s12.addShape(S.rect, { x: 7.6, y: 1.95, w: 0.07, h: 2.6, fill: { color: C.coral } });
  s12.addText("解读", {
    x: 7.92, y: 2.12, w: 4.3, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
  });
  s12.addText("对比度与导出保真占首轮命中的一半以上;其余是占位与小字。", {
    x: 7.92, y: 2.55, w: 4.3, h: 1.6, fontFace: FONT, fontSize: 14, color: C.ink, lineSpacing: 22, margin: 0,
  });
  s12.addText("示意数据:各检查项首轮命中构成", {
    x: 0.8, y: 5.5, w: 6.4, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
  });
  anchor(s12, "图只负责证明;解读必须给结论");

  // ---- P13 terminal block -----------------------------------------------------
  const s13 = pres.addSlide();
  s13.background = { color: C.light };
  title(s13, "四条命令,顺序固定");
  s13.addShape(S.roundRect, { x: 0.8, y: 1.85, w: 7.5, h: 4.1, fill: { color: C.navy } });
  [C.gray, C.border, C.ice].forEach((dot, k) => {
    s13.addShape(S.ellipse, { x: 1.1 + k * 0.22, y: 2.03, w: 0.12, h: 0.12, fill: { color: dot } });
  });
  s13.addText("PowerShell · 项目根目录", {
    x: 1.8, y: 1.96, w: 5.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s13.addText(
    [
      { text: "$ node make_sample.js", options: { breakLine: true } },
      { text: "$ python scripts/normalize_pptx_order.py inplace deck.pptx", options: { breakLine: true } },
      { text: "$ python scripts/qa_check.py deck.pptx --pdf render/deck.pdf --strict", options: { breakLine: true } },
      { text: "$ scripts/render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf" },
    ],
    {
      x: 1.15, y: 2.6, w: 7.0, h: 2.9, fontFace: MONO, fontSize: 13,
      color: C.white, paraSpaceAfter: 12, margin: 0,
    }
  );
  s13.addText(
    [
      { text: "先归一化,再断言——顺序别乱", options: { bullet: true, breakLine: true } },
      { text: "带 PDF 才覆盖 C7 / C8", options: { bullet: true, breakLine: true } },
      { text: "零 flag 才进入渲染目检", options: { bullet: true } },
    ],
    { x: 8.7, y: 2.2, w: 3.9, h: 2.8, fontFace: FONT, fontSize: 14, color: C.ink, paraSpaceAfter: 10, margin: 0 }
  );
  anchor(s13, "四条命令的顺序 = 依赖关系");

  // ---- P14 palette ------------------------------------------------------------
  const s14 = pres.addSlide();
  s14.background = { color: C.white };
  title(s14, "一套颜色,三个角色");
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
    s14.addShape(S.rect, { x, y: 1.9, w: 1.65, h: 1.1, fill: { color: fill }, line: { color: C.border, width: 1 } });
    s14.addText(hex, {
      x, y: 3.08, w: 1.65, h: 0.3, fontFace: MONO, fontSize: 12, color: C.ink, margin: 0,
    });
    s14.addText(role, {
      x, y: 3.4, w: 1.65, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  s14.addText(
    [
      { text: "白字只做大字:珊瑚底白字 3.64:1,仅 ≥18pt 或 ≥14pt 粗", options: { bullet: true, breakLine: true } },
      { text: "两档灰(222222 / 5F6B7C)对三种浅底均 ≥ 4.5:1", options: { bullet: true, breakLine: true } },
      { text: "数值口径:WCAG 2.1,不四舍五入(qa_check C5 实测)", options: { bullet: true } },
    ],
    { x: 0.8, y: 4.15, w: 11.7, h: 1.6, fontFace: FONT, fontSize: 13, color: C.ink, paraSpaceAfter: 8, margin: 0 }
  );
  anchor(s14, "角色分工见 typography.md;本页是它的可视版");

  // ---- P15 closing ------------------------------------------------------------
  const s15 = pres.addSlide();
  s15.background = { color: C.navy };
  s15.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s15.addText("拿它当模板,或直接照流程走", {
    x: 0.8, y: 2.5, w: 11.7, h: 0.9, fontFace: FONT, fontSize: 36, bold: true, color: C.white, margin: 0,
  });
  s15.addText(
    [
      { text: "本包 = deck + 渲染图 + QA 证据 + 检查指引", options: { bullet: true, breakLine: true } },
      { text: "改内容重生成:node make_sample.js", options: { bullet: true, breakLine: true } },
      { text: "全量复跑:python tests/run_tests.py", options: { bullet: true } },
    ],
    { x: 0.8, y: 3.6, w: 11.7, h: 2.2, fontFace: FONT, fontSize: 16, color: C.ice, paraSpaceAfter: 8 }
  );
  s15.addText("pptx-delivery · examples/acceptance-sample", {
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
    { frac: 0.62, color: C.slate },
    { frac: 0.45, color: "6C7BBF" },
    { frac: 0.28, color: "AAB6E8" },
  ]);
  await makeDotGridPng(path.join(ASSETS, "dot-grid.png"), 1600, 900);
  await build();
  console.log("acceptance sample done -> " + HERE);
})().catch((e) => {
  console.error("FAIL:", e);
  process.exit(1);
});
