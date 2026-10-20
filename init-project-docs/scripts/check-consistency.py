#!/usr/bin/env python3
"""check-consistency.py — heuristic warnings for duplicate definitions / numeric conflicts.

This is a WARNING tool: it does not decide truth, and should not be a hard gate.
- Duplicate term definitions: a `- **term**: ...` definition in `docs/` that
  redefines a glossary term, or appears more than once.
- Unregistered definitions: a `- **term**: ...` definition in `docs/`
  whose term is not in docs/glossary.md.
- Numeric conflicts: the same key written with different values inside inline
  code or table cells (prose is ignored to keep noise low).
Records (`docs/decisions/`, `docs/reviews/`) are history, not current docs:
they are not scanned (ADR option names / rationale bullets are not terms).
Definition scanning is limited to sections whose heading names a definition
scope (`是什么 / 定义 / 术语 / 概念`) or to files with no heading at all —
`[为什么]` / `[不变量]` bullets are rationale and never term definitions.
L1 files are not scanned for `- **term**` definitions: emphasis bullets there
are not term definitions.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

from _doc_common import active_mask, iter_docs, read_lines, rel

DEF_RE = re.compile(r"^\s*[-*]\s+\*\*([^*]+?)\*\*\s*[:：]\s*(.+)$")
NUM_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_.]{2,})\s*[:=]\s*(\d+(?:\.\d+)?)\b")
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


def parse_glossary(root):
    """Terms defined in docs/glossary.md (table rows; bullet terms if used)."""
    path = os.path.join(root, "docs", "glossary.md")
    terms = set()
    if not os.path.isfile(path):
        return terms
    for line in read_lines(path):
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


def collect(root, ignore_keys):
    glossary_terms = parse_glossary(root)
    definitions = defaultdict(list)
    numbers = defaultdict(list)
    for path in iter_docs(root):
        file_rel = rel(root, path)
        in_docs = file_rel.startswith("docs/") and file_rel != "docs/glossary.md"
        lines = read_lines(path)
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
    return glossary_terms, definitions, numbers


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings")
    ap.add_argument("--json", help="write JSON report to this path")
    ap.add_argument("--ignore", default="", help="comma-separated numeric keys to ignore")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    ignore_keys = {k.strip().lower() for k in args.ignore.split(",") if k.strip()}
    glossary_terms, definitions, numbers = collect(root, ignore_keys)

    warnings = []

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

    for warning in warnings:
        if warning["kind"] == "duplicate-definition":
            print("[duplicate-definition] {}:".format(warning["term"]))
            for item in warning["items"]:
                print("  {}:{}  {}".format(item["file"], item["line"], item["definition"]))
        elif warning["kind"] == "unregistered-definition":
            print("[unregistered-definition] {}:".format(warning["term"]))
            for item in warning["items"]:
                print("  {}:{}  {}".format(item["file"], item["line"], item["definition"]))
        else:
            print("[numeric-conflict] {}: {}".format(warning["key"], ", ".join(warning["values"])))
            for item in warning["items"]:
                print("  {}:{}  = {}".format(item["file"], item["line"], item["value"]))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"warnings": warnings}, f, ensure_ascii=False, indent=2)

    if not warnings:
        print("[check-consistency] no duplicate definitions or numeric conflicts found.")
    else:
        print("[check-consistency] {} warning(s); heuristic only, confirm before editing.".format(len(warnings)))

    return 1 if (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
