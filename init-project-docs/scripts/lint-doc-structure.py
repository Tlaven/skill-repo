#!/usr/bin/env python3
"""lint-doc-structure.py — structural readability warnings (never a hard gate).

Warnings:
- a paragraph longer than --max-paragraph-lines (default 20; a 10–20 line main
  flow is the documented target, so 20 is the warning threshold)
- a long document with no `## ` headings
- a long document with no examples/structure (no fenced code, table, or list)
"""

import argparse
import json
import os
import re
import sys

from _doc_common import active_mask, iter_docs, read_lines, rel

LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")


def is_break(line, in_fence):
    s = line.strip()
    return (
        in_fence
        or not s
        or s.startswith("#")
        or s.startswith("|")
        or s.startswith(">")
        or LIST_RE.match(line) is not None
    )


def check_file(root, path, max_paragraph_lines):
    lines = read_lines(path)
    mask = active_mask(lines)
    warnings = []

    run = 0
    start = 0
    for lineno, (line, in_fence) in enumerate(zip(lines, mask), 1):
        if is_break(line, in_fence):
            if run > max_paragraph_lines:
                warnings.append(
                    {
                        "file": rel(root, path),
                        "line": start,
                        "kind": "long-paragraph",
                        "detail": "{} lines without a break".format(run),
                    }
                )
            run = 0
            start = 0
        else:
            if run == 0:
                start = lineno
            run += 1
    if run > max_paragraph_lines:
        warnings.append(
            {
                "file": rel(root, path),
                "line": start,
                "kind": "long-paragraph",
                "detail": "{} lines without a break".format(run),
            }
        )

    if len(lines) > 20:
        has_heading = any(line.strip().startswith("## ") for line in lines)
        has_example = any(
            line.strip().startswith(("```", "~~~", "|"))
            or LIST_RE.match(line) is not None
            for line in lines
        )
        if not has_heading:
            warnings.append(
                {
                    "file": rel(root, path),
                    "line": 1,
                    "kind": "no-headings",
                    "detail": "long document with no `## ` headings",
                }
            )
        if not has_example:
            warnings.append(
                {
                    "file": rel(root, path),
                    "line": 1,
                    "kind": "no-examples",
                    "detail": "long document with no code block / table / list",
                }
            )

    return warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--max-paragraph-lines", type=int, default=20)
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings")
    ap.add_argument("--json", help="write JSON report to this path")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    warnings = []
    for path in iter_docs(root):
        warnings.extend(check_file(root, path, args.max_paragraph_lines))

    for warning in warnings:
        print(
            "[{kind}] {file}:{line}  {detail}".format(**warning)
        )

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"warnings": warnings}, f, ensure_ascii=False, indent=2)

    if not warnings:
        print("[lint-doc-structure] no structural warnings.")
    else:
        print(
            "[lint-doc-structure] {} warning(s); readability judgment still needs review.".format(
                len(warnings)
            )
        )

    return 1 if (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
