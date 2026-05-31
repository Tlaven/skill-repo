"""
core/reference.py — Reference write operations.

Mixin for SafeDocument. Provides add/remove/renumber/citation-scan
operations for the bibliography section of Chinese theses.
"""

from __future__ import annotations
import re
from typing import Optional

from .types import Anchor, ParagraphInfo


class ReferenceMixin:

    def _find_ref_section_range(self) -> tuple[int, int] | None:
        """Find the paragraph range [start, end) of the reference section."""
        paras = self.model._paragraphs
        ref_start = None
        for p in paras:
            if p.level is not None and p.level <= 2 and '参考文献' in p.text:
                ref_start = p.index
                break
        if ref_start is None:
            return None

        ref_end = len(paras)
        for i in range(ref_start + 1, len(paras)):
            if paras[i].level is not None and paras[i].level <= 2:
                ref_end = i
                break

        return (ref_start, ref_end)

    def _find_last_ref_index(self) -> int | None:
        range_ = self._find_ref_section_range()
        if range_ is None:
            return None
        _, ref_end = range_
        refs = self.model._references
        if not refs:
            return None
        last = refs[-1]
        if last.para_index < ref_end:
            return last.para_index
        return None

    def add_reference(self, text: str, ref_type: str | None = None) -> bool:
        """Append a reference entry at the end of the bibliography section.

        Automatically assigns the next sequential [N] number.
        Returns True on success.
        """
        ref_range = self._find_ref_section_range()
        if ref_range is None:
            return False
        ref_start, ref_end = ref_range

        # Determine next number
        next_num = 1
        for r in self.model._references:
            if r.index >= next_num:
                next_num = r.index + 1

        # Find insertion point
        insert_after = ref_end - 1
        last_idx = self._find_last_ref_index()
        if last_idx is not None:
            insert_after = last_idx

        target_para = self.model._doc.paragraphs[insert_after]
        new_text = f"[{next_num}] {text}"
        new_p = self.model._doc.add_paragraph(new_text)
        target_para._element.addnext(new_p._element)

        # Update model (full rebuild to pick up new paragraph)
        self.model._build_indexes()
        return True

    def remove_reference(self, index: int) -> bool:
        """Remove a reference entry by its [N] number. Renumbers subsequent entries."""
        target = None
        for r in self.model._references:
            if r.index == index:
                target = r
                break
        if target is None:
            return False

        idx = target.para_index
        if idx < 0 or idx >= len(self.model._doc.paragraphs):
            return False

        p = self.model._doc.paragraphs[idx]
        p._element.getparent().remove(p._element)

        self.model._build_indexes()
        self._renumber_reference_paragraphs()
        self.model._build_indexes()
        return True

    def _renumber_reference_paragraphs(self):
        """Rewrite [N] prefixes in reference section paragraphs sequentially."""
        for i, r in enumerate(self.model._references, start=1):
            if r.index == i:
                continue
            idx = r.para_index
            if idx < 0 or idx >= len(self.model._doc.paragraphs):
                continue
            para = self.model._doc.paragraphs[idx]
            old_text = para.text
            new_text = re.sub(r'^\[\d+\]', f'[{i}]', old_text)
            if new_text != old_text:
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = new_text
                else:
                    para.add_run(new_text)

    def list_citations(self, with_guide: bool = False) -> list[dict]:
        """Scan body paragraphs for citation markers like [1], [2,3], [1-5].

        Returns list of dicts sorted by appearance order:
            {para_index, chapter_path, text_snippet, numbers: [int]}
        """
        results = []
        citation_pattern = re.compile(r'\[(\d+(?:\s*[-,]\s*\d+)*)\]')

        ref_range = self._find_ref_section_range()
        ref_start = ref_range[0] if ref_range else len(self.model._paragraphs)

        for p in self.model._paragraphs:
            if p.index >= ref_start:
                break
            if p.level is not None:
                continue

            matches = citation_pattern.findall(p.text)
            if not matches:
                continue

            numbers = []
            for group in matches:
                for part in re.split(r'\s*[-,]\s*', group):
                    part = part.strip()
                    if part.isdigit():
                        numbers.append(int(part))

            if numbers:
                results.append({
                    "para_index": p.index,
                    "chapter_path": p.chapter_path,
                    "text_snippet": p.text[:60],
                    "numbers": sorted(set(numbers)),
                })

        if with_guide:
            results.append({
                "_guide": True,
                "message": "正文引用列表。与参考文献条目对照、格式规范见 references/reference-format.md。",
                "file": "references/reference-format.md",
            })
        return results

    def renumber_references(self) -> dict:
        """Renumber reference entries based on first citation order in body text.

        References not cited in text get appended numbers after cited ones.
        Updates both body citations (e.g. [3] → [1]) and reference section entries.

        Returns stats dict.
        """
        citations = self.list_citations()
        seen: set[int] = set()
        citation_order: list[int] = []
        for cit in citations:
            for n in cit["numbers"]:
                if n not in seen:
                    seen.add(n)
                    citation_order.append(n)

        # Build mapping old → new, preserving document order
        ref_order = sorted(self.model._references, key=lambda r: r.para_index)
        ref_numbers = [r.index for r in ref_order]
        cited = [n for n in ref_numbers if n in seen]
        uncited = [n for n in ref_numbers if n not in seen]
        mapping: dict[int, int] = {}
        for new_num, old_num in enumerate(citation_order + uncited, start=1):
            mapping[old_num] = new_num

        if all(old == new for old, new in mapping.items()):
            return {"status": "already_in_order", "total": len(mapping)}

        # Update body text citations
        body_pattern = re.compile(r'\[(\d+(?:\s*[-,]\s*\d+)*)\]')
        ref_range = self._find_ref_section_range()
        ref_start = ref_range[0] if ref_range else len(self.model._paragraphs)

        def _replace_citation(m, mapping=mapping):
            parts = re.split(r'\s*[-,]\s*', m.group(1))
            new_parts = []
            for part in parts:
                part = part.strip()
                if part.isdigit() and int(part) in mapping:
                    new_parts.append(str(mapping[int(part)]))
                else:
                    new_parts.append(part)
            return f"[{','.join(new_parts)}]"

        for p_info in self.model._paragraphs:
            if p_info.index >= ref_start:
                break

            para = self.model._doc.paragraphs[p_info.index]
            new_text = body_pattern.sub(_replace_citation, para.text)
            if new_text != para.text:
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = new_text
                else:
                    para.add_run(new_text)

        # Update reference section entries
        for r in self.model._references:
            old_num = r.index
            if old_num in mapping and mapping[old_num] != old_num:
                idx = r.para_index
                if 0 <= idx < len(self.model._doc.paragraphs):
                    para = self.model._doc.paragraphs[idx]
                    new_text = re.sub(r'^\[\d+\]', f'[{mapping[old_num]}]', para.text)
                    if new_text != para.text:
                        for run in para.runs:
                            run.text = ""
                        if para.runs:
                            para.runs[0].text = new_text
                        else:
                            para.add_run(new_text)

        self.model._build_indexes()
        return {"status": "renumbered", "total": len(mapping), "changes": sum(
            1 for o, n in mapping.items() if o != n
        )}

    def check_citation_density(self) -> dict:
        """Extract citation density per chapter for LLM judgment."""
        citations = self.list_citations()
        ref_range = self._find_ref_section_range()
        ref_start = ref_range[0] if ref_range else len(self.model._paragraphs)

        # Count citations per top-level chapter
        from collections import defaultdict
        chapter_citations = defaultdict(lambda: {"count": 0, "numbers": set()})
        for cit in citations:
            ch = cit["chapter_path"].split(".")[0] if cit["chapter_path"] else "unknown"
            chapter_citations[ch]["count"] += 1
            chapter_citations[ch]["numbers"].update(cit["numbers"])

        # Count body paragraphs per top-level chapter
        chapter_paras = defaultdict(int)
        for p in self.model._paragraphs:
            if p.index >= ref_start:
                break
            if p.level is not None:
                continue
            ch = p.chapter_path.split(".")[0] if p.chapter_path else "unknown"
            chapter_paras[ch] += 1

        # Find uncited references
        cited_numbers = set()
        for cit in citations:
            cited_numbers.update(cit["numbers"])
        uncited = [r.index for r in self.model._references if r.index not in cited_numbers]

        per_chapter = []
        for ch in sorted(chapter_paras.keys()):
            cit_info = chapter_citations.get(ch, {"count": 0, "numbers": set()})
            para_count = chapter_paras[ch]
            density = round(cit_info["count"] / para_count, 2) if para_count else 0
            per_chapter.append({
                "chapter": ch,
                "body_paragraphs": para_count,
                "citation_count": cit_info["count"],
                "density": density,
                "zero_citations": cit_info["count"] == 0,
            })

        return {
            "per_chapter": per_chapter,
            "total_citations_in_body": sum(c_["citation_count"] for c_ in per_chapter),
            "total_references": len(self.model._references),
            "uncited_reference_numbers": uncited,
            "_guide": "引用密度检查。每章应有引用支撑，引用分布不应过度集中。标准见 references/citation-density.md。",
        }
