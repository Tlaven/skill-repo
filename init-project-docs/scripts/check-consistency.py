#!/usr/bin/env python3
"""check-consistency.py — heuristic warnings for copied or drifting docs.

WARNING tool: it does not decide truth, and should not be a hard gate.

Default checks:
- Duplicate term definitions: a `- **term**: ...` definition in `docs/` that
  redefines a glossary term, or appears more than once.
- Unregistered definitions: a `- **term**: ...` definition in `docs/`
  whose term is not in docs/glossary.md.
- Numeric conflicts: the same key written with different values inside inline
  code or table cells (prose is ignored to keep noise low).
- Duplicate literals: the same key:value inside inline code or table cells in
  two or more live docs.
- Duplicate aliases: a backticked glossary alias (e.g. `profCoast`) appears in
  two or more live docs (README is included).
- Dangling clause codes: a live doc cites a stable code (`D-14` / `A-1` / `R-5`)
  that no live doc defines. Codes are the only legal cross-doc reference, so a
  code without a definition means it was renamed or retired and the citation
  rotted. Record codes (`ADR-031`) are excluded — records expire, clauses do not.
- Over-budget: soft line caps (L1 100 / L2 80 / L3 400; see DEFAULT_BUDGETS).
- Scope: docs/.live when present (only allowlisted docs count as current);
  --all-docs ignores it and scans every docs/ file (migration / audit).

Opt-in:
- Single-module terms (`--glossary-locality`): a glossary term mentioned
  >= N times in exactly one module and < N times elsewhere. Candidate only;
  review manually before demoting.

Records (`docs/decisions/`, `docs/reviews/`) are history, not current docs:
they are not scanned (ADR option names / rationale bullets are not terms).
Definition scanning is limited to sections whose heading names a definition
scope (`是什么 / 定义 / 术语 / 概念`) or to files with no heading at all —
`[为什么]` / `[不变量]` bullets are rationale and never term definitions.
L1 files are not scanned for `- **term**` definitions: emphasis bullets there
are not term definitions. Use `--ignore` / `--ignore-alias` for known noise.
"""

import argparse
import fnmatch
import json
import os
import re
import sys
from collections import defaultdict

from _doc_common import active_mask, iter_docs, live_allowlist_missing, read_lines, rel

DEF_RE = re.compile(r"^\s*[-*]\s+\*\*([^*]+?)\*\*\s*[:：]\s*(.+)$")
NUM_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_.]{2,})\s*[:=]\s*(-?(?:\d+(?:\.\d+)?|\.\d+))\b"
)
# Stable clause codes: defined either as a bolded table cell (`| **D-14** | ...`)
# or as a numbered heading (`## E-1: ...`), cited anywhere as `D-14` / `E-1`.
# Record codes (ADR-031) are deliberately not matched.
CODE_DEF_RE = re.compile(r"\|\s*\*\*([A-Z]{1,3}-\d{1,3})\*\*\s*\|")
CODE_DEF_HEAD_RE = re.compile(r"^\s{0,3}#{1,6}\s+([A-Z]{1,3}-\d{1,3})\b")
CODE_REF_RE = re.compile(r"\b([A-Z]{1,3}-\d{1,3})\b")


def is_param_name(name):
    """camelCase / snake_case / wl15-style names are likely parameters."""
    return bool(re.fullmatch(
        r"[a-z][A-Za-z0-9_]*[A-Z][A-Za-z0-9_]*"
        r"|[a-z][a-z0-9_]*_[a-z0-9_]+"
        r"|[a-z]+[0-9]+",
        name,
    ))
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$")
DEF_SCOPE_RE = re.compile(r"是什么|定义|术语|概念|glossary", re.I)
FIELD_LABELS = {
    "定义", "类型 / 结构", "例子", "反例 / 易混", "禁用别名", "出处",
    "职责", "前置不变量", "后置不变量", "谁必须读它", "为什么它是核心",
    "它是什么", "定义域 / 规范形", "相等判据", "公共后置条件", "实现落在哪",
    "被拒方案", "危险实现清单", "它不是什么", "不写版本故事",
    "高扇入公共依赖", "架构骨架", "不变量守护者", "执行流入口",
    "AI 未见的领域核心", "收窄",
}


