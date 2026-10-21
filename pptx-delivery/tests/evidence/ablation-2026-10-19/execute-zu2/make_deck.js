"use strict";
// execute-zu2: 把 outputs/组2.md 的页面规划落成 8 页 PPTX。
// 约束来自规划本身:16:9 13.333×7.5 / 版心 0.75in / 安全区 0.5in /
// 间距刻度 8·16·24·40·64pt / 字号 H0 64·H1 40·H2 28·正文 18–20·表格 16·注 14 /
// 色板 6 色 / 每页红色 ≤ 1 处 / 右下角 14pt“所以呢”句 ≤ 28 字。
// Run:  node make_deck.js   (需全局 pptxgenjs)

const pptxgen = require("pptxgenjs");

const FONT = "Microsoft YaHei";
const MONO = "Consolas";
const NUM = "Arial"; // 大号数字:Consolas 的 0 带斜杠,读作 Ø
const C = {
  ink: "1A1A1A",
  gray: "4D4D4D",
  light: "9A9A9A", // 仅用于深底文字或非文字线条(白底 14pt 文字达不到 4.5:1)
  base: "F2F2F2",
  white: "FFFFFF",
  red: "C0392B",
};
const W = 13.333;
const H = 7.5;
const M = 0.75;
const CW = W - 2 * M; // 11.833
const P = (pt) => pt / 72;
const P8 = P(8);
const P16 = P(16);
const P24 = P(24);
const P40 = P(40);
const P64 = P(64);

const TOTAL = 8;

let pres;
let S;

function newSlide(bg) {
  const s = pres.addSlide();
  if (bg) s.background = { color: bg };
  return s;
}

/** 正文文本:默认 18pt,左对齐,零内边距 */
function txt(s, text, o) {
  const opt = Object.assign(
    {
      fontFace: FONT,
      fontSize: 18,
      color: C.ink,
      margin: 0,
      valign: "top",
      align: "left",
      objectName: "t-" + Math.random().toString(36).slice(2, 8),
    },
    o
  );
  return s.addText(text, opt);
}

/** 装饰性色块,统一 bg- 前缀,越界/重叠检查时豁免 */
function block(s, x, y, w, h, color, extra) {
  return s.addShape(S.rect, Object.assign({
    x, y, w, h,
    fill: { color },
    line: { color, width: 0 },
    objectName: "bg-" + Math.random().toString(36).slice(2, 8),
  }, extra || {}));
}

function hair(s, x, y, w, color, pt, name) {
  return s.addShape(S.rect, {
    x, y, w, h: P(pt),
    fill: { color },
    line: { color, width: 0 },
    objectName: "bg-" + (name || "hair"),
  });
}

/** 页眉 + 页脚(第 2–7 页) */
function chrome(s, n, section, close) {
  if (section) {
    block(s, M, 0.565, 0.09, 0.09, C.ink, { objectName: "bg-mark" });
    txt(s, section, {
      x: M + 0.21, y: 0.5, w: 5, h: 0.24,
      fontSize: 14, color: C.gray, objectName: "ftr-section",
    });
  }
  txt(s, String(n).padStart(2, "0") + " / 0" + TOTAL, {
    x: W - M - 1.2, y: 0.5, w: 1.2, h: 0.24,
    fontSize: 14, color: C.gray, align: "right", fontFace: MONO, objectName: "ftr-num",
  });
  txt(s, "AI 生成 PPTX 的交付验收", {
    x: M, y: 6.53, w: 4.8, h: 0.26,
    fontSize: 14, color: C.gray, objectName: "ftr-deck",
  });
  txt(s, close, {
    x: W - M - 6.4, y: 6.53, w: 6.4, h: 0.26,
    fontSize: 14, color: C.gray, align: "right", objectName: "ftr-close",
  });
}

/** 两行 action title */
function title(s, l1, l2) {
  txt(s, l1, { x: M, y: 0.76, w: CW, h: 0.68, fontSize: 40, bold: true, color: C.ink });
  txt(s, l2, { x: M, y: 1.44, w: CW, h: 0.68, fontSize: 40, bold: true, color: C.ink });
}

