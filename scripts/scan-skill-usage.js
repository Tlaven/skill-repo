#!/usr/bin/env node
// scan-skill-usage.js — skill 使用对账(观察期工具,未固化进任何 skill 处方)
//
// 背景:skill 的"静默错误"——该触发没触发 / 加载后被忽略——此前没有观测手段。
// 对照面 = Command Code 会话记录(~/.commandcode/projects/<slug>/*.jsonl):用户消息
// 与全部 tool_use 都会落盘,可反查"任务里出现了某 skill 的触发词、但整个会话没有
// 该 skill 的任何使用信号"的候选。
//
// 使用信号(三类):
//   1) activate —— activate_skill 工具调用
//   2) file     —— 对 skill 目录的文件操作(路径含 .commandcode/skills/<name>/、
//                  skills-repo/<name>/ 或 bundled/<name>/)
//   3) explicit —— 用户消息里出现 /skill:<name> 或 /<name>(粗匹配,可能污染)
//
// 触发词来源:各 SKILL.md description 的 TRIGGER 段(逗号分隔)。无 TRIGGER 段的
// skill 不参与候选检测(会在末尾列出)——触发面写在别处(如 system prompt 规则)的
// skill 覆盖不到,这是已知盲区。
//
// 用法:
//   node scan-skill-usage.js [--skills-dir DIR]... [--projects-dir DIR]
//   默认 --skills-dir: ~/.commandcode/skills 与 ~/.agents/skills
//   默认 --projects-dir: ~/.commandcode/projects
//   bundled skill 不在默认面内,需要时手动加,例如(Windows):
//     node scan-skill-usage.js --skills-dir "C:/Users/<你>/AppData/Local/nvm/v22.23.2/node_modules/command-code/dist/bundled"
//
// 边界(诚实声明):
//   - 只覆盖有落盘的会话(--no-session 与不留痕的宿主 → 不可观测)
//   - 触发词匹配是启发式:命中≠该用,未命中≠不该用(词表之外的说法会漏)
//   - 输出是候选;判定"该不该触发、有无损失"需要人工/验证者复核——工具只筛不判

"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");

// ── 参数 ──────────────────────────────────────────────────────────────
const opts = { skillsDirs: [], projectsDir: null };
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === "--skills-dir") opts.skillsDirs.push(argv[++i]);
  else if (argv[i] === "--projects-dir") opts.projectsDir = argv[++i];
  else {
    console.error("未知参数: " + argv[i]);
    process.exit(2);
  }
}
if (!opts.skillsDirs.length) {
  opts.skillsDirs = [
    path.join(os.homedir(), ".commandcode", "skills"),
    path.join(os.homedir(), ".agents", "skills"),
  ];
}
if (!opts.projectsDir) opts.projectsDir = path.join(os.homedir(), ".commandcode", "projects");

// ── skill 发现与触发词提取 ──────────────────────────────────────────
function unquote(s) {
  s = s.trim();
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) s = s.slice(1, -1);
  return s.trim();
}

