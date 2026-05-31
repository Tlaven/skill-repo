"""
core/locator.py — The single source of truth for content-based addressing.

This module eliminates the massive duplication of by_text / after_text / chapter resolution
that existed across the original codebase.

All mutation and high-level operations should go through Locator → Anchor resolution.
"""

from typing import Optional
import re

from .types import Locator, Anchor, ParagraphInfo, SectionNode


def _norm_title(s: str) -> str:
    """Aggressive normalization for real Chinese academic thesis titles."""
    s = re.sub(r'^[\d.、\s　]+', '', s).strip()
    s = re.sub(r'^(第[一二三四五六七八九十百]+章|第[\d]+章)\s*', '', s)
    s = re.sub(r'^(基于|改进|一种|面向).+的', '', s)
    return s.lower().strip()


# Common synonym groups for Chinese thesis section titles.
# If normalized query and normalized title land in the same group, treat as match.
SECTION_TITLE_SYNONYMS: list[set[str]] = [
    {"引言", "绪论"},
    {"相关工作", "国内外研究现状", "文献综述", "研究现状", "相关研究"},
    {"实验结果", "实验与结果", "结果与分析", "实验设计与结果分析", "实验结果与分析", "实验与分析"},
    {"方法", "算法设计", "模型设计", "方法设计", "技术路线"},
    {"结论", "结论与展望", "总结"},
    {"摘要", "中英文摘要"},
]


def _titles_match(query: str, title: str) -> bool:
    """Return True if query and title should be considered the same section title."""
    if not query or not title:
        return False

    q = query.strip()
    t = title.strip()

    # Direct / contains (original)
    if q in t or t in q:
        return True

    q_lower = q.lower()
    t_lower = t.lower()
    if q_lower in t_lower or t_lower in q_lower:
        return True

    qn = _norm_title(q)
    tn = _norm_title(t)

    if qn and tn and (qn in tn or tn in qn):
        return True

    # Synonym group matching (the powerful part for real theses)
    for group in SECTION_TITLE_SYNONYMS:
        q_in_group = any(qn in g or g in qn or q_lower in g or g in q_lower for g in group)
        t_in_group = any(tn in g or g in tn or t_lower in g or g in t_lower for g in group)
        if q_in_group and t_in_group:
            return True

    return False


def _find_section_by_chapter_path(sections: list[SectionNode], target: str) -> Optional[SectionNode]:
    """
    Recursively search the entire SectionNode tree (including all children)
    for a node whose chapter_path matches the target.

    This is the key fix for deep chapters like "4.1.1" returning rich SectionNode.
    """
    for sec in sections:
        if sec.chapter_path == target or sec.chapter_path.startswith(target + "."):
            return sec
        if sec.children:
            found = _find_section_by_chapter_path(sec.children, target)
            if found:
                return found
    return None