// ---------------------------------------------------------------------------
// P1 封面
// ---------------------------------------------------------------------------
function slide1() {
  const s = newSlide(C.ink);
  txt(s, "内部工程团队 · 交付规范提案 v1", {
    x: W - M - 6.2, y: 0.5, w: 6.2, h: 0.28,
    fontSize: 14, color: C.light, align: "right", objectName: "ftr-eyebrow",
  });

  txt(s, "「能打开」不是交付标准", {
    x: M, y: 1.95, w: 9.2, h: 0.66, fontSize: 40, bold: true, color: C.white,
  });
  block(s, M, 2.68, 2.72, P(2), C.red, { objectName: "bg-accent-rule" });
  txt(s, "AI 生成的 PPTX 需要一道", {
    x: M, y: 2.9, w: 9.2, h: 0.66, fontSize: 40, bold: true, color: C.white,
  });
  txt(s, "可执行、可复现的验收闸门", {
    x: M, y: 3.58, w: 10.2, h: 0.66, fontSize: 40, bold: true, color: C.white,
  });

  txt(s, "C1–C9 九类断言 · 7 个负控样本 · 交付前三层清单", {
    x: M, y: 4.62, w: 10.5, h: 0.36, fontSize: 20, color: C.light,
  });

  txt(s, "提案:交付流水线维护者 · 2026-10-20", {
    x: M, y: 6.53, w: 5.2, h: 0.26, fontSize: 14, color: C.light, objectName: "ftr-deck",
  });
  txt(s, "本 deck 的每条主张都能被机器判定", {
    x: W - M - 6.4, y: 6.53, w: 6.4, h: 0.26,
    fontSize: 14, color: C.light, align: "right", objectName: "ftr-close",
  });
}

// ---------------------------------------------------------------------------
// P2 症状 — 左 2×2 症状卡 / 右 谁会先发现
// ---------------------------------------------------------------------------
function slide2() {
  const s = newSlide(C.white);
  chrome(s, 2, "01 · 症状", "错误的验收标准:文件能被 PowerPoint 打开");
  title(s, "最常见的失败是不报错:文件能打开、能翻页", "却在字号、越界、渲染上塌方");

  const cards = [
    { n: "01", name: "脚注被压到 8pt", why: "没人读小字,导出也不报错", inverted: true },
    { n: "02", name: "图片被拉伸变形", why: "预览看不出 12% 的拉伸" },
    { n: "03", name: "文本框出到页外", why: "翻页时看不出,PDF 才裁" },
    { n: "04", name: "字体被换成宋体", why: "换机才发生,原机永远正常" },
  ];
  const cw = (6.9 - P24) / 2;
  const ch = 1.72;
  const xs = [M, M + cw + P24];
  const ys = [2.28, 2.28 + ch + P24];

  cards.forEach((c, i) => {
    const x = xs[i % 2];
    const y = ys[Math.floor(i / 2)];
    block(s, x, y, cw, ch, c.inverted ? C.ink : C.base, { objectName: "bg-card" + (i + 1) });
    txt(s, c.n, {
      x: x + 0.22, y: y + 0.2, w: 0.6, h: 0.24,
      fontSize: 14, color: c.inverted ? C.light : C.gray, fontFace: MONO, objectName: "lbl-card-num",
    });
    txt(s, c.name, {
      x: x + 0.22, y: y + 0.46, w: cw - 0.44, h: 0.36,
      fontSize: 20, bold: true, color: c.inverted ? C.white : C.ink,
    });
    txt(s, c.why, {
      x: x + 0.22, y: y + 0.92, w: cw - 0.44, h: 0.62,
      fontSize: 18, color: c.inverted ? C.light : C.gray,
    });
  });

  // 右栏
  const rx = M + 6.9 + P24;
  const rw = 4.6;
  txt(s, "谁会先发现", {
    x: rx, y: 2.24, w: rw, h: 0.28, fontSize: 14, color: C.gray, objectName: "lbl-right-head",
  });
  hair(s, rx, 2.58, rw, C.ink, 1, "rule-right-head");

  const rows = [
    { who: "生成脚本", found: "无" },
    { who: "打开文件", found: "无" },
    { who: "评审现场 / 客户", found: "有", hot: true },
  ];
  const rowH = P64; // 64pt(组间一级),不再用 64.8pt 这种刻度外值
  rows.forEach((r, i) => {
    const y = 2.76 + i * rowH;
    if (i > 0) hair(s, rx, y - 0.02, rw, C.light, 0.75, "rule-right-row");
    if (r.hot) {
      block(s, rx, y + 0.04, rw, rowH - 0.12, C.base, { objectName: "bg-hotrow" });
      block(s, rx, y + 0.04, 0.06, rowH - 0.12, C.ink, { objectName: "bg-hotbar" });
    }
    txt(s, r.who, {
      x: rx + (r.hot ? 0.24 : 0), y: y + 0.22, w: 2.9, h: 0.36, fontSize: 20, color: C.ink,
    });
    txt(s, r.found, {
      x: rx + rw - 1.2, y: y + 0.22, w: 1.2, h: 0.36,
      fontSize: 20, bold: true, color: r.hot ? C.ink : C.gray, align: "right",
    });
  });
}