# 活文档软预算（行）。warning-only；--max-lines 覆盖，--no-budget 关闭。
DEFAULT_BUDGETS = (
    ("AGENTS.md", 100), ("CLAUDE.md", 100),
    (".cursorrules", 100), (".windsurfrules", 100),
    (".cursor/rules/project.mdc", 100),
    (".github/copilot-instructions.md", 100),
    ("docs/architecture.md", 80), ("docs/architecture.markdown", 80),
    ("docs/core-code.md", 200), ("docs/core-code.markdown", 200),
    ("docs/modules/*.md", 400), ("docs/modules/*.markdown", 400),
)


def budget_for(file_rel, override):
    if override is not None:
        return override
    for pattern, budget in DEFAULT_BUDGETS:
        if fnmatch.fnmatch(file_rel, pattern):
            return budget
    return None


def term_key(term):
    """Glossary cell -> primary label (drop ** and a backticked alias)."""
    t = term.replace("**", "").strip()
    if "`" in t:
        t = t.split("`", 1)[0].strip()
    return t


def parse_glossary(root):
    """Terms defined in docs/glossary.md or docs/glossary.markdown."""
    terms = set()
    for name in ("docs/glossary.md", "docs/glossary.markdown"):
        path = os.path.join(root, *name.split("/"))
        if not os.path.isfile(path):
            continue
        lines = read_lines(path)
        mask = active_mask(lines)
        for line, inactive in zip(lines, mask):
            if inactive:
                continue
            s = line.strip()
            if s.startswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if len(cells) < 2:
                    continue
                term = cells[0]
                if not term or term.startswith("---") or term.startswith("<!--") or term == "术语":
                    continue
                terms.add(term.strip("`"))
            m = DEF_RE.match(line)
            if m and m.group(1).strip() not in FIELD_LABELS:
                terms.add(m.group(1).strip())
    return terms


def numeric_segments(line):
    """Only inline code and table rows are scanned for numeric conflicts."""
    if line.strip().startswith("|"):
        return [line]
    return BACKTICK_RE.findall(line)


def parse_glossary_aliases(root):
    """Backticked identifiers listed in glossary rows (e.g. `profCoast`)."""
    aliases = set()
    for name in ("docs/glossary.md", "docs/glossary.markdown"):
        path = os.path.join(root, *name.split("/"))
        if not os.path.isfile(path):
            continue
        lines = read_lines(path)
        mask = active_mask(lines)
        for line, inactive in zip(lines, mask):
            if inactive:
                continue
            if not line.strip().startswith("|"):
                continue
            for span in re.findall(r"`([^`]+)`", line):
                for token in re.split(r"[/,，、\s]+", span):
                    if token:
                        aliases.add(token)
    return aliases


