"use strict";
// Shared helpers for pptx test fixtures (controls + end-to-end deck).
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const OUT = path.join(__dirname, "out");
const ASSETS = path.join(OUT, "assets");

// Palette: "Midnight Executive" (SKILL.md 设计建议) + one accent.
const C = {
  navy: "1E2761",
  ice: "CADCFC",
  white: "FFFFFF",
  ink: "222222",
  gray: "64748B",
  light: "F7F8FA",
  card: "F0F4FA",
  coral: "E4574F", // large-text / shape accent only (3.64:1 on white -> use >= 18pt)
  cream: "F9E795",
};
const FONT = "Microsoft YaHei";

function ensureDirs() {
  fs.mkdirSync(ASSETS, { recursive: true });
}

function newDeck() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in -> 960 x 540 pt
  return pres;
}

function shapes(pres) {
  const S = pres.ShapeType || pres.shapes || {};
  return {
    rect: S.rect || S.RECTANGLE,
    roundRect: S.roundRect || S.ROUNDED_RECTANGLE,
    ellipse: S.ellipse || S.OVAL,
    line: S.line || S.LINE,
  };
}

async function save(pres, name) {
  const file = path.join(OUT, name);
  await pres.writeFile({ fileName: file });
  console.log("wrote " + file);
}

function hexToRgb(hex) {
  return {
    r: parseInt(hex.slice(0, 2), 16),
    g: parseInt(hex.slice(2, 4), 16),
    b: parseInt(hex.slice(4, 6), 16),
    alpha: 1,
  };
}

// Flat-color PNG (for aspect tests).
async function makeFlatPng(file, w, h, hex) {
  await sharp({ create: { width: w, height: h, channels: 4, background: hexToRgb(hex) } })
    .png()
    .toFile(file);
}

// Bar-chart-like PNG, no embedded text (labels live in slide text).
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

module.exports = {
  OUT,
  ASSETS,
  C,
  FONT,
  ensureDirs,
  newDeck,
  shapes,
  save,
  hexToRgb,
  makeFlatPng,
  makeBarPng,
};