// ---------------------------------------------------------------------------
// P3 九类断言 3×3 矩阵
// ---------------------------------------------------------------------------
function slide3() {
  const s = newSlide(C.white);
  chrome(s, 3, "02 · 九类断言", "九类 = 九个可独立失败的点,任一点失败即整体不通过");
  title(s, "九类断言覆盖全部已知失败模式", "每一类都有独立的判定对象");

  const colW = (CW - 2 * P24) / 3;
  const cols = [
    {
      head: "文件层",
      cells: [
        ["C1", "结构", "判:引用可解析", true],
        ["C2", "占位符", "判:占位文本残留"],
        ["C3", "字号下限", "判:所有 sz 最小值"],
      ],
    },
    {
      head: "视觉层",
      cells: [
        ["C4", "颜色卫生", "判:非法色值"],
        ["C5", "对比度 WCAG", "判:文字底色比值"],
        ["C6", "图片形变", "判:显示比 vs 原图"],
      ],
    },
    {
      head: "产出层",
      cells: [
        ["C7", "越界", "判:元素与安全区"],
        ["C8", "渲染保真", "判:PDF 文本与像素"],
        ["C9", "可编辑性", "判:能否二次编辑"],
      ],
    },
  ];

  const cellH = 0.92;
  cols.forEach((col, ci) => {
    const x = M + ci * (colW + P24);
    txt(s, col.head, { x, y: 2.26, w: colW, h: 0.28, fontSize: 14, color: C.gray, objectName: "lbl-col-head" });
    hair(s, x, 2.62, colW, C.ink, 1.5, "rule-col-head");
    col.cells.forEach((cell, ri) => {
      const y = 2.84 + ri * (cellH + P16);
      block(s, x, y, colW, cellH, cell[3] ? C.white : C.base, { objectName: "bg-cell" });
      if (cell[3]) {
        s.addShape(S.rect, {
          x, y, w: colW, h: cellH,
          fill: { color: C.white, transparency: 100 },
          line: { color: C.ink, width: 1 },
          objectName: "bg-focus-cell",
        });
      }
      txt(s, cell[0], {
        x: x + 0.2, y: y + 0.12, w: 0.72, h: 0.5,
        fontSize: 28, color: C.gray, fontFace: MONO, objectName: "lbl-c-num",
      });
      txt(s, cell[1], {
        x: x + 0.98, y: y + 0.12, w: colW - 1.16, h: 0.34, fontSize: 20, bold: true, color: C.ink,
      });
      txt(s, cell[2], {
        x: x + 0.98, y: y + 0.5, w: colW - 1.16, h: 0.3, fontSize: 18, color: C.gray,
      });
    });
  });
}

