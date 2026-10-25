"""Shared helpers for init-project-docs checkers (standard library only)."""

import os

L1_NAMES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    ".cursor/rules/project.mdc",
    ".windsurfrules",
    ".github/copilot-instructions.md",
)

# 对账忽略:历史快照、存档层、待填件目录、记录类文档
# decisions/ 与 reviews/ 同为记录(历史真相源,不与现状同步):扫"现状"的检查器一律不碰。
DEFAULT_EXCLUDE = (
    "docs/reviews/",
    "docs/decisions/",
    "docs/legacy/",
    "docs/archive/",
    "docs/experiment/",
    "docs/scaffolds/",
    "docs/templates/",
    "docs-templates/",
)


def _excluded(rel_dir):
    return any(rel_dir == ex.rstrip("/") or rel_dir.startswith(ex) for ex in DEFAULT_EXCLUDE)


def read_live_allowlist(root):
    """Read docs/.live, or None when the project has no allowlist.

    One path per line, relative to docs/; '#' comments and blank lines are
    ignored. A leading './' or 'docs/' is tolerated. Parent traversal is
    ignored (the allowlist is for docs/, not arbitrary files).
    """
    path = os.path.join(root, "docs", ".live")
    if not os.path.isfile(path):
        return None
    entries = []
    for line in read_lines(path):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = s.replace("\\", "/")
        if s.startswith("./"):
            s = s[2:]
        if s.startswith("docs/"):
            s = s[5:]
        if not s or s.startswith("..") or "/../" in s:
            continue
        entries.append(s)
    return entries


def live_allowlist_paths(root):
    entries = read_live_allowlist(root)
    if entries is None:
        return None
    docs = os.path.join(root, "docs")
    paths = []
    for entry in entries:
        paths.append(os.path.normpath(os.path.join(docs, *entry.split("/"))))
    return paths


def live_allowlist_missing(root):
    """Entries in docs/.live that do not point to a readable file."""
    entries = read_live_allowlist(root)
    if entries is None:
        return []
    docs = os.path.join(root, "docs")
    missing = []
    for entry in entries:
        path = os.path.normpath(os.path.join(docs, *entry.split("/")))
        if not os.path.isfile(path):
            missing.append(entry)
    return missing


def iter_docs(root, use_live=True):
    """Yield current docs: docs/.live when present, else docs/ minus excluded; + L1.

    A project without docs/.live keeps the old behaviour, so existing projects
    are not broken. With docs/.live, only the allowlisted docs count as
    current; everything else is history/reference and is skipped.
    """
    docs = os.path.join(root, "docs")
    allowed = live_allowlist_paths(root) if use_live else None
    if allowed is not None:
        for path in allowed:
            if os.path.isfile(path) and path.endswith((".md", ".markdown")):
                yield path
    elif os.path.isdir(docs):
        for dirpath, dirnames, filenames in os.walk(docs):
            rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
            if _excluded(rel_dir):
                dirnames[:] = []
                continue
            dirnames[:] = sorted(
                d for d in dirnames
                if not _excluded((rel_dir + "/" + d).replace("./", ""))
            )
            for fn in sorted(filenames):
                if fn.endswith((".md", ".markdown")):
                    yield os.path.join(dirpath, fn)
    for name in L1_NAMES:
        path = os.path.join(root, *name.split("/"))
        if os.path.isfile(path):
            yield path


def read_lines(path):
    # utf-8-sig tolerates a BOM (PowerShell 5.1 UTF-8 output); without it the
    # first heading can be missed by structural checks.
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read().splitlines()


def fenced_mask(lines):
    """True for lines inside or delimiting a fenced code block."""
    mask = []
    in_fence = False
    fence = None
    for line in lines:
        s = line.strip()
        if not in_fence and (s.startswith("```") or s.startswith("~~~")):
            in_fence = True
            fence = s[:3]
            mask.append(True)
            continue
        if in_fence and s.startswith(fence):
            in_fence = False
            fence = None
            mask.append(True)
            continue
        mask.append(in_fence)
    return mask


def comment_mask(lines):
    """True for lines inside or opening an HTML comment.

    Template examples live in HTML comments; checkers must not treat them as
    live docs (the shell check-doc-refs strips comments for the same reason).
    """
    mask = []
    in_comment = False
    for line in lines:
        if in_comment:
            mask.append(True)
            if "-->" in line:
                in_comment = False
            continue
        if "<!--" in line:
            mask.append(True)
            if "-->" not in line.split("<!--", 1)[1]:
                in_comment = True
            continue
        mask.append(False)
    return mask


def active_mask(lines):
    """True for lines that should not be scanned (fenced code or HTML comment)."""
    return [f or c for f, c in zip(fenced_mask(lines), comment_mask(lines))]


def rel(root, path):
    return os.path.relpath(path, root).replace("\\", "/")
