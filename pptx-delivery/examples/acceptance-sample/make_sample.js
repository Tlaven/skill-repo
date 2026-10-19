"use strict";
// acceptance-sample: 参考示例交付包的本体生成脚本(13 页,信息图 / 咨询 exhibit 式密度;
// 判据见 docs/scaffolds/slide-patterns-essentials.md v0.1:每页 ≥3 模块同时在场)。
// 约定与 tests/make_e2e_deck.js 同源(角色色 / 底锚线 / 标题对齐),但本文件 standalone——
// 只依赖全局 pptxgenjs + sharp,复制到任何项目可直接改内容使用。
//
// Run:  set NODE_PATH to `npm root -g`, then:  node make_sample.js
// Out:  deck.pptx + assets/chart-bars.png + assets/donut.png + assets/dot-grid.png

const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const HERE = __dirname;
const ASSETS = path.join(HERE, "assets");
const MONO = "Consolas";
const TOTAL = 13;

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

async function makeDonutPng(file, size, segs) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.38;
  const sw = size * 0.2;
  const circ = 2 * Math.PI * r;
  let off = 0;
  let arcs = "";
  for (const s of segs) {
    const len = circ * s.frac;
    arcs +=
      `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#${s.color}" stroke-width="${sw}" ` +
      `stroke-dasharray="${len} ${circ - len}" stroke-dashoffset="${-off}" ` +
      `transform="rotate(-90 ${cx} ${cy})"/>`;
    off += len;
  }
  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">` +
    `<rect width="${size}" height="${size}" fill="#FFFFFF"/>${arcs}</svg>`;
  await sharp(Buffer.from(svg)).png().toFile(file);
}

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
  const noFill = { color: C.white, transparency: 100 };

  const section = (s, t, color = C.gray) =>
    s.addText(t, { x: 0.8, y: 0.28, w: 6.0, h: 0.26, fontFace: FONT, fontSize: 12, color, margin: 0 });
  const pageNum = (s, n, color = C.gray) =>
    s.addText(`${String(n).padStart(2, "0")} / ${TOTAL}`, {
      x: 10.9, y: 6.25, w: 1.6, h: 0.4, fontFace: FONT, fontSize: 12, color, align: "right", margin: 0,
    });
  const title = (s, t) =>
    s.addText(t, {
      x: 0.8, y: 0.55, w: 11.7, h: 0.7, fontFace: FONT, fontSize: 28, bold: true, color: C.navy, margin: 0,
    });
  const anchor = (s, t) =>
    s.addText(t, {
      x: 0.8, y: 6.25, w: 9.9, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  const chip = (s, x, y, w, t, fill = C.light, color = C.ink, h = 0.42) => {
    s.addShape(S.roundRect, { x, y, w, h, fill: { color: fill } });
    s.addText(t, {
      x: x + 0.16, y: y + (h - 0.3) / 2, w: w - 0.3, h: 0.3, fontFace: FONT, fontSize: 12, color, margin: 0,
    });
  };

  // ---- P1 cover ---------------------------------------------------------------
  const s1 = pres.addSlide();
  s1.background = { color: C.navy };
  s1.addImage({ path: path.join(ASSETS, "dot-grid.png"), x: 0, y: 0, w: 13.333, h: 7.5, altText: "装饰性点阵底纹" });
  s1.addShape(S.ellipse, {
    x: 9.1, y: 0.9, w: 3.7, h: 3.7, fill: noFill, line: { color: C.slate, width: 1.25 },
  });
  s1.addText("v1.2 · 2026-10", {
    x: 9.9, y: 0.35, w: 2.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.ice, align: "right", margin: 0,
  });
  s1.addShape(S.rect, { x: 0.8, y: 2.0, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s1.addText("交付示例:一份逐项可查的 PPTX", {
    x: 0.8, y: 2.5, w: 11.7, h: 1.1, fontFace: FONT, fontSize: 40, bold: true, color: C.white, margin: 0,
  });
  s1.addText("生成 → 断言 → 渲染复验 → 验收清单,一步不落", {
    x: 0.8, y: 3.75, w: 11.7, h: 0.6, fontFace: FONT, fontSize: 18, color: C.ice, margin: 0,
  });
  ["13 页 · 信息图式密度", "12 种版式原型", "0 flag · 有据可查"].forEach((t, i) => {
    chip(s1, 0.8 + i * 2.6, 5.05, 2.45, t, C.slate, C.ice, 0.46);
  });
  s1.addText("Command Code · pptx-delivery 示例交付包", {
    x: 0.8, y: 6.6, w: 9.9, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });

  // ---- P2 executive summary + stat band --------------------------------------
  const s2 = pres.addSlide();
  s2.background = { color: C.white };
  section(s2, "01 · 总览");
  title(s2, "验收链已被拆成 9 条可执行断言");
  const cols = [
    ["现状", ["AI 产出快,交付常翻车", "占位、低对比、导出丢字", "问题多在导出后才暴露"]],
    ["做法", ["9 条断言覆盖五类高频缺陷", "负控套件先证明检查会红", "渲染后带 PDF 复检"]],
    ["结果", ["本样张 0 error / 0 flag", "13 页全部通过 C7 / C8", "证据文件随包可复查"]],
  ];
  cols.forEach(([head, items], i) => {
    const x = 0.8 + i * 4.0;
    s2.addShape(S.rect, { x, y: 1.9, w: 1.3, h: 0.05, fill: { color: C.coral } });
    s2.addText(head, {
      x, y: 2.05, w: 3.5, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
    });
    s2.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })), {
      x, y: 2.5, w: 3.5, h: 1.4, fontFace: FONT, fontSize: 13, color: C.ink, paraSpaceAfter: 6, margin: 0,
    });
  });
  s2.addShape(S.roundRect, { x: 0.8, y: 3.95, w: 11.7, h: 1.85, fill: { color: C.light } });
  [
    ["9 条", "自动断言(C1–C9)"],
    ["7 组", "必红负控 + 干净基线"],
    ["291 处", "对比度检查,全部通过"],
    ["0", "error 与 flag(本样张)"],
  ].forEach(([num, label], i) => {
    const x = 1.15 + i * 2.9;
    s2.addShape(S.rect, { x, y: 4.15, w: 0.18, h: 0.18, fill: { color: C.coral } });
    s2.addText(num, {
      x, y: 4.42, w: 2.6, h: 0.55, fontFace: FONT, fontSize: 24, bold: true, color: C.navy, margin: 0,
    });
    s2.addText(label, {
      x, y: 5.0, w: 2.6, h: 0.6, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  anchor(s2, "结构:现状 → 做法 → 结果;底部为数字速览");
  pageNum(s2, 2);

  // ---- P3 checks panorama + threshold panel -----------------------------------
  const s3 = pres.addSlide();
  s3.background = { color: C.white };
  section(s3, "02 · 断言");
  title(s3, "九项断言,各有其责");
  const checks = [
    ["C1", "结构", "页数 / 媒体清点"],
    ["C2", "占位", "模板残留扫描"],
    ["C3", "字号", "10pt 硬下限"],
    ["C4", "颜色", "非法 hex / 负影"],
    ["C5", "对比", "4.5:1 / 3:1 阈值"],
    ["C6", "比例", "形变 ≤ 2%"],
    ["C7", "越界", "跨缘词框"],
    ["C8", "保真", "导出不丢字"],
    ["C9", "编辑", "整页图预警"],
  ];
  checks.forEach(([id, name, desc], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.8 + col * 3.05;
    const y = 1.9 + row * 1.28;
    s3.addShape(S.roundRect, { x, y, w: 2.9, h: 1.15, fill: { color: C.card } });
    s3.addText(id, {
      shape: S.rect, x: x + 0.14, y: y + 0.14, w: 0.5, h: 0.5, fill: { color: C.navy },
      fontFace: FONT, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s3.addText(name, {
      x: x + 0.74, y: y + 0.16, w: 1.9, h: 0.4, fontFace: FONT, fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s3.addText(desc, {
      x: x + 0.14, y: y + 0.7, w: 2.6, h: 0.35, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  s3.addText("阈值与来源", {
    x: 10.15, y: 1.9, w: 2.4, h: 0.35, fontFace: FONT, fontSize: 13, bold: true, color: C.navy, margin: 0,
  });
  [
    ["4.5:1 / 3:1", "对比度阈值(WCAG 2.1)"],
    ["10pt", "字号下限(自定)"],
    ["≤ 2%", "图片形变(实测容差)"],
    ["80%", "整页图预警(假设待测)"],
  ].forEach(([val, label], i) => {
    const y = 2.35 + i * 0.82;
    s3.addShape(S.rect, { x: 10.15, y: y - 0.06, w: 2.35, h: 0.02, fill: { color: C.border } });
    s3.addText(val, {
      x: 10.15, y, w: 2.35, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: C.navy, margin: 0,
    });
    s3.addText(label, {
      x: 10.15, y: y + 0.3, w: 2.35, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  anchor(s3, "九项 = 五类高频缺陷 + 四类破坏项;阈值可在上限内收紧");
  pageNum(s3, 3);

  // ---- P4 process + table -----------------------------------------------------
  const s4 = pres.addSlide();
  s4.background = { color: C.white };
  section(s4, "03 · 流水线");
  title(s4, "每份 deck 走同一条四步流水线");
  const steps = [
    ["生成", "make_sample.js 产出 pptx", "deck.pptx"],
    ["断言", "qa_check --strict", "qa/*.json"],
    ["渲染", "WPS / LO → PNG·PDF", "render/"],
    ["复验", "带 PDF 复跑 + 目检", "复核记录"],
  ];
  steps.forEach(([name, desc, out], i) => {
    const x = 0.8 + i * 2.95;
    s4.addShape(S.chevron, { x, y: 1.85, w: 2.55, h: 0.8, fill: { color: C.navy }, line: { color: C.white, width: 1 } });
    s4.addText(name, {
      x: x + 0.6, y: 2.05, w: 1.6, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: C.white, margin: 0,
    });
    s4.addText(desc, {
      x: x + 0.28, y: 2.82, w: 2.2, h: 0.5, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
    chip(s4, x + 0.28, 3.35, 2.15, out, C.card, C.ink, 0.4);
  });
  const hcell = (t) => ({
    text: t,
    options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: FONT },
  });
  const dcell = (t) => ({
    text: t,
    options: { fill: { color: C.white }, color: C.ink, fontSize: 12, fontFace: FONT },
  });
  s4.addTable(
    [
      [hcell("步"), hcell("命令"), hcell("失败时")],
      [dcell("生成"), dcell("node make_sample.js"), dcell("报错即停")],
      [dcell("断言"), dcell("qa_check.py --strict"), dcell("修到 0 flag")],
      [dcell("渲染"), dcell("render_slides.ps1 -Pdf"), dcell("PNG 必须齐全")],
      [dcell("复验"), dcell("qa --pdf + 目检"), dcell("有 flag 重来")],
    ],
    { x: 0.8, y: 4.0, w: 11.7, colW: [2.0, 5.9, 3.8], rowH: 0.34, valign: "middle", border: { pt: 1, color: C.border } }
  );
  anchor(s4, "四步固定顺序;跳步 = 返工");
  pageNum(s4, 4);

  // ---- P5 timeline with tag layer --------------------------------------------
  const s5 = pres.addSlide();
  s5.background = { color: C.white };
  section(s5, "04 · 复核");
  title(s5, "复核从“看一眼”演进到校准探针");
  s5.addShape(S.rect, { x: 1.0, y: 3.42, w: 11.3, h: 0.06, fill: { color: C.border } });
  const phases = [
    ["靠人", "人工目检", "看一眼就走,结论不可复现", "不可复现", false],
    ["靠脚本", "机器断言", "9 项可复跑,先红后绿", "先红后绿", false],
    ["靠外眼", "独立评审", "外部眼睛,不受自评偏差影响", "抽样偏差", false],
    ["靠证据", "校准探针", "评审者先证明自己会红", "当前 · 探针 2/2", true],
  ];
  phases.forEach(([phase, name, desc, tag, hot], i) => {
    const x = 1.6 + i * 3.0;
    s5.addShape(S.roundRect, { x: x - 0.7, y: 2.25, w: 1.7, h: 0.34, fill: { color: C.light } });
    s5.addText(phase, {
      x: x - 0.7, y: 2.3, w: 1.7, h: 0.26, fontFace: FONT, fontSize: 12, color: C.gray, align: "center", margin: 0,
    });
    if (hot) {
      s5.addShape(S.ellipse, { x: x - 0.15, y: 3.3, w: 0.3, h: 0.3, fill: { color: C.coral } });
    } else {
      s5.addShape(S.ellipse, { x: x - 0.11, y: 3.34, w: 0.22, h: 0.22, fill: { color: C.navy } });
    }
    s5.addText(name, {
      x: x - 0.7, y: 3.7, w: 2.4, h: 0.4, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
    });
    s5.addText(desc, {
      x: x - 0.7, y: 4.12, w: 2.4, h: 0.7, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
    chip(s5, x - 0.7, 5.0, 1.9, tag, hot ? C.navy : C.light, hot ? C.ice : C.gray, 0.36);
  });
  anchor(s5, "终点高亮:现在站的位置是“证据可复现”");
  pageNum(s5, 5);

  // ---- P6 dashboard: donut + legend + KPI tiles + band -----------------------
  const s6 = pres.addSlide();
  s6.background = { color: C.white };
  section(s6, "05 · 数据");
  title(s6, "六个指标里只有一个还需要盯");
  s6.addImage({ path: path.join(ASSETS, "donut.png"), x: 0.8, y: 1.9, w: 2.9, h: 2.9, altText: "环形图示意:首轮命中构成" });
  s6.addText("首轮命中构成(示意)", {
    x: 0.8, y: 4.88, w: 2.9, h: 0.35, fontFace: FONT, fontSize: 12, color: C.gray, align: "center", margin: 0,
  });
  [
    [C.navy, "C5 对比度 42%"],
    [C.slate, "C8 保真 25%"],
    ["6C7BBF", "C3 字号 18%"],
    ["AAB6E8", "其他 15%"],
  ].forEach(([color, label], i) => {
    const y = 2.05 + i * 0.42;
    s6.addShape(S.rect, { x: 3.95, y: y + 0.06, w: 0.14, h: 0.14, fill: { color } });
    s6.addText(label, {
      x: 4.2, y, w: 2.0, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  const kpis = [
    ["断言", "9 项", false],
    ["负控", "7/7", false],
    ["对比度", "291 处", false],
    ["页面", "13 页", false],
    ["C7 夹具", "缺 1", true],
    ["E2E flags", "0", false],
  ];
  kpis.forEach(([label, value, hot], i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 6.4 + col * 2.05;
    const y = 1.9 + row * 1.4;
    s6.addShape(S.roundRect, {
      x, y, w: 1.95, h: 1.3, fill: { color: C.white },
      line: { color: hot ? C.coral : C.border, width: hot ? 1.75 : 1 },
    });
    if (hot) s6.addShape(S.ellipse, { x: x + 1.68, y: y + 0.12, w: 0.13, h: 0.13, fill: { color: C.coral } });
    s6.addText(label, {
      x: x + 0.16, y: y + 0.12, w: 1.5, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
    s6.addText(value, {
      x: x + 0.16, y: y + 0.44, w: 1.7, h: 0.55, fontFace: FONT, fontSize: 20, bold: true, color: C.navy, margin: 0,
    });
    [0.1, 0.18, 0.14, 0.24].forEach((hh, k) => {
      s6.addShape(S.rect, {
        x: x + 0.16 + k * 0.2, y: y + 1.12 - hh, w: 0.1, h: hh,
        fill: { color: hot ? C.coral : C.navy },
      });
    });
  });
  s6.addShape(S.roundRect, { x: 0.8, y: 4.95, w: 11.7, h: 1.15, fill: { color: C.light } });
  s6.addText("本轮完成", {
    x: 1.1, y: 5.05, w: 5.2, h: 0.3, fontFace: FONT, fontSize: 12, bold: true, color: C.navy, margin: 0,
  });
  s6.addText(
    [
      { text: "C5 叠层解析修复 + 自测锁定", options: { bullet: true, breakLine: true } },
      { text: "示例重做:13 页 · 每页 3+ 模块", options: { bullet: true } },
    ],
    { x: 1.1, y: 5.38, w: 5.2, h: 0.65, fontFace: FONT, fontSize: 12, color: C.ink, paraSpaceAfter: 3, margin: 0 }
  );
  s6.addText("下一步", {
    x: 6.9, y: 5.05, w: 5.4, h: 0.3, fontFace: FONT, fontSize: 12, bold: true, color: C.navy, margin: 0,
  });
  s6.addText(
    [
      { text: "补 C7 触发夹具(需换渲染器)", options: { bullet: true, breakLine: true } },
      { text: "拿真实 deck 走一遍全流程", options: { bullet: true } },
    ],
    { x: 6.9, y: 5.38, w: 5.4, h: 0.65, fontFace: FONT, fontSize: 12, color: C.ink, paraSpaceAfter: 3, margin: 0 }
  );
  anchor(s6, "红色贴片是邀请:这一项要不要现在补?");
  pageNum(s6, 6);

  // ---- P7 2x2 matrix + captions ----------------------------------------------
  const s7 = pres.addSlide();
  s7.background = { color: C.white };
  section(s7, "06 · 处置");
  title(s7, "缺陷按频率 × 伤害落位,先打右上角");
  s7.addShape(S.rect, { x: 6.3, y: 1.9, w: 0.05, h: 3.75, fill: { color: C.border } });
  s7.addShape(S.rect, { x: 1.2, y: 3.74, w: 11.0, h: 0.05, fill: { color: C.border } });
  s7.addText("伤害高", { x: 6.42, y: 1.62, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  s7.addText("伤害低", { x: 6.42, y: 5.72, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  s7.addText("频率低", { x: 0.8, y: 3.86, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  s7.addText("频率高", { x: 11.3, y: 3.86, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0 });
  const quads = [
    [2.1, 2.1, C.light, C.ink, "C7 越界 · C8 丢字", "低频但致命:拦住一次算一次"],
    [8.3, 2.1, C.navy, C.white, "C5 低对比 · C2 占位", "高频高伤:每份 deck 都会踩"],
    [2.1, 4.2, C.light, C.ink, "C4 颜色破坏", "低频低伤:顺手修"],
    [8.3, 4.2, C.light, C.ink, "C3 小字 · C6 拉伸", "高频低伤:批量修"],
  ];
  quads.forEach(([x, y, fill, color, t, cap]) => {
    s7.addShape(S.roundRect, { x, y, w: 2.9, h: 0.66, fill: { color: fill } });
    s7.addText(t, {
      x: x + 0.22, y: y + 0.12, w: 2.5, h: 0.42, fontFace: FONT, fontSize: 13, color, margin: 0,
    });
    s7.addText(cap, {
      x, y: y + 0.78, w: 2.9, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  anchor(s7, "右上优先;左上低频但致命,也要拦");
  pageNum(s7, 7);

  // ---- P8 comparison + VS + evidence strip -----------------------------------
  const s8 = pres.addSlide();
  s8.background = { color: C.white };
  section(s8, "07 · 方法");
  title(s8, "清单把“靠感觉”换成“逐项勾”");
  const panel2 = (x, fill, heading, headingColor, items, markColor) => {
    s8.addShape(S.roundRect, { x, y: 1.85, w: 5.8, h: 3.45, fill: { color: fill } });
    s8.addText(heading, {
      x: x + 0.35, y: 2.02, w: 5.1, h: 0.45, fontFace: FONT, fontSize: 16, bold: true, color: headingColor, margin: 0,
    });
    items.forEach((t, i) => {
      const y = 2.65 + i * 0.56;
      s8.addShape(S.rect, { x: x + 0.38, y: y + 0.09, w: 0.14, h: 0.14, fill: { color: markColor } });
      s8.addText(t, {
        x: x + 0.66, y, w: 4.9, h: 0.38, fontFace: FONT, fontSize: 13, color: C.ink, margin: 0,
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
  s8.addText("VS", {
    shape: S.ellipse, x: 6.33, y: 3.22, w: 0.66, h: 0.66, fill: { color: C.navy },
    fontFace: FONT, fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
  });
  [
    ["291 处", "对比度全过"],
    ["9/9", "断言通过"],
    ["7/7", "负控命中"],
    ["2/2", "校准探针命中"],
  ].forEach(([num, label], i) => {
    const x = 0.8 + i * 3.1;
    s8.addText(num, {
      x, y: 5.45, w: 1.5, h: 0.4, fontFace: FONT, fontSize: 18, bold: true, color: C.navy, margin: 0,
    });
    s8.addText(label, {
      x: x + 1.5, y: 5.52, w: 1.5, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  anchor(s8, "差别不在工具,在“每项都有人签过字”");
  pageNum(s8, 8);

  // ---- P9 scorecard -----------------------------------------------------------
  const s9 = pres.addSlide();
  s9.background = { color: C.white };
  section(s9, "08 · 证据");
  title(s9, "九项断言记分卡:八项满分,一项欠夹具");
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
  s9.addTable(
    [
      [head("断言"), head("记分"), head("说明")],
      row("C1 结构", 3, "页数 / 媒体清点"),
      row("C2 占位", 3, "模板残留扫描"),
      row("C3 字号", 3, "10pt 硬下限"),
      row("C4 颜色", 3, "非法 hex / 负影"),
      row("C5 对比", 3, "4.5:1 / 3:1,291 处"),
      row("C6 比例", 3, "形变 ≤ 2%"),
      row("C7 越界", 1, "无触发夹具(防御性检查)"),
      row("C8 保真", 3, "导出不丢字"),
      row("C9 编辑", 3, "整页图预警"),
    ],
    { x: 0.8, y: 1.85, w: 11.7, colW: [3.0, 2.0, 6.7], rowH: 0.38, valign: "middle", border: { pt: 1, color: C.border } }
  );
  anchor(s9, "口径:三档记分;C7 缺夹具已在验收清单 §5 如实标注");
  pageNum(s9, 9);

  // ---- P10 quote + evidence (dark) -------------------------------------------
  const s10 = pres.addSlide();
  s10.background = { color: C.navy };
  section(s10, "09 · 原则", C.ice);
  s10.addText("“", {
    x: 0.75, y: 1.35, w: 2.0, h: 1.6, fontFace: FONT, fontSize: 120, bold: true, color: C.ice, margin: 0,
  });
  s10.addText("检查不是最后一步,\n是每一步。", {
    x: 0.8, y: 2.45, w: 8.0, h: 1.7, fontFace: FONT, fontSize: 32, bold: true, color: C.white, lineSpacing: 44, margin: 0,
  });
  s10.addText("— pptx-delivery 设计原则", {
    x: 0.8, y: 4.35, w: 6.0, h: 0.4, fontFace: FONT, fontSize: 13, color: C.ice, margin: 0,
  });
  s10.addShape(S.rect, { x: 9.3, y: 2.35, w: 0.06, h: 2.6, fill: { color: C.slate } });
  s10.addText("291", {
    x: 9.6, y: 2.3, w: 2.8, h: 0.7, fontFace: FONT, fontSize: 30, bold: true, color: C.ice, margin: 0,
  });
  s10.addText("处对比度检查,全部通过", {
    x: 9.6, y: 3.0, w: 2.8, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s10.addText("9/9", {
    x: 9.6, y: 3.75, w: 2.8, h: 0.7, fontFace: FONT, fontSize: 30, bold: true, color: C.ice, margin: 0,
  });
  s10.addText("断言通过;7/7 负控命中", {
    x: 9.6, y: 4.45, w: 2.8, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s10.addText("来源:qa/deck-pdf.json · docs/reviews/ · 13 页全量", {
    x: 0.8, y: 5.35, w: 9.9, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s10.addText("pptx-delivery · examples/acceptance-sample", {
    x: 0.8, y: 6.6, w: 9.9, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  pageNum(s10, 10, C.ice);

  // ---- P11 terminal + product chips ------------------------------------------
  const s11 = pres.addSlide();
  s11.background = { color: C.light };
  section(s11, "10 · 运行");
  title(s11, "五条命令,顺序固定");
  s11.addShape(S.roundRect, { x: 0.8, y: 1.8, w: 7.5, h: 3.55, fill: { color: C.navy } });
  [C.gray, C.border, C.ice].forEach((dot, k) => {
    s11.addShape(S.ellipse, { x: 1.1 + k * 0.22, y: 1.98, w: 0.12, h: 0.12, fill: { color: dot } });
  });
  s11.addText("PowerShell · 项目根目录", {
    x: 1.8, y: 1.91, w: 5.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  s11.addText(
    [
      { text: "$ node make_sample.js", options: { breakLine: true } },
      { text: "$ python scripts/normalize_pptx_order.py inplace deck.pptx", options: { breakLine: true } },
      { text: "$ python scripts/office/validate.py deck.pptx", options: { breakLine: true } },
      { text: "$ python scripts/qa_check.py deck.pptx --pdf render/deck.pdf --strict", options: { breakLine: true } },
      { text: "$ scripts/render_slides.ps1 -Pptx deck.pptx -OutDir render/ -Pdf" },
    ],
    { x: 1.15, y: 2.42, w: 7.0, h: 2.8, fontFace: MONO, fontSize: 13, color: C.white, paraSpaceAfter: 8, margin: 0 }
  );
  s11.addText(
    [
      { text: "先归一化与校验,再断言", options: { bullet: true, breakLine: true } },
      { text: "带 PDF 才覆盖 C7 / C8", options: { bullet: true, breakLine: true } },
      { text: "零 flag 才进入渲染目检", options: { bullet: true } },
    ],
    { x: 8.7, y: 2.0, w: 3.9, h: 2.8, fontFace: FONT, fontSize: 14, color: C.ink, paraSpaceAfter: 10, margin: 0 }
  );
  ["deck.pptx", "render/*.png", "qa/*.json", "evidence/run.log"].forEach((t, i) => {
    chip(s11, 0.8 + i * 2.95, 5.55, 2.7, t, C.card, C.ink);
  });
  anchor(s11, "顺序 = 依赖;产物四件套同步更新");
  pageNum(s11, 11);

  // ---- P12 palette + usage table ---------------------------------------------
  const s12 = pres.addSlide();
  s12.background = { color: C.white };
  section(s12, "11 · 样式");
  title(s12, "一套颜色,三个角色");
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
    s12.addShape(S.rect, { x, y: 1.75, w: 1.65, h: 1.0, fill: { color: fill }, line: { color: C.border, width: 1 } });
    s12.addText(hex, {
      x, y: 2.85, w: 1.65, h: 0.3, fontFace: MONO, fontSize: 12, color: C.ink, margin: 0,
    });
    s12.addText(role, {
      x, y: 3.14, w: 1.65, h: 0.3, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
    });
  });
  const hcell2 = (t) => ({
    text: t,
    options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 12, fontFace: FONT },
  });
  const dcell2 = (t) => ({
    text: t,
    options: { fill: { color: C.white }, color: C.ink, fontSize: 12, fontFace: FONT },
  });
  s12.addTable(
    [
      [hcell2("角色"), hcell2("字号"), hcell2("用途")],
      [dcell2("标题 / 名称"), dcell2("28–40pt"), dcell2("页标题、卡片题、条目名")],
      [dcell2("正文"), dcell2("12–14pt"), dcell2("要点、表格、终端代码")],
      [dcell2("说明 / 注脚"), dcell2("12pt"), dcell2("来源行、页码、标签")],
    ],
    { x: 0.8, y: 3.65, w: 11.7, colW: [2.6, 3.0, 6.1], rowH: 0.36, valign: "middle", border: { pt: 1, color: C.border } }
  );
  s12.addText("白字只做大字:珊瑚底 3.64:1,仅 ≥18pt 或 ≥14pt 粗;数值口径 WCAG 2.1,不四舍五入。", {
    x: 0.8, y: 5.35, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 12, color: C.gray, margin: 0,
  });
  anchor(s12, "角色分工见 typography.md;本页是它的可视版");
  pageNum(s12, 12);

  // ---- P13 closing ------------------------------------------------------------
  const s13 = pres.addSlide();
  s13.background = { color: C.navy };
  section(s13, "12 · 收尾", C.ice);
  s13.addShape(S.rect, { x: 0.8, y: 1.9, w: 0.34, h: 0.34, fill: { color: C.coral } });
  s13.addText("拿它当模板,或直接照流程走", {
    x: 0.8, y: 2.4, w: 11.7, h: 0.9, fontFace: FONT, fontSize: 36, bold: true, color: C.white, margin: 0,
  });
  s13.addText(
    [
      { text: "本包 = deck + 渲染图 + QA 证据 + 检查指引", options: { bullet: true, breakLine: true } },
      { text: "改内容重生成:node make_sample.js", options: { bullet: true, breakLine: true } },
      { text: "全量复跑:python tests/run_tests.py", options: { bullet: true } },
    ],
    { x: 0.8, y: 3.45, w: 11.7, h: 1.4, fontFace: FONT, fontSize: 16, color: C.ice, paraSpaceAfter: 6 }
  );
  ["① 补 C7 触发夹具", "② 真实 deck 试跑", "③ 评审两个脚手架"].forEach((t, i) => {
    chip(s13, 0.8 + i * 3.0, 5.05, 2.8, t, C.slate, C.ice, 0.46);
  });
  s13.addText("pptx-delivery · examples/acceptance-sample", {
    x: 0.8, y: 6.6, w: 9.9, h: 0.4, fontFace: FONT, fontSize: 12, color: C.ice, margin: 0,
  });
  pageNum(s13, 13, C.ice);

  const deck = path.join(HERE, "deck.pptx");
  await pres.writeFile({ fileName: deck });
  console.log("wrote " + deck);
}

(async () => {
  fs.mkdirSync(ASSETS, { recursive: true });
  await makeDonutPng(path.join(ASSETS, "donut.png"), 1200, [
    { frac: 0.42, color: C.navy },
    { frac: 0.25, color: C.slate },
    { frac: 0.18, color: "6C7BBF" },
    { frac: 0.15, color: "AAB6E8" },
  ]);
  await makeDotGridPng(path.join(ASSETS, "dot-grid.png"), 1600, 900);
  await build();
  console.log("acceptance sample done -> " + HERE);
})().catch((e) => {
  console.error("FAIL:", e);
  process.exit(1);
});