// ---------------------------------------------------------------------------
// P4 阈值表
// ---------------------------------------------------------------------------
function slide4() {
  const s = newSlide(C.white);
  chrome(s, 4, "03 · 阈值", "阈值不靠主观估计:由干净基线 + 7 个负控样本校准");
  title(s, "每一类断言都要落到一个数字", "阈值写进配置,判定只有通过或不通过");

  const head = ["断言", "判的是哪个量", "阈值(默认值,待校准)", "失败等级"];
  const rows = [
    ["C1 结构", "部件引用能否全部解析", "未解析引用 = 0", "阻断"],
    ["C2 占位符", "残留占位文本", "命中 = 0", "阻断"],
    ["C3 字号下限", "每个 run 的 sz 最小值", "≥ 14pt,违规 = 0", "阻断"],
    ["C4 颜色卫生", "非法色值与负阴影", "非法色值 = 0", "阻断"],
    ["C5 对比度", "文字与底色的 WCAG 比值", "正文 ≥ 4.5:1,大字 ≥ 3:1", "阻断"],
    ["C6 图片形变", "显示比例偏离原图比例", "偏差 ≤ 2%", "告警"],
    ["C7 越界", "元素是否越出 0.5in 安全区", "越界元素 = 0", "阻断"],
    ["C8 渲染保真", "PDF 文本层 + 逐像素差", "段落全在,差 ≤ 0.3%", "告警"],
    ["C9 可编辑性", "全页图占比与可编辑文本", "无文本且覆盖 ≥ 80% = 0", "阻断"],
  ];

  const tbl = [head, ...rows].map((r, ri) =>
    r.map((t, ci) => {
      const opt = {
        fontFace: FONT,
        fontSize: 16,
        color: ri === 0 ? C.gray : C.ink,
        bold: ri === 0,
        align: ci === 2 ? "right" : "left",
        valign: "middle",
        border: { type: "none" },
      };
      if (ri > 0 && ci === 3) {
        const block = t === "阻断";
        return {
          text: [
            { text: block ? "  ● " : "  ○ ", options: { fontSize: 16, color: C.gray } },
            { text: t, options: { fontSize: 16, color: block ? C.ink : C.gray, bold: block } },
          ],
          options: opt,
        };
      }
      return { text: t, options: opt };
    })
  );

  const top = 2.24;
  const rowH = 0.396;
  s.addTable(tbl, {
    x: M, y: top, w: CW,
    colW: [1.55, 4.45, 4.18, 1.65],
    rowH,
    fontFace: FONT,
    fontSize: 16,
    margin: 0.06,
    valign: "middle",
    border: { type: "none" },
    objectName: "tbl-thresholds",
  });

  hair(s, M, top + rowH - P(1), CW, C.ink, 1.5, "rule-th-head");
  for (let i = 2; i < 10; i++) {
    hair(s, M, top + rowH * i - P(0.5), CW, C.light, 0.5, "rule-row");
  }
  hair(s, M, top + rowH * 10 - P(1), CW, C.ink, 1.2, "rule-th-bottom");
}

// ---------------------------------------------------------------------------
// P5 负控记分板
// ---------------------------------------------------------------------------
function slide5() {
  const s = newSlide(C.white);
  chrome(s, 5, "04 · 负控", "负控说明检查器有效,不说明覆盖完整——覆盖靠缺陷库");
  title(s, "检查器本身也要被检查", "7 个蓄意缺陷必须全中,干净基线必须 0 误报");

  const defects = [
    ["D1", "空占位符", "C2"],
    ["D2", "字号 8pt", "C3"],
    ["D3", "非色板红", "C4"],
    ["D4", "对比 2.8:1", "C5"],
    ["D5", "拉伸 12%", "C6"],
    ["D6", "文本出界", "C7"],
    ["D7", "文本转曲", "C9"],
  ];
  const gw = (CW - 6 * P8) / 7;
  defects.forEach((d, i) => {
    const x = M + i * (gw + P8);
    block(s, x, 2.24, gw, 1.0, C.base, { objectName: "bg-score-cell" });
    txt(s, d[0] + "  " + d[1], {
      x: x + 0.14, y: 2.4, w: gw - 0.24, h: 0.26, fontSize: 14, color: C.gray, objectName: "lbl-defect",
    });
    txt(s, "✓ 命中 " + d[2], {
      x: x + 0.14, y: 2.78, w: gw - 0.24, h: 0.26, fontSize: 14, color: C.ink, objectName: "lbl-hit",
    });
  });

  // 两个数字,等大并置
  txt(s, "7", {
    x: M, y: 3.62, w: 0.58, h: 1.05, fontSize: 64, color: C.ink, fontFace: NUM,
  });
  txt(s, "/7", {
    x: M + 0.6, y: 3.96, w: 0.9, h: 0.44, fontSize: 28, color: C.gray, fontFace: NUM,
  });
  txt(s, "7 个蓄意缺陷,全部被抓", {
    x: M, y: 4.86, w: 4.2, h: 0.32, fontSize: 18, color: C.gray,
  });

  block(s, 6.42, 3.68, P(4), 1.0, C.red, { objectName: "bg-gate-mark" });
  txt(s, "0", {
    x: 6.72, y: 3.62, w: 0.62, h: 1.05, fontSize: 64, color: C.ink, fontFace: NUM,
  });
  txt(s, "干净基线全部通过,误报 0", {
    x: 6.72, y: 4.86, w: 5.4, h: 0.32, fontSize: 18, color: C.gray,
  });

  txt(s, "合并条件:负控 7/7 且误报 0;任一不满足,阻断", {
    x: M, y: 5.62, w: CW, h: 0.36, fontSize: 20, color: C.ink, bold: true,
  });
}