function extractTriggers(desc) {
  const m = desc.match(/TRIGGER[:：]\s*([\s\S]*)/i);
  if (!m) return null;
  let s = m[1];
  const cut = s.search(/不适用[:：]/);
  if (cut >= 0) s = s.slice(0, cut);
  return s
    .split(/[,，]/)
    .map((w) => unquote(w.trim()).replace(/^["'“”。]+|["'“”]+$/g, "").replace(/。+$/, "").trim())
    .filter((w) => w.length >= 2);
}

function loadSkills(dirs) {
  const skills = new Map();
  for (const dir of dirs) {
    if (!fs.existsSync(dir)) continue;
    let entries = [];
    try {
      entries = fs.readdirSync(dir);
    } catch {
      continue;
    }
    for (const entry of entries) {
      const skPath = path.join(dir, entry, "SKILL.md");
      if (!fs.existsSync(skPath)) continue;
      let txt = "";
      try {
        txt = fs.readFileSync(skPath, "utf8");
      } catch {
        continue;
      }
      const fm = txt.match(/^---\r?\n([\s\S]*?)\r?\n---/);
      if (!fm) continue;
      const nameM = fm[1].match(/^name:\s*(.+)$/m);
      const descM = fm[1].match(/^description:\s*(.+)$/m);
      if (!nameM || !descM) continue;
      const name = unquote(nameM[1]);
      if (skills.has(name)) continue;
      skills.set(name, { name, triggers: extractTriggers(unquote(descM[1])) });
    }
  }
  return skills;
}

// ── 会话扫描 ────────────────────────────────────────────────────────
function hasPathPattern(s, name) {
  // input 先经过 JSON.stringify:Windows 路径的反斜杠会变成双反斜杠——统一压成
  // 正斜杠再匹配,否则纯反斜杠路径(如 skills-repo\name\)永远漏检。
  const sl = s.toLowerCase().replace(/\\\\/g, "/").replace(/\\/g, "/");
  const n = name.toLowerCase();
  return (
    sl.includes(".commandcode/skills/" + n + "/") ||
    sl.includes("skills-repo/" + n + "/") ||
    sl.includes("bundled/" + n + "/") ||
    sl.includes("/" + n + "/skill.md")
  );
}

function sigAdd(map, name, kind) {
  if (!map.has(name)) map.set(name, new Set());
  map.get(name).add(kind);
}

function bump(stats, name, kind) {
  if (!stats.has(name)) stats.set(name, { sessions: new Set(), activate: 0, file: 0, explicit: 0 });
  stats.get(name)[kind]++;
}

const skills = loadSkills(opts.skillsDirs);
const skillNames = [...skills.keys()];
const stats = new Map();
const candidates = [];
const slugs = [];
let totalSessions = 0;

function scanOne(file, slug, sid) {
  let lines;
  try {
    lines = fs.readFileSync(file, "utf8").split(/\r?\n/).filter(Boolean);
  } catch {
    return;
  }
  const userTexts = [];
  let firstUser = "";
  let date = "";
  const sessionSignals = new Map();

  for (const line of lines) {
    let e;
    try {
      e = JSON.parse(line);
    } catch {
      continue;
    }
    if (e.type === "session") {
      date = (e.timestamp || "").slice(0, 10);
      continue;
    }
    if (e.type !== "message") continue;
    const m = e.message || {};
    const c = Array.isArray(m.content) ? m.content : [];
    if (m.role === "user") {
      for (const item of c) {
        if (item.type === "text" && item.text) {
          userTexts.push(item.text);
          if (!firstUser && !item.text.startsWith("<")) firstUser = item.text;
        }
      }
    } else if (m.role === "assistant") {
      for (const item of c) {
        if (item.type !== "tool_use") continue;
        if (item.name === "activate_skill" && item.input && item.input.name) {
          sigAdd(sessionSignals, item.input.name, "activate");
          bump(stats, item.input.name, "activate");
        }
        const s = JSON.stringify(item.input || {});
        for (const name of skillNames) {
          if (hasPathPattern(s, name)) {
            sigAdd(sessionSignals, name, "file");
            bump(stats, name, "file");
          }
        }
      }
    }
  }

  const joined = userTexts.join("\n").toLowerCase();
  for (const name of skillNames) {
    if (joined.includes("skill:" + name.toLowerCase()) || joined.includes("/" + name.toLowerCase())) {
      sigAdd(sessionSignals, name, "explicit");
      bump(stats, name, "explicit");
    }
  }

  for (const name of skillNames) {
    const sk = skills.get(name);
    if (!sk.triggers || !sk.triggers.length) continue;
    const hit = sk.triggers.filter((t) => joined.includes(t.toLowerCase()));
    if (!hit.length) continue;
    const signaled = sessionSignals.has(name) && sessionSignals.get(name).size;
    if (signaled) {
      const st = stats.get(name) || { sessions: new Set(), activate: 0, file: 0, explicit: 0 };
      stats.set(name, st);
      st.sessions.add(sid);
    } else {
      candidates.push({
        slug,
        sid,
        date,
        name,
        hit: hit.slice(0, 6),
        firstUser: firstUser.replace(/\s+/g, " ").slice(0, 90),
      });
    }
  }
  for (const [name, kinds] of sessionSignals) {
    if (!kinds.size) continue;
    if (!stats.has(name)) stats.set(name, { sessions: new Set(), activate: 0, file: 0, explicit: 0 });
    stats.get(name).sessions.add(sid);
  }
}

if (fs.existsSync(opts.projectsDir)) {
  for (const slug of fs.readdirSync(opts.projectsDir)) {
    const slugDir = path.join(opts.projectsDir, slug);
    let isDir = false;
    try {
      isDir = fs.statSync(slugDir).isDirectory();
    } catch {
      isDir = false;
    }
    if (!isDir) continue;
    slugs.push(slug);
    for (const f of fs.readdirSync(slugDir)) {
      if (!f.endsWith(".jsonl") || f.includes(".checkpoints.")) continue;
      totalSessions++;
      scanOne(path.join(slugDir, f), slug, f.replace(/\.jsonl$/, ""));
    }
  }
}

// ── 报告 ────────────────────────────────────────────────────────────
console.log("scan-skill-usage — skill 使用对账(观察期)");
console.log("skill 面: " + opts.skillsDirs.join(" | "));
console.log("会话面: " + opts.projectsDir + "(" + slugs.length + " 个 slug / " + totalSessions + " 个会话)");
console.log("");
console.log("[信号统计] sessions=有信号的会话数; activate/file/explicit=事件数");
for (const [name] of skills) {
  const st = stats.get(name) || { sessions: new Set(), activate: 0, file: 0, explicit: 0 };
  console.log(
    "  " +
      name.padEnd(22) +
      " sessions " +
      st.sessions.size +
      " · activate " +
      st.activate +
      " · file " +
      st.file +
      " · explicit " +
      st.explicit
  );
}
console.log("");
if (candidates.length) {
  console.log("[候选: 触发词命中但无使用信号] (需人工复核)");
  candidates.sort((a, b) => (a.date < b.date ? -1 : 1));
  for (const c of candidates) {
    console.log("  * " + c.slug + "/" + c.sid.slice(0, 8) + " " + c.date + " -> " + c.name);
    console.log("      命中: " + c.hit.join(" | "));
    console.log("      首条: " + c.firstUser);
  }
} else {
  console.log("[候选: 无]");
}
const noTrigger = [...skills.values()].filter((s) => !s.triggers || !s.triggers.length).map((s) => s.name);
if (noTrigger.length) {
  console.log("");
  console.log("无 TRIGGER 段、未纳入候选检测: " + noTrigger.join(", "));
}
console.log("");
console.log("边界: 仅覆盖有落盘会话;匹配为启发式;候选需人工复核(工具只筛不判)。");