def collect(root, ignore_keys, max_lines=None, use_live=True):
    glossary_terms = parse_glossary(root)
    definitions = defaultdict(list)
    numbers = defaultdict(list)
    file_lines = {}
    module_texts = {}
    other_texts = {}
    all_texts = {}
    glossary_files = ("docs/glossary.md", "docs/glossary.markdown")

    paths = list(iter_docs(root, use_live=use_live))
    for name in ("README.md", "README.markdown"):
        path = os.path.join(root, name)
        if os.path.isfile(path) and path not in paths:
            paths.append(path)

    for path in paths:
        file_rel = rel(root, path)
        lines = read_lines(path)
        file_lines[file_rel] = len(lines)
        text = "\n".join(lines)
        if file_rel.startswith("docs/modules/"):
            module_texts[file_rel] = text
        elif file_rel not in glossary_files and not file_rel.startswith("README"):
            other_texts[file_rel] = text
        if file_rel not in glossary_files:
            all_texts[file_rel] = text
        in_docs = file_rel.startswith("docs/") and file_rel not in glossary_files
        mask = active_mask(lines)
        in_def_scope = True                     # 无小标题的文件按定义语境处理
        for lineno, (line, in_fence) in enumerate(zip(lines, mask), 1):
            if in_fence:
                continue
            heading = HEADING_RE.match(line)
            if heading:
                in_def_scope = bool(DEF_SCOPE_RE.search(heading.group(1)))
                continue
            if in_docs and in_def_scope:
                m = DEF_RE.match(line)
                if m:
                    term = m.group(1).strip()
                    if term and term not in FIELD_LABELS:
                        definitions[term].append(
                            {"file": file_rel, "line": lineno, "definition": m.group(2).strip()}
                        )
            for segment in numeric_segments(line):
                for m in NUM_RE.finditer(segment):
                    key, value = m.group(1), m.group(2)
                    if key.lower() in ignore_keys:
                        continue
                    numbers[key].append(
                        {"file": file_rel, "line": lineno, "value": value}
                    )
    return (glossary_terms, definitions, numbers, file_lines,
            module_texts, other_texts, all_texts)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings")
    ap.add_argument("--json", help="write JSON report to this path")
    ap.add_argument("--ignore", default="", help="comma-separated numeric keys to ignore")
    ap.add_argument("--ignore-alias", default="",
                    help="comma-separated glossary aliases to ignore in duplicate-alias")
    ap.add_argument("--max-lines", type=int, default=None,
                    help="override the line budget for every scanned doc")
    ap.add_argument("--no-budget", action="store_true",
                    help="disable line-budget warnings")
    ap.add_argument("--glossary-locality", action="store_true",
                    help="show single-module glossary-term candidates (coarse; review manually)")
    ap.add_argument("--min-term-mentions", type=int, default=3,
                    help="minimum mentions in one module before a term-demote hint (default 3)")
    ap.add_argument("--all-docs", action="store_true",
                    help="ignore docs/.live and scan every docs/ file (migration / audit)")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    ignore_keys = {k.strip().lower() for k in args.ignore.split(",") if k.strip()}
    ignore_aliases = {a.strip() for a in args.ignore_alias.split(",") if a.strip()}
    glossary_terms, definitions, numbers, file_lines, module_texts, other_texts, all_texts = collect(
        root, ignore_keys, None if args.no_budget else args.max_lines,
        use_live=not args.all_docs,
    )

    warnings = []
    if not args.all_docs:
        for entry in live_allowlist_missing(root):
            warnings.append({"kind": "live-missing", "entry": entry})

    for term, items in sorted(definitions.items()):
        if term in glossary_terms or len(items) > 1:
            warnings.append(
                {
                    "kind": "duplicate-definition",
                    "term": term,
                    "items": items,
                }
            )
        else:
            warnings.append(
                {
                    "kind": "unregistered-definition",
                    "term": term,
                    "items": items,
                }
            )

    for key, items in sorted(numbers.items()):
        values = sorted({item["value"] for item in items})
        if len(values) > 1:
            warnings.append(
                {
                    "kind": "numeric-conflict",
                    "key": key,
                    "values": values,
                    "items": items,
                }
            )

    # Same key=value (or key: value) in two or more live docs: a copy candidate.
    by_pair = defaultdict(list)
    for key, items in numbers.items():
        for item in items:
            by_pair[(key, item["value"])].append(item)
    for (key, value), items in sorted(by_pair.items()):
        files = sorted({item["file"] for item in items})
        if len(files) > 1:
            warnings.append(
                {
                    "kind": "duplicate-literal",
                    "key": key,
                    "value": value,
                    "items": items,
                }
            )

    # Glossary-listed parameter aliases in >=2 live docs: the same knob is
    # specified in more than one place.
    for alias in sorted(parse_glossary_aliases(root)):
        if not is_param_name(alias) or alias in ignore_aliases:
            continue
        files = sorted(f for f, text in all_texts.items() if alias in text)
        if len(files) > 1:
            warnings.append(
                {
                    "kind": "duplicate-alias",
                    "alias": alias,
                    "files": files,
                }
            )

    # Stable clause codes may be cited across live docs, but every cited code
    # must be defined somewhere: a dangling code means a rename or a retirement
    # left a rotted citation behind.
    code_defs = set()
    code_lines = defaultdict(list)
    for file_rel, text in all_texts.items():
        for lineno, line in enumerate(text.splitlines(), 1):
            m = CODE_DEF_RE.search(line) or CODE_DEF_HEAD_RE.match(line)
            if m:
                code_defs.add(m.group(1))
            for m in CODE_REF_RE.finditer(line):
                code_lines[m.group(1)].append({"file": file_rel, "line": lineno})
    families = {code.split("-")[0] for code in code_defs}
    for code, items in sorted(code_lines.items()):
        family = code.split("-")[0]
        if code in code_defs or family not in families or family == "ADR":
            continue
        warnings.append({"kind": "dangling-code", "code": code, "items": items})

    # NOTE: there is deliberately no "downward reference" check. Whether a line is
    # an index entry (legal: an upper doc lists the docs below it) or a sentence
    # placed too high cannot be told apart from the text; that judgement is a
    # review job. A proxy here fired on the legal pattern and taught readers to
    # ignore the tool.

    # Line budgets: always-loaded and per-module docs have soft caps.
    if not args.no_budget:
        for file_rel, count in sorted(file_lines.items()):
            budget = budget_for(file_rel, args.max_lines)
            if budget is not None and count > budget:
                warnings.append(
                    {
                        "kind": "over-budget",
                        "file": file_rel,
                        "lines": count,
                        "budget": budget,
                    }
                )

    # A glossary term used in exactly one module is a demotion candidate.
    if args.glossary_locality:
        for term in sorted(glossary_terms):
            key = term_key(term)
            if not key:
                continue
            users = [m for m, text in module_texts.items()
                     if text.count(key) >= args.min_term_mentions]
            if len(users) != 1:
                continue
            module = users[0]
            mentions = module_texts[module].count(key)
            # A one-line pointer elsewhere does not make it cross-module.
            if any(text.count(key) >= args.min_term_mentions
                   for text in other_texts.values()):
                continue
            warnings.append(
                {
                    "kind": "term-demote",
                    "term": key,
                    "module": module,
                    "mentions": mentions,
                }
            )

    for warning in warnings:
        kind = warning["kind"]
        if kind == "duplicate-definition":
            print("[duplicate-definition] {}:".format(warning["term"]))
            for item in warning["items"]:
                print("  {}:{}  {}".format(item["file"], item["line"], item["definition"]))
        elif kind == "unregistered-definition":
            print("[unregistered-definition] {}:".format(warning["term"]))
            for item in warning["items"]:
                print("  {}:{}  {}".format(item["file"], item["line"], item["definition"]))
        elif kind == "numeric-conflict":
            print("[numeric-conflict] {}: {}".format(warning["key"], ", ".join(warning["values"])))
            for item in warning["items"]:
                print("  {}:{}  = {}".format(item["file"], item["line"], item["value"]))
        elif kind == "duplicate-literal":
            print("[duplicate-literal] {}={}:".format(warning["key"], warning["value"]))
            for item in warning["items"]:
                print("  {}:{}".format(item["file"], item["line"]))
        elif kind == "duplicate-alias":
            print("[duplicate-alias] {}: {}".format(
                warning["alias"], ", ".join(warning["files"])))
        elif kind == "dangling-code":
            print("[dangling-code] {}: cited but never defined".format(warning["code"]))
            for item in warning["items"]:
                print("  {}:{}".format(item["file"], item["line"]))
        elif kind == "over-budget":
            print("[over-budget] {}: {} lines > budget {}".format(
                warning["file"], warning["lines"], warning["budget"]))
        elif kind == "term-demote":
            print("[term-demote] {}: only in {} ({} mentions); "
                  "move it to that module's term section unless a second module "
                  "uses it as a rule/criterion".format(
                      warning["term"], warning["module"], warning["mentions"]))
        elif kind == "live-missing":
            print("[live-missing] docs/.live lists {} but the file does not exist".format(
                warning["entry"]))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"warnings": warnings}, f, ensure_ascii=False, indent=2)

    if not warnings:
        print("[check-consistency] no consistency warnings found.")
    else:
        print("[check-consistency] {} warning(s); heuristic only, confirm before editing.".format(len(warnings)))

    return 1 if (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