// ---------------------------------------------------------------------------
// P6 三层清单 + 盲区条带
// ---------------------------------------------------------------------------
function slide6() {
  const s = newSlide(C.white);
  chrome(s, 6, "05 · 清单", "清单的价值不在全,而在每条都能判 True / False");
  title(s, "交付验收清单分三层执行", "自动断言、阈值复核、人工目检,并标出盲区");

  const colW = (CW - 2 * P24) / 3;
  const cols = [
    {
      head: "01 机器断言",
      items: [
        [
          { text: "□  C1–C9 全自动,", options: {} },
          { text: "0 容忍", options: { color: C.red, bold: true } },
        ],
        [{ text: "□  交付前必跑,失败不出预览", options: {} }],
        [{ text: "□  未过闸不进评审", options: {} }],
      ],
    },
    {
      head: "02 阈值复核",
      items: [
        [{ text: "□  阈值集中在配置,不进模板", options: {} }],
        [{ text: "□  配置 diff 进评审", options: {} }],
        [{ text: "□  阈值变更须重跑基线", options: {} }],
      ],
    },
    {
      head: "03 人工目检",
      items: [
        [{ text: "□  叙事逻辑", options: {} }],
        [{ text: "□  图表语义", options: {} }],
        [{ text: "□  字体观感", options: {} }],
        [{ text: "□  页面平衡", options: {} }],
        [{ text: "□  术语一致", options: {} }],
      ],
    },
  ];

  cols.forEach((col, ci) => {
    const x = M + ci * (colW + P24);
    txt(s, col.head, { x, y: 2.26, w: colW, h: 0.28, fontSize: 14, color: C.gray, objectName: "lbl-col-head" });
    hair(s, x, 2.62, colW, C.ink, 1, "rule-col-head");
    col.items.forEach((it, i) => {
      txt(s, it, {
        x, y: 2.86 + i * 0.35, w: colW, h: 0.34, fontSize: 18, color: C.ink,
      });
    });
  });

  // 盲区条带
  block(s, M, 5.02, CW, 1.34, C.base, { objectName: "bg-blind-band" });
  txt(s, [
    { text: "目检盲区", options: { bold: true } },
    { text: "(自动化不覆盖)", options: { bold: false } },
  ], {
    x: M + 0.33, y: 5.3, w: 6, h: 0.3, fontSize: 18, color: C.ink,
  });
  txt(s, "动画与切换 · 备注可读性 · 投影色偏 · 跨机字体 · 表述敏感性", {
    x: M + 0.33, y: 5.72, w: CW - 0.66, h: 0.34, fontSize: 18, color: C.gray,
  });
}

