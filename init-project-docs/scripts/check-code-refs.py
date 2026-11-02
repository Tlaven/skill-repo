#!/usr/bin/env python3
"""check-code-refs.py — check inline code path/file references in current docs.

Scope: `docs/` (minus reviews/decisions/legacy/archive/templates) + L1 files.
Records (`docs/reviews/`, `docs/decisions/`) are history and may cite deleted
files — they are not scanned (a record's dead link is evidence, not drift).
Checks backticked tokens that look like paths or filenames:
  - contains `/`, or has a known file extension
  - skips URLs, placeholders (`<…>`, `…`), globs, backslashes, fenced code blocks
  - bare extensions (`.sh`) and alternative L1 host names (`CLAUDE.md`) are skipped
  - only known path prefixes or file extensions are treated as paths
    (`读/写`, `py/js`, `N0/N1` are prose, not paths); a no-slash token must be
    ASCII — `父.h` / `邻.h` are identifiers, not filenames
  - a leading `/` is treated as repo-relative
  - missing on-demand docs (`docs/architecture.md|.markdown`, `docs/glossary.*`,
    `docs/core-analysis.*`, `docs/experiment/scaffolds/`, `docs/modules/…`, `docs/decisions/…`,
    `docs/reviews/…`, `docs/templates/`) and `task_plan.md` are reported as
    `pending-doc`, not as errors (they are created later by design).
Exit 1 only with --strict when real findings exist.
"""

import argparse
import json
import os
import re
import sys

from _doc_common import L1_NAMES, N2_L2_DOCS, active_mask, iter_docs, read_lines, rel

TOKEN_RE = re.compile(r"`([^`\n]+)`")
EXT_RE = re.compile(
    r"\.(md|markdown|py|sh|ps1|js|jsx|mjs|cjs|ts|tsx|json|ya?ml|toml|txt|csv|"
    r"html|css|java|go|rs|c|cc|cpp|h|hpp|rb|php|cs|swift|kt|lua|sql|ini|cfg|conf|env|lock)$",
    re.I,
)
BARE_EXT_RE = re.compile(r"^\.[A-Za-z0-9]+$")
PATH_RE = re.compile(r"^[A-Za-z0-9_.@+-]+(?:/[A-Za-z0-9_.@+-]+)+$")
NAME_RE = re.compile(r"^[A-Za-z0-9_.@+-]+$")
PATH_PREFIXES = (
    "docs/", "docs-templates/", "scripts/", "src/", "tests/", "test/", "lib/",
    "app/", "packages/", "config/", "assets/", "public/", "bin/", "tools/",
    "spec/", "cmd/", "internal/", "pkg/", "include/",
)
PENDING_DOCS = (
    *N2_L2_DOCS,
    "docs/glossary.md",
    "docs/glossary.markdown",
    "docs/core-analysis.md",
    "docs/core-analysis.markdown",
    "docs/design-contract.md",
    "docs/design-contract.markdown",
    "docs/n2-acceptance.json",
    "docs/.live",
    "docs/experiment/scaffolds",
    "docs/scaffolds",  # 旧路径:只容忍,规范落点是 docs/experiment/scaffolds/
    "docs/modules",
    "docs/decisions",
    "docs/reviews",
    "docs/templates",
)
PENDING_NAMES = ("task_plan.md",)


def candidates(token):
    token = token.strip().rstrip(".,;:)")
    token = token.split("#", 1)[0]
    token = re.split(r":\d+", token)[0]
    if not token or any(ch in token for ch in " \t"):
        return []
    if token.startswith(("http://", "https://", "mailto:", "#", "~", "<")):
        return []
    token = token.rstrip("/")
    if not token:
        return []
    if any(ch in token for ch in "*?{}[]\\<>…"):
        return []
    if token in L1_NAMES or BARE_EXT_RE.match(token):
        return []
    if token.startswith("/"):
        return [token.lstrip("/")]

    has_slash = "/" in token
    has_ext = bool(EXT_RE.search(token))
    if has_slash:
        if not PATH_RE.match(token):
            return []
        if not has_ext and not token.startswith(PATH_PREFIXES):
            return []
    elif not has_ext:
        return []
    elif not NAME_RE.match(token):
        return []                       # `父.h` / `邻.h`: identifier, not a filename

    out = [token]
    if not has_slash:
        out.append(os.path.join("scripts", token))
    if token.startswith("scripts/") and not has_ext:
        out.extend([token + ".sh", token + ".ps1", token + ".py"])
    return out


def is_pending_doc(token, tried):
    if token in PENDING_NAMES:
        return True
    for candidate in [token] + list(tried):
        if candidate.startswith(PENDING_DOCS):
            return True
    return False


def check(root):
    findings = []
    pending = []
    for path in iter_docs(root):
        lines = read_lines(path)
        mask = active_mask(lines)
        for lineno, (line, in_fence) in enumerate(zip(lines, mask), 1):
            if in_fence:
                continue
            for match in TOKEN_RE.finditer(line):
                token = match.group(1).strip()
                tried = candidates(token)
                if not tried:
                    continue
                found = False
                for candidate in tried:
                    if os.path.exists(os.path.join(root, candidate)) or os.path.exists(
                        os.path.join(os.path.dirname(path), candidate)
                    ):
                        found = True
                        break
                if found:
                    continue
                item = {
                    "file": rel(root, path),
                    "line": lineno,
                    "token": token,
                    "tried": tried,
                }
                if is_pending_doc(token, tried):
                    pending.append(item)
                else:
                    findings.append(item)
    return findings, pending


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on real findings (pending docs do not fail)")
    ap.add_argument("--json", help="write JSON report to this path")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    findings, pending = check(root)

    for item in findings:
        print(
            "[missing-ref] {}:{} `{}` (tried: {})".format(
                item["file"], item["line"], item["token"], ", ".join(item["tried"])
            )
        )
    for item in pending:
        print("[pending-doc] {}:{} `{}` (created on demand; not an error)".format(
            item["file"], item["line"], item["token"]
        ))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"findings": findings, "pending": pending}, f, ensure_ascii=False, indent=2)

    if not findings:
        print("[check-code-refs] no missing inline code references ({} pending doc reference(s)).".format(len(pending)))
    else:
        print("[check-code-refs] {} missing reference(s); {} pending doc(s); semantic claims still need review.".format(
            len(findings), len(pending)
        ))

    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