def resolve(
    locator: Locator | str,
    paragraphs: list[ParagraphInfo],
    sections: list[SectionNode],
    images: list = None,
    tables: list = None,
    formulas: list = None,
    references: list = None,
) -> Optional[Anchor]:
    """
    Resolve a Locator (or simple string) into a stable Anchor.

    This is the central function that replaces all the scattered resolution logic
    from the original api.py / editor.py / commands.
    """
    if isinstance(locator, str):
        locator = Locator(kind="text", value=locator)

    if locator.kind in ("text", "by_text"):
        if not locator.value:
            return None
        for p in paragraphs:
            if locator.value in p.text:
                return Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path
                )
        return None

    if locator.kind == "after_text":
        if not locator.value:
            return None
        for i, p in enumerate(paragraphs):
            if locator.value in p.text:
                if i + 1 < len(paragraphs):
                    next_p = paragraphs[i + 1]
                    return Anchor(
                        kind="paragraph",
                        paragraph_index=next_p.index,
                        text_snippet=next_p.text[:80],
                        chapter_path=next_p.chapter_path
                    )
        return None

    if locator.kind == "before_text":
        if not locator.value:
            return None
        for i, p in enumerate(paragraphs):
            if locator.value in p.text:
                if i > 0:
                    prev_p = paragraphs[i - 1]
                    return Anchor(
                        kind="paragraph",
                        paragraph_index=prev_p.index,
                        text_snippet=prev_p.text[:80],
                        chapter_path=prev_p.chapter_path
                    )
        return None

    if locator.kind in ("chapter", "chapter_path"):
        target = str(locator.value or "").strip()
        if not target:
            return None

        # Prefer rich SectionNode by recursively searching the entire tree.
        # This is the critical fix so that deep chapters (e.g. "4.1.1") can return
        # proper SectionNode instead of falling back to a plain paragraph.
        sec = _find_section_by_chapter_path(sections, target)
        if sec:
            return Anchor(
                kind="section",
                section=sec,
                paragraph_index=sec.para_range[0],
                chapter_path=sec.chapter_path,
                text_snippet=(sec.title[:80] if sec.title else None),
            )

        # Fallback: first paragraph belonging to that chapter (still useful)
        for p in paragraphs:
            cp = p.chapter_path
            if cp == target or cp.startswith(target + "."):
                return Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path
                )
        return None

    if locator.kind in ("section_title", "section", "title"):
        query = str(locator.value or "").strip()
        if not query:
            return None

        # Recursive search across the entire tree so deep sections can also be found by title.
        def _find_section_by_title(sections: list[SectionNode], q: str, qn: str) -> Optional[SectionNode]:
            for sec in sections:
                if _titles_match(q, sec.title):
                    return sec

                if sec.children:
                    found = _find_section_by_title(sec.children, q, qn)
                    if found:
                        return found
            return None

        qn = _norm_title(query)
        sec = _find_section_by_title(sections, query, qn)
        if sec:
            return Anchor(
                kind="section",
                section=sec,
                paragraph_index=sec.para_range[0],
                chapter_path=sec.chapter_path,
                text_snippet=sec.title[:80],
            )

        # Final fallback to paragraph-level heading text
        for p in paragraphs:
            if query in p.text and p.level is not None:
                return Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path
                )
        return None

    if locator.kind == "paragraph_range" and locator.start is not None:
        # For now we just return the start paragraph as anchor
        if 0 <= locator.start < len(paragraphs):
            p = paragraphs[locator.start]
            return Anchor(
                kind="paragraph",
                paragraph_index=p.index,
                text_snippet=p.text[:80],
                chapter_path=p.chapter_path
            )
        return None

    # Revisions support — Phase 1 minimal (user-accepted design)
    if locator.kind in ("has_revision", "revision"):
        for p in paragraphs:
            if p.has_revisions:
                return Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path,
                )
        return None

    if locator.kind == "revision_type" and locator.value:
        target_type = str(locator.value).lower()
        for p in paragraphs:
            if target_type in p.revision_types:
                return Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path,
                )
        return None

    if locator.kind == "revision_author" and locator.value:
        target_author = str(locator.value)
        for p in paragraphs:
            if target_author in p.revision_authors:
                return Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path,
                )
        return None

    # E1 basic support for images and tables
    if locator.kind == "image" and images is not None:
        query = str(locator.value or "").lower().strip() if locator.value else ""
        for img in images:
            if query:
                if query in (img.caption or "").lower() or query in (img.chapter_path or ""):
                    return Anchor(
                        kind="image",
                        paragraph_index=img.para_index,
                        text_snippet=img.caption or img.filename,
                        chapter_path=img.chapter_path,
                        media_index=images.index(img) if img in images else None
                    )
            else:
                return Anchor(
                    kind="image",
                    paragraph_index=img.para_index,
                    text_snippet=img.caption or img.filename,
                    chapter_path=img.chapter_path,
                    media_index=images.index(img),
                )
        return None

    if locator.kind == "table" and tables is not None:
        query = str(locator.value or "").lower().strip() if locator.value else ""
        for tbl in tables:
            if query:
                if query in (tbl.caption or "").lower() or query in (tbl.chapter_path or ""):
                    return Anchor(
                        kind="table",
                        paragraph_index=tbl.para_index,
                        text_snippet=tbl.caption,
                        chapter_path=tbl.chapter_path,
                        media_index=tables.index(tbl) if tbl in tables else None
                    )
            else:
                return Anchor(
                    kind="table",
                    paragraph_index=tbl.para_index,
                    text_snippet=tbl.caption,
                    chapter_path=tbl.chapter_path,
                    media_index=tables.index(tbl),
                )
        return None

    if locator.kind == "formula" and formulas is not None:
        query = str(locator.value or "").strip() if locator.value else ""
        for f in formulas:
            if query:
                if query in (f.equation_number or "") or query in f.chapter_path:
                    return Anchor(
                        kind="formula",
                        paragraph_index=f.para_index,
                        text_snippet=f.content[:80] or f.equation_number,
                        chapter_path=f.chapter_path,
                        media_index=formulas.index(f),
                    )
            else:
                return Anchor(
                    kind="formula",
                    paragraph_index=f.para_index,
                    text_snippet=f.content[:80] or f.equation_number,
                    chapter_path=f.chapter_path,
                    media_index=formulas.index(f),
                )
        return None

    if locator.kind == "reference" and references is not None:
        val = locator.value
        if val is not None and (isinstance(val, int) or str(val).isdigit()):
            target = int(val)
            for r in references:
                if r.index == target:
                    return Anchor(
                        kind="reference",
                        paragraph_index=r.para_index,
                        text_snippet=r.text[:80],
                        chapter_path=r.chapter_path,
                    )
            return None
        query = str(val or "").lower().strip() if val else ""
        for r in references:
            if not query or query in r.text.lower():
                return Anchor(
                    kind="reference",
                    paragraph_index=r.para_index,
                    text_snippet=r.text[:80],
                    chapter_path=r.chapter_path,
                )
        return None

    return None