// ---------------------------------------------------------------------------
// P7 三道闸
// ---------------------------------------------------------------------------
function slide7() {
  const s = newSlide(C.white);
  chrome(s, 7, "06 · 流程", "闸门位置比数量重要:越靠前修,成本越低");
  title(s, "QA 不是交付前的一次性动作", "而是三道闸:生成即检、合并前拦、交付前签");

  const gates = [
    { tag: "闸 1", name: "生成即检", desc: "输出后跑 C1–C9,\n失败不出预览", owner: "责任:生成器 owner", fail: "失败 → 不出预览" },
    { tag: "闸 2", name: "合并前拦", desc: "CI 跑负控与基线,\n7/7 且 0 才可合", owner: "责任:模板维护者", fail: "失败 → 不合并" },
    { tag: "闸 3", name: "交付前签", desc: "人工目检 + 渲染抽检,\n签字留档", owner: "责任:交付人", fail: "失败 → 不签字" },
    { tag: "终点", name: "交付", desc: "三闸全过才产出交付件", owner: "留档:签字与报告", fail: "" },
  ];
  const nw = 2.53;
  const gap = P40; // 节点间距 40pt(组间一级)
  const axisY = 4.06;

  // 主轴(先画线,节点压在上面;收在终点节点)
  hair(s, M, axisY - P(0.75), 9.52, C.ink, 0.75, "rule-axis");

  gates.forEach((g, i) => {
    const x = M + i * (nw + gap);
    txt(s, g.tag, { x, y: 2.34, w: nw, h: 0.24, fontSize: 14, color: C.gray, objectName: "lbl-gate-tag" });
    txt(s, g.name, { x, y: 2.58, w: nw, h: 0.36, fontSize: 20, bold: true, color: C.ink });
    txt(s, g.desc, {
      x, y: 3.0, w: nw, h: 0.62, fontSize: 18, color: C.gray, lineSpacingMultiple: 1.05,
    });
    txt(s, g.owner, { x, y: 3.7, w: nw, h: 0.24, fontSize: 14, color: C.gray, objectName: "lbl-owner" });

    // 节点标记
    if (i < 3) {
      s.addShape(S.ellipse, {
        x: x + 0.04, y: axisY - 0.09, w: 0.18, h: 0.18,
        fill: { color: C.ink }, line: { color: C.ink, width: 0 },
        objectName: "bg-node",
      });
    } else {
      block(s, x + 0.04, axisY - 0.09, 0.18, 0.18, C.ink, { objectName: "bg-node-end" });
    }

    if (g.fail) {
      txt(s, g.fail, { x, y: 4.28, w: nw, h: 0.3, fontSize: 18, color: C.ink });
    }
  });

  // 主轴
  // 失败回流(全页唯一红)
  const ay = 5.16;
  s.addShape(S.line, {
    x: M + 0.2, y: ay, w: 9.32, h: 0,
    line: { color: C.red, width: 1.25, beginArrowType: "triangle", endArrowType: "none" },
    objectName: "bg-return-flow",
  });
  txt(s, "失败回流:退回修改,重新过一遍三道闸", {
    x: M + 0.2, y: 5.34, w: 8, h: 0.3, fontSize: 18, color: C.ink,
  });
}

// ---------------------------------------------------------------------------
// P8 结论 + 行动
// ---------------------------------------------------------------------------
function slide8() {
  const s = newSlide(C.ink);
  txt(s, "内部工程团队 · 交付规范提案 v1", {
    x: W - M - 6.2, y: 0.5, w: 6.2, h: 0.28,
    fontSize: 14, color: C.light, align: "right", objectName: "ftr-eyebrow",
  });

  txt(s, "未通过 C1–C9 的 PPTX", {
    x: M, y: 1.9, w: 10.2, h: 0.66, fontSize: 40, bold: true, color: C.white,
  });
  txt(s, "不进入交付", {
    x: M, y: 2.6, w: 6.0, h: 0.66, fontSize: 40, bold: true, color: C.white,
  });
  block(s, M, 3.32, 2.72, P(2), C.red, { objectName: "bg-accent-rule" });

  const reqs = [
    "① 把 C1–C9 写进交付定义",
    "② 7 个负控进 CI,7/7 + 0 误报作为合并条件",
    "③ 每季度重校准阈值与缺陷库",
  ];
  reqs.forEach((r, i) => {
    txt(s, r, { x: M, y: 3.86 + i * 0.572, w: 10.5, h: 0.34, fontSize: 18, color: C.white });
  });

  txt(s, "下一步:两周内接入现有生成脚本", {
    x: M, y: 5.68, w: 8, h: 0.28, fontSize: 14, color: C.light, objectName: "ftr-next",
  });

  txt(s, "本 deck 的每条主张,都能被 C1–C9 判真假", {
    x: W - M - 6.4, y: 6.53, w: 6.4, h: 0.26,
    fontSize: 14, color: C.light, align: "right", objectName: "ftr-close",
  });
}

async function main() {
  pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "交付流水线维护者";
  pres.title = "AI 生成 PPTX 的交付验收";
  S = pres.ShapeType || pres.shapes;

  slide1(); slide2(); slide3(); slide4(); slide5(); slide6(); slide7(); slide8();

  await pres.writeFile({ fileName: "deck.pptx" });
  console.log("written: deck.pptx");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
