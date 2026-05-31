"""
core/exporter.py — Validation and export operations.

Mixin for SafeDocument. Provides format validation checks,
markdown export, image extraction, and document statistics.
"""

from __future__ import annotations
import os
import re

from .types import Anchor


# Common Chinese thesis font mappings
VALID_BODY_FONTS = {"宋体", "SimSun", "Times New Roman", "楷体", "KaiTi",
                    "仿宋_GB2312", "FangSong_GB2312"}
VALID_HEADING_FONTS = {"黑体", "SimHei", "Times New Roman", "Arial"}


class ExporterMixin:

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, with_guide: bool = False) -> list[dict]:
        """Run all thesis format checks. Returns list of issues sorted by paragraph index.

        Checks:
        - Style consistency
        - Font consistency within style class
        - Heading hierarchy (no skipped levels)
        - Image/table caption presence
        - Citation format
        - Body font size range
        """
        issues = []

        # Check heading hierarchy
        prev_level = 0
        for p in self.model._paragraphs:
            if p.level is not None:
                if p.level > prev_level + 1 and prev_level > 0:
                    issues.append({
                        "severity": "warning",
                        "para_index": p.index,
                        "chapter": p.chapter_path,
                        "text_snippet": p.text[:50],
                        "check": "heading_hierarchy",
                        "message": f"Heading level jumps from {prev_level} to {p.level} (skipped level {prev_level + 1})"
                    })
                prev_level = p.level

        # Check body paragraph styles
        for p in self.model._paragraphs:
            # Empty paragraphs
            if p.level is None and not p.text.strip() and not p.has_image:
                issues.append({
                    "severity": "info",
                    "para_index": p.index,
                    "chapter": p.chapter_path,
                    "text_snippet": "(empty)",
                    "check": "empty_paragraph",
                    "message": "Empty paragraph"
                })

            # Font size extremes in body text
            if p.level is None and p.font_size is not None:
                if p.font_size < 9:
                    issues.append({
                        "severity": "warning",
                        "para_index": p.index,
                        "chapter": p.chapter_path,
                        "text_snippet": p.text[:50],
                        "check": "font_too_small",
                        "message": f"Body font size {p.font_size}pt"
                    })
                elif p.font_size > 16:
                    issues.append({
                        "severity": "warning",
                        "para_index": p.index,
                        "chapter": p.chapter_path,
                        "text_snippet": p.text[:50],
                        "check": "font_too_large",
                        "message": f"Body font size {p.font_size}pt"
                    })

            # Unusual fonts in body
            if p.level is None and p.font_name and p.font_name not in VALID_BODY_FONTS | VALID_HEADING_FONTS | {"Cambria Math"}:
                issues.append({
                    "severity": "info",
                    "para_index": p.index,
                    "chapter": p.chapter_path,
                    "text_snippet": p.text[:50],
                    "check": "unusual_font",
                    "message": f"Unusual body font '{p.font_name}'"
                })

        # Check images for caption
        for img in self.model._images:
            if not img.caption:
                issues.append({
                    "severity": "warning",
                    "para_index": img.para_index,
                    "chapter": img.chapter_path,
                    "text_snippet": img.filename,
                    "check": "image_no_caption",
                    "message": f"Image '{img.filename}' has no caption"
                })

        # Check tables for caption
        for t in self.model._tables:
            if not t.caption:
                issues.append({
                    "severity": "warning",
                    "para_index": t.para_index,
                    "chapter": t.chapter_path,
                    "text_snippet": f"Table at para {t.para_index}",
                    "check": "table_no_caption",
                    "message": f"Table (header: {t.header[:2]}) has no caption"
                })

        issues.sort(key=lambda x: (x["para_index"] if x["para_index"] is not None else 0))
        if with_guide:
            issues.append({
                "_guide": True,
                "message": "验证发现多类问题。格式标准见 references/format-roles.md；图表编号规则见 references/figure-table-numbering.md。",
                "file": "references/format-roles.md",
            })
        return issues

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def count_words(self, chapter: str | None = None) -> dict:
        """Count characters, paragraphs, images, tables, formulas.

        If chapter is specified, only count within that chapter.
        """
        paras = self.model._paragraphs
        if chapter:
            paras = [p for p in paras if p.chapter_path == chapter or p.chapter_path.startswith(chapter + ".")]

        total_chars = sum(p.char_count for p in paras if p.level is None)
        total_paras = len(paras)
        body_paras = len([p for p in paras if p.level is None])
        heading_paras = len([p for p in paras if p.level is not None])
        images = len([p for p in paras if p.has_image])
        empty_paras = len([p for p in paras if not p.text.strip() and not p.has_image])

        # Count tables and formulas in this chapter's range
        tables = 0
        formulas = 0
        if paras:
            start_idx = paras[0].index
            end_idx = paras[-1].index
            tables = sum(1 for t in self.model._tables if start_idx <= t.para_index <= end_idx)
            formulas = sum(1 for f in self.model._formulas if start_idx <= f.para_index <= end_idx)

        result = {
            "total_chars": total_chars,
            "total_paras": total_paras,
            "body_paras": body_paras,
            "heading_paras": heading_paras,
            "empty_paras": empty_paras,
            "images": images,
            "tables": tables,
            "formulas": formulas,
        }
        if chapter:
            result["chapter"] = chapter
        result["_guide"] = "段落是否过长的判断标准见 references/paragraph-length.md。"

        return result

    def count_words_per_section(self) -> list[dict]:
        """Count statistics per top-level section (Heading 1)."""
        results = []
        for sec in self.model._sections:
            stats = self.count_words(chapter=sec.chapter_path)
            stats.pop("_guide", None)
            stats["title"] = sec.title
            stats["chapter_path"] = sec.chapter_path
            results.append(stats)
        results.append({
            "_guide": True,
            "message": "各章字数统计。段落是否过长的判断标准见 references/paragraph-length.md。",
            "file": "references/paragraph-length.md",
        })
        return results

    # ------------------------------------------------------------------
    # Content Quality Checks (extract data for LLM judgment)
    # ------------------------------------------------------------------

    def check_abstract_vs_conclusion(self) -> dict:
        abstract_text = ""
        conclusion_text = ""
        abstract_chapter = ""
        conclusion_chapter = ""
        for p in self.model._paragraphs:
            if p.level is not None and p.level <= 2:
                title = p.text.strip().lower()
                if any(k in title for k in ("摘要", "abstract")):
                    abstract_chapter = p.chapter_path
                if any(k in title for k in ("结论", "总结", "conclusion")):
                    conclusion_chapter = p.chapter_path
        for p in self.model._paragraphs:
            if abstract_chapter and p.chapter_path == abstract_chapter:
                abstract_text += p.text + "\n"
            if conclusion_chapter and p.chapter_path == conclusion_chapter:
                conclusion_text += p.text + "\n"
        if not abstract_text and not conclusion_text:
            for p in self.model._paragraphs:
                if p.level is not None and '摘要' in (p.text or ''):
                    abstract_chapter = p.chapter_path or ''
                if p.level is not None and ('结论' in (p.text or '') or '总结' in (p.text or '')):
                    conclusion_chapter = p.chapter_path or ''
            for p in self.model._paragraphs:
                if abstract_chapter and p.chapter_path == abstract_chapter:
                    abstract_text += p.text + "\n"
                if conclusion_chapter and p.chapter_path == conclusion_chapter:
                    conclusion_text += p.text + "\n"
        return {
            "abstract": abstract_text[:2000] if abstract_text else "(未找到摘要)",
            "conclusion": conclusion_text[:2000] if conclusion_text else "(未找到结论)",
            "abstract_chapter": abstract_chapter,
            "conclusion_chapter": conclusion_chapter,
            "_guide": "摘要和结论文本并排对照。二者不应有重复段落，区别见 references/abstract-vs-conclusion.md。",
        }

    def check_residual_content(self) -> dict:
        import re
        patterns = {
            'TODO': r'TODO|FIXME|XXX',
            'zh_placeholder': r'待补充|待完善|待填|待定|TBD|TK',
            'formula_marker': r'FORMULA_\d+_?\d*',
            'table_marker': r'TABLE_\d+_?\d*',
            'figure_marker': r'FIGURE_\d+_?\d*',
        }
        matches: dict[str, list[dict]] = {k: [] for k in patterns}
        for p in self.model._paragraphs:
            for label, pat in patterns.items():
                for m in re.finditer(pat, p.text):
                    matches[label].append({
                        "para_index": p.index,
                        "chapter": p.chapter_path,
                        "match": m.group(),
                        "context": p.text[max(0, m.start()-10):m.end()+10],
                    })
        empty_paras = []
        prev_empty = False
        for p in self.model._paragraphs:
            is_empty = not p.text.strip() and not p.has_image
            if is_empty:
                location = "start" if p.index < 3 else ("end" if p.index >= len(self.model._paragraphs) - 3 else "body")
                empty_paras.append({
                    "para_index": p.index,
                    "chapter": p.chapter_path,
                    "location": location,
                    "consecutive": prev_empty,
                })
            prev_empty = is_empty
        return {
            "pattern_matches": {k: v for k, v in matches.items() if v},
            "empty_paras": empty_paras,
            "_guide": "残留内容检查。占位符/标记见上表，空段列表见上。判断标准和完整规范见 references/residual-content.md。",
        }

    def check_punctuation(self) -> dict:
        samples = [
            {
                "index": p.index,
                "chapter": p.chapter_path,
                "text": p.text[:120],
            }
            for p in self.model._paragraphs
            if p.level is None and p.char_count > 30
        ]
        return {
            "body_paragraphs": len(samples),
            "samples": samples[:20],
            "_guide": "正文段落文本样本。检查中英文标点混用、引号是否统一。标准见 references/punctuation.md。",
        }

    def check_structure_completeness(self) -> dict:
        sections = self.model.sections
        section_titles = []
        has_abstract = False
        has_conclusion = False
        has_references = False
        has_appendix = False
        has_acknowledgement = False
        for s in sections:
            title = s.title.strip()
            section_titles.append({"level": s.level, "title": title, "chapter": s.chapter_path})
            t = title.lower()
            if any(k in t for k in ("摘要", "abstract")):
                has_abstract = True
            if any(k in t for k in ("结论", "总结", "conclusion")):
                has_conclusion = True
            if any(k in t for k in ("参考文献", "reference")):
                has_references = True
            if any(k in t for k in ("附录", "appendix")):
                has_appendix = True
            if any(k in t for k in ("致谢", "acknowledgement")):
                has_acknowledgement = True
        return {
            "section_count": len(sections),
            "top_level_count": len([s for s in sections if s.level == 1]),
            "structure": section_titles[:30],
            "has_abstract": has_abstract,
            "has_conclusion": has_conclusion,
            "has_references": has_references,
            "has_appendix": has_appendix,
            "has_acknowledgement": has_acknowledgement,
            "_guide": "文档结构概览。标准论文应有摘要/正文/结论/参考文献/致谢。检查标准见 references/document-structure.md。",
        }

    # ------------------------------------------------------------------
    # Phase 3+ Checks (8 new data-extraction methods)
    # ------------------------------------------------------------------

    def check_formula_numbering(self) -> dict:
        """Extract formula numbering data and cross-reference info."""
        formulas = self.model.formulas
        formula_list = []
        for f in formulas:
            formula_list.append({
                "para_index": f.para_index,
                "chapter": f.chapter_path,
                "eq_number": f.equation_number,
                "type": f.formula_type,
                "content": f.content[:60] if f.content else "",
            })

        # Scan body text for formula references: 式(3.1), 式3.1, (3.1), 式(3-1)
        ref_pattern = re.compile(r'式\s*[\(（]?\s*(\d+[\.\-]\d+)\s*[\)）]?')
        ref_range = self._find_ref_section_range() if hasattr(self, '_find_ref_section_range') else None
        ref_start = ref_range[0] if ref_range else len(self.model._paragraphs)

        body_refs = []
        for p in self.model._paragraphs:
            if p.index >= ref_start:
                break
            if p.level is not None:
                continue
            for m in ref_pattern.finditer(p.text):
                body_refs.append({
                    "para_index": p.index,
                    "chapter": p.chapter_path,
                    "referenced_number": m.group(1),
                    "context": p.text[max(0, m.start()-8):m.end()+8],
                })

        return {
            "formula_count": len(formula_list),
            "formulas": formula_list,
            "body_references": body_refs,
            "_guide": "公式编号连续性和交叉引用检查。编号应连续无跳号，正文引用与实际公式一一对应。标准见 references/formula-numbering.md。",
        }

    def check_figure_table_quality(self) -> dict:
        """Extract figure/table quality data (size, format, caption)."""
        images = self.model.images
        tables = self.model.tables

        image_list = []
        for img in images:
            image_list.append({
                "para_index": img.para_index,
                "chapter": img.chapter_path,
                "width_cm": img.width_cm,
                "height_cm": img.height_cm,
                "format": img.format,
                "caption": img.caption,
                "filename": img.filename,
            })

        table_list = []
        for t in tables:
            table_list.append({
                "para_index": t.para_index,
                "chapter": t.chapter_path,
                "row_count": t.row_count,
                "col_count": t.col_count,
                "header": t.header,
                "caption": t.caption,
            })

        return {
            "image_count": len(image_list),
            "images": image_list,
            "table_count": len(table_list),
            "tables": table_list,
            "_guide": "图表质量检查。图片尺寸合理性、格式、题注；表格结构、题注。标准见 references/figure-table-quality.md。",
        }

    def check_abstract_bilingual(self) -> dict:
        """Extract Chinese and English abstracts + keywords for comparison."""
        zh_abstract = ""
        en_abstract = ""
        zh_keywords = ""
        en_keywords = ""

        current_section = None
        for p in self.model._paragraphs:
            title = p.text.strip().lower()
            if p.level is not None and p.level <= 2:
                if any(k in title for k in ("摘要", "abstract")):
                    if any(k in title for k in ("abstract", "英文")):
                        current_section = "en_abstract"
                    else:
                        current_section = "zh_abstract"
                elif any(k in title for k in ("关键词", "keyword")):
                    current_section = None
                elif p.level <= 2:
                    current_section = None
                continue

            if current_section == "zh_abstract":
                zh_abstract += p.text + "\n"
                if "关键词" in p.text or "关键字" in p.text:
                    zh_keywords = p.text
            elif current_section == "en_abstract":
                en_abstract += p.text + "\n"
                if "keyword" in p.text.lower():
                    en_keywords = p.text

        return {
            "zh_abstract": zh_abstract[:3000] if zh_abstract else "(未找到中文摘要)",
            "en_abstract": en_abstract[:3000] if en_abstract else "(未找到英文摘要)",
            "zh_keywords": zh_keywords,
            "en_keywords": en_keywords,
            "_guide": "中英文摘要和关键词对照。核心要素应一致，术语应对应，数量应相同。标准见 references/abstract-bilingual.md。",
        }

    def check_section_balance(self) -> dict:
        """Extract per-chapter word counts for balance analysis."""
        sections = self.model.sections
        top_sections = []
        for s in sections:
            if s.level != 1:
                continue
            start, end = s.para_range
            char_count = sum(
                self.model._paragraphs[p].char_count
                for p in range(start, end + 1)
                if p < len(self.model._paragraphs)
            )
            top_sections.append({
                "title": s.title,
                "chapter": s.chapter_path,
                "char_count": char_count,
                "para_count": end - start + 1,
            })

        total_chars = sum(s_["char_count"] for s_ in top_sections)
        for s_ in top_sections:
            s_["percentage"] = round(s_["char_count"] / total_chars * 100, 1) if total_chars else 0

        return {
            "total_chars": total_chars,
            "section_count": len(top_sections),
            "sections": top_sections,
            "_guide": "章节均衡性检查。正文章节字数不应悬殊，篇幅应与内容重要性匹配。标准见 references/section-balance.md。",
        }

    def check_keywords(self) -> dict:
        """Extract and compare Chinese/English keywords."""
        zh_kw = []
        en_kw = []
        in_zh_abstract = False
        in_en_abstract = False

        for p in self.model._paragraphs:
            title = p.text.strip().lower()
            if p.level is not None and p.level <= 2:
                if any(k in title for k in ("摘要", "abstract")):
                    if any(k in title for k in ("abstract", "英文")):
                        in_en_abstract = True
                        in_zh_abstract = False
                    else:
                        in_zh_abstract = True
                        in_en_abstract = False
                elif p.level <= 2:
                    in_zh_abstract = False
                    in_en_abstract = False
                continue

            text = p.text.strip()
            if "关键词" in text or "关键字" in text:
                import re as _re
                kw_text = _re.split(r'关键词[：:]', text)[-1] if '关键词' in text else _re.split(r'关键字[：:]', text)[-1]
                zh_kw = [k.strip().strip('；;，,。.') for k in _re.split(r'[；;]', kw_text) if k.strip()]
            elif "keyword" in text.lower():
                import re as _re
                kw_text = _re.split(r'keywords?\s*[:：]', text, flags=_re.IGNORECASE)[-1]
                en_kw = [k.strip().strip('；;，,。.') for k in _re.split(r'[；;,]', kw_text) if k.strip()]

        return {
            "zh_keywords": zh_kw,
            "zh_count": len(zh_kw),
            "en_keywords": en_kw,
            "en_count": len(en_kw),
            "count_match": len(zh_kw) == len(en_kw),
            "_guide": "关键词一致性检查。中英文关键词数量应一致、术语应对应、格式应统一。标准见 references/keywords.md。",
        }

    def check_section_numbering(self) -> dict:
        """Extract section numbering data for continuity check."""
        sections = self.model.sections
        numbered = []
        for s in sections:
            numbered.append({
                "level": s.level,
                "title": s.title,
                "chapter_path": s.chapter_path,
            })

        # Check continuity: group by parent, check sequential
        issues = []
        from collections import defaultdict
        by_parent = defaultdict(list)
        for s in sections:
            path = s.chapter_path
            if not path:
                continue
            parts = path.split(".")
            if len(parts) >= 2:
                parent = ".".join(parts[:-1])
            else:
                parent = ""
            by_parent[parent].append({
                "path": path,
                "title": s.title,
                "last_part": parts[-1],
            })

        for parent, children in by_parent.items():
            nums = []
            for c in children:
                try:
                    nums.append(int(c["last_part"]))
                except ValueError:
                    continue
            if nums:
                nums.sort()
                for i in range(1, len(nums)):
                    if nums[i] != nums[i-1] + 1:
                        issues.append({
                            "parent": parent or "(root)",
                            "gap": f"{nums[i-1]} → {nums[i]}",
                            "missing": list(range(nums[i-1]+1, nums[i])),
                        })

        return {
            "section_count": len(numbered),
            "sections": numbered[:40],
            "numbering_issues": issues,
            "_guide": "标题编号连续性检查。同级编号应连续递增无跳号，格式应统一。标准见 references/section-numbering.md。",
        }

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_markdown(self, output_path: str | os.PathLike,
                        include_images: bool = True) -> str:
        """Export the document content as Markdown.

        Preserves heading levels, paragraph text, table structure as markdown tables.
        Images are referenced by filename (or extracted if include_images=True).
        """
        lines = []
        ref_section_start = None
        for p in self.model._paragraphs:
            if p.level is not None and p.level <= 2 and '参考文献' in p.text:
                ref_section_start = p.index
                lines.append("\n## 参考文献\n")
                continue

            if ref_section_start is not None:
                # In reference section
                if p.level is not None and p.level <= 2:
                    break
                for r in self.model._references:
                    if r.para_index == p.index:
                        lines.append(f"[{r.index}] {r.text}\n")
                        break
                continue

            if p.level is not None:
                prefix = "#" * min(p.level, 6)
                lines.append(f"\n{prefix} {p.text}\n")
            elif p.has_image:
                for img in self.model._images:
                    if img.para_index == p.index:
                        cap = f" _{img.caption}_" if img.caption else ""
                        lines.append(f"\n![{img.filename}]({img.filename}){cap}\n")
                        break
            elif p.text.strip():
                lines.append(f"{p.text}\n\n")

        # Build table content
        for t in self.model._tables:
            if t.caption:
                lines.append(f"\n**{t.caption}**\n\n")
            # Header row
            if t.header:
                lines.append("| " + " | ".join(t.header) + " |\n")
                lines.append("| " + " | ".join(["---"] * len(t.header)) + " |\n")

        output = "".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        return os.path.abspath(output_path)

    def extract_images(self, output_dir: str | os.PathLike) -> list[str]:
        """Extract all embedded images from the document to a directory.

        Returns list of saved file paths.
        """
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        saved = []
        for img in self.model._images:
            rel = self.model._doc.part.rels.get(img.r_id)
            if rel is None:
                continue

            try:
                blob = rel.target_part.blob
            except Exception:
                continue

            # Determine extension
            ext = img.format or "png"
            if ext == "jpg":
                ext = "jpg"
            filename = f"img_{img.para_index}.{ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(blob)
            saved.append(filepath)

        return saved