def resolve_all(
    locator: Locator | str,
    paragraphs: list[ParagraphInfo],
    sections: list[SectionNode],
    images: list = None,
    tables: list = None,
    formulas: list = None,
    references: list = None,
) -> list[Anchor]:
    """
    Resolve a Locator into ALL matching Anchors (unlike resolve() which returns first match).
    Use for compound words like image-list-all, paragraph-find-all, etc.
    """
    if isinstance(locator, str):
        locator = Locator(kind="text", value=locator)

    results: list[Anchor] = []

    if locator.kind in ("text", "by_text"):
        if not locator.value:
            return results
        for p in paragraphs:
            if locator.value in p.text:
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path
                ))
        return results

    if locator.kind == "after_text":
        if not locator.value:
            return results
        for i, p in enumerate(paragraphs):
            if locator.value in p.text and i + 1 < len(paragraphs):
                next_p = paragraphs[i + 1]
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=next_p.index,
                    text_snippet=next_p.text[:80],
                    chapter_path=next_p.chapter_path
                ))
        return results

    if locator.kind == "before_text":
        if not locator.value:
            return results
        for i, p in enumerate(paragraphs):
            if locator.value in p.text and i > 0:
                prev_p = paragraphs[i - 1]
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=prev_p.index,
                    text_snippet=prev_p.text[:80],
                    chapter_path=prev_p.chapter_path
                ))
        return results

    if locator.kind in ("chapter", "chapter_path"):
        target = str(locator.value or "").strip()
        if not target:
            return results
        for p in paragraphs:
            cp = p.chapter_path
            if cp == target or cp.startswith(target + "."):
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path
                ))
        return results

    if locator.kind in ("section_title", "section", "title"):
        query = str(locator.value or "").strip()
        if not query:
            return results
        qn = _norm_title(query)
        for sec in sections:
            if _titles_match(query, sec.title):
                results.append(Anchor(
                    kind="section",
                    section=sec,
                    paragraph_index=sec.para_range[0],
                    chapter_path=sec.chapter_path,
                    text_snippet=sec.title[:80],
                ))
        for p in paragraphs:
            if query in p.text and p.level is not None:
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path
                ))
        return results

    if locator.kind == "paragraph_range" and locator.start is not None:
        if 0 <= locator.start < len(paragraphs):
            p = paragraphs[locator.start]
            results.append(Anchor(
                kind="paragraph",
                paragraph_index=p.index,
                text_snippet=p.text[:80],
                chapter_path=p.chapter_path
            ))
        return results

    if locator.kind in ("has_revision", "revision"):
        for p in paragraphs:
            if p.has_revisions:
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path,
                ))
        return results

    if locator.kind == "revision_type" and locator.value:
        target_type = str(locator.value).lower()
        for p in paragraphs:
            if target_type in p.revision_types:
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path,
                ))
        return results

    if locator.kind == "revision_author" and locator.value:
        target_author = str(locator.value)
        for p in paragraphs:
            if target_author in p.revision_authors:
                results.append(Anchor(
                    kind="paragraph",
                    paragraph_index=p.index,
                    text_snippet=p.text[:80],
                    chapter_path=p.chapter_path,
                ))
        return results

    if locator.kind == "image" and images is not None:
        query = str(locator.value or "").lower().strip() if locator.value else ""
        for img in images:
            if query:
                if query in (img.caption or "").lower() or query in (img.chapter_path or ""):
                    results.append(Anchor(
                        kind="image",
                        paragraph_index=img.para_index,
                        text_snippet=img.caption or img.filename,
                        chapter_path=img.chapter_path,
                        media_index=images.index(img) if img in images else None
                    ))
            else:
                results.append(Anchor(
                    kind="image",
                    paragraph_index=img.para_index,
                    text_snippet=img.caption or img.filename,
                    chapter_path=img.chapter_path,
                ))
        return results

    if locator.kind == "table" and tables is not None:
        query = str(locator.value or "").lower().strip() if locator.value else ""
        for tbl in tables:
            if query:
                if query in (tbl.caption or "").lower() or query in (tbl.chapter_path or ""):
                    results.append(Anchor(
                        kind="table",
                        paragraph_index=tbl.para_index,
                        text_snippet=tbl.caption,
                        chapter_path=tbl.chapter_path,
                        media_index=tables.index(tbl) if tbl in tables else None
                    ))
            else:
                results.append(Anchor(
                    kind="table",
                    paragraph_index=tbl.para_index,
                    text_snippet=tbl.caption,
                    chapter_path=tbl.chapter_path,
                ))
        return results

    if locator.kind == "formula" and formulas is not None:
        query = str(locator.value or "").strip() if locator.value else ""
        for f in formulas:
            if query:
                if query in (f.equation_number or "") or query in f.chapter_path:
                    results.append(Anchor(
                        kind="formula",
                        paragraph_index=f.para_index,
                        text_snippet=f.content[:80] or f.equation_number,
                        chapter_path=f.chapter_path,
                        media_index=formulas.index(f),
                    ))
            else:
                results.append(Anchor(
                    kind="formula",
                    paragraph_index=f.para_index,
                    text_snippet=f.content[:80] or f.equation_number,
                    chapter_path=f.chapter_path,
                ))
        return results

    if locator.kind == "reference" and references is not None:
        val = locator.value
        if val is not None and (isinstance(val, int) or str(val).isdigit()):
            target = int(val)
            for r in references:
                if r.index == target:
                    results.append(Anchor(
                        kind="reference",
                        paragraph_index=r.para_index,
                        text_snippet=r.text[:80],
                        chapter_path=r.chapter_path,
                    ))
            return results
        query = str(val or "").lower().strip() if val else ""
        for r in references:
            if not query or query in r.text.lower():
                results.append(Anchor(
                    kind="reference",
                    paragraph_index=r.para_index,
                    text_snippet=r.text[:80],
                    chapter_path=r.chapter_path,
                ))
        return results

    return results


def to_locator(obj: str | dict | Locator) -> Locator:
    """Convenience converter for ergonomic usage."""
    if isinstance(obj, Locator):
        return obj
    if isinstance(obj, str):
        return Locator(kind="text", value=obj)
    if isinstance(obj, dict):
        return Locator(**obj)
    raise TypeError(f"Cannot convert {type(obj)} to Locator")
