"""
core/persistence.py — SafeDocument + guarded persistence.

Owns the sacred save_zip logic and basic mutations.
Batch/table/image operations live in separate mixin modules.
"""

from __future__ import annotations
import os
import tempfile
import zipfile
from dataclasses import replace
from lxml import etree

from .model import DocumentModel
from .types import ParagraphInfo, Anchor, Locator, SectionNode
from .editor import EditorMixin
from .table import TableMixin
from .image import ImageMixin
from .formula_mixin import FormulaMixin
from .style import StyleMixin
from .reference import ReferenceMixin
from .layout import LayoutMixin
from .exporter import ExporterMixin


class SafeDocument(EditorMixin, TableMixin, ImageMixin, FormulaMixin, StyleMixin, ReferenceMixin, LayoutMixin, ExporterMixin):
    """
    The mutable, safe-to-persist wrapper around a DocumentModel.

    All real document changes that need to survive to disk should eventually
    go through this class (or methods it exposes).
    """

    def __init__(self, filepath: str | os.PathLike):
        self.model = DocumentModel(filepath)
        self._original_path = os.path.abspath(filepath)
        self._media_overrides: dict[str, bytes] = {}

    def _rebuild(self):
        """Rebuild all model indexes after a structural mutation."""
        self.model._build_indexes()

    def save(self, output_path: str | os.PathLike | None = None) -> str:
        """
        The one true way to persist changes.

        - Uses the battle-tested zip-rewrite strategy from the original.
        - After successful save, the internal model is automatically refreshed.
        """
        target = output_path or self._original_path
        path = self._save_zip_impl(target)
        self._media_overrides.clear()
        self.model = DocumentModel(path)
        return path

    # ------------------------------------------------------------------
    # Basic Mutation Support (Phase 1 - content-based only)
    # ------------------------------------------------------------------

    def replace_text(self, anchor: "Anchor", new_text: str) -> bool:
        """
        Replace the text of the paragraph referenced by the Anchor.

        B1 Hardened behavior for real revision scenarios (user-accepted design):

        - Paragraphs WITHOUT revisions:
            Best-effort formatting preservation. Tries to reuse the most
            representative run style in the paragraph.

        - Paragraphs WITH revisions (w:ins / w:del present):
            *Preserve all existing revision history structure*.
            Only the "currently visible" text is replaced.
            The new text is inserted as clean content (NOT wrapped in a new w:ins).
            This keeps revision history honest and untouched.

        - If the revision structure is too complex to operate on safely,
          the method returns False immediately (fail fast, no best-effort).
        """
        if anchor.kind != "paragraph" or anchor.paragraph_index is None:
            return False

        idx = anchor.paragraph_index
        if idx < 0 or idx >= len(self.model._doc.paragraphs):
            return False

        para = self.model._doc.paragraphs[idx]
        pinfo = self.model._paragraphs[idx] if idx < len(self.model._paragraphs) else None
        has_revisions = bool(pinfo and pinfo.has_revisions)

        if has_revisions:
            success = self._replace_visible_text_in_revised_paragraph(para, new_text)
        else:
            success = self._replace_text_preserve_formatting(para, new_text)

        if not success:
            return False

        if pinfo:
            self.model._paragraphs[idx] = replace(
                pinfo, text=new_text, char_count=len(new_text)
            )

        return True

    def _replace_text_preserve_formatting(self, para, new_text: str) -> bool:
        """Non-revised path: find representative run, reuse its style."""
        if not para.runs:
            para.add_run(new_text)
            return True

        representative = para.runs[0]
        best_score = 0

        for run in para.runs:
            score = 0
            if run.text:
                score += 1
            if run.bold:
                score += 1
            if run.italic:
                score += 1
            if run.font and run.font.size:
                score += 1
            if score > best_score:
                best_score = score
                representative = run

        for run in para.runs:
            if run is not representative:
                run.text = ""
        representative.text = new_text
        return True

    def _replace_visible_text_in_revised_paragraph(self, para, new_text: str) -> bool:
        """Revised paragraph path. Never destroys w:ins/w:del. Returns False if too complex."""
        p = para._element

        w_ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        ins_tag = f'{w_ns}ins'
        del_tag = f'{w_ns}del'
        r_tag = f'{w_ns}r'
        t_tag = f'{w_ns}t'

        children = list(p)
        has_complex_structure = False
        visible_run_count = 0

        for child in children:
            tag = child.tag
            if tag in (ins_tag, del_tag):
                inner_runs = child.findall('.//' + r_tag)
                if len(inner_runs) > 3:
                    has_complex_structure = True
            elif tag == r_tag:
                visible_run_count += 1

        if has_complex_structure or visible_run_count > 8:
            return False

        visible_runs = []
        for child in children:
            if child.tag == r_tag:
                visible_runs.append(child)

        for run in visible_runs:
            for t in run.findall('.//' + t_tag):
                t.text = ""

        if visible_runs:
            target_run = visible_runs[-1]
            t_elem = target_run.find('.//' + t_tag)
            if t_elem is not None:
                t_elem.text = new_text
            else:
                new_t = etree.SubElement(target_run, t_tag)
                new_t.text = new_text
        else:
            new_run = etree.SubElement(p, r_tag)
            new_t = etree.SubElement(new_run, t_tag)
            new_t.text = new_text

        return True

    # ------------------------------------------------------------------
    # Query Helpers
    # ------------------------------------------------------------------

    def find(self, locator: "Locator | str"):
        """Convenience: resolve a locator against the current model."""
        return self.model.resolve(locator)

    def find_all(self, locator: "Locator | str"):
        """Resolve a locator and return ALL matching anchors."""
        return self.model.resolve_all(locator)

    def find_revised_paragraphs(self, chapter: str | None = None, author: str | None = None, rev_type: str | None = None):
        """Ergonomic helper for revision queries."""
        results = []
        for p in self.model.paragraphs:
            if not p.has_revisions:
                continue
            if chapter and not (p.chapter_path == chapter or p.chapter_path.startswith(chapter + ".")):
                continue
            if author and author not in p.revision_authors:
                continue
            if rev_type and rev_type not in p.revision_types:
                continue
            results.append(Anchor(
                kind="paragraph",
                paragraph_index=p.index,
                text_snippet=p.text[:80],
                chapter_path=p.chapter_path,
            ))
        return results

    def get_revised_paragraphs_in_section(self, section: "SectionNode") -> list["ParagraphInfo"]:
        """Return all revised paragraphs within a SectionNode's range."""
        return section.get_revised_paragraphs(self.model.paragraphs)

    # ------------------------------------------------------------------
    # Structural Mutations (basic)
    # ------------------------------------------------------------------

    def delete_paragraph(self, anchor: "Anchor") -> bool:
        """Delete the paragraph referenced by the Anchor."""
        if anchor.kind != "paragraph" or anchor.paragraph_index is None:
            return False
        idx = anchor.paragraph_index
        if idx < 0 or idx >= len(self.model._doc.paragraphs):
            return False

        p = self.model._doc.paragraphs[idx]
        p._element.getparent().remove(p._element)

        if idx < len(self.model._paragraphs):
            del self.model._paragraphs[idx]
            for i in range(idx, len(self.model._paragraphs)):
                self.model._paragraphs[i] = replace(
                    self.model._paragraphs[i], index=i
                )
        return True

    def insert_paragraph(self, after: "Anchor", text: str, style: str = "Normal") -> bool:
        """Insert a new paragraph after the one referenced by Anchor."""
        if after.kind != "paragraph" or after.paragraph_index is None:
            return False
        idx = after.paragraph_index
        if idx < 0 or idx >= len(self.model._doc.paragraphs):
            return False

        target_para = self.model._doc.paragraphs[idx]
        new_p = self.model._doc.add_paragraph(text, style=style)
        target_para._element.addnext(new_p._element)

        new_info = ParagraphInfo(
            index=idx + 1,
            text=text,
            style=style,
            level=None,
            chapter_path=self.model._paragraphs[idx].chapter_path if idx < len(self.model._paragraphs) else "",
            char_count=len(text),
        )
        self.model._paragraphs.insert(idx + 1, new_info)

        for i in range(idx + 2, len(self.model._paragraphs)):
            self.model._paragraphs[i] = replace(
                self.model._paragraphs[i], index=i
            )
        return True

    # ------------------------------------------------------------------
    # Shared Helpers (used by table.py and image.py mixins)
    # ------------------------------------------------------------------

    def _detect_caption_style(self) -> str | None:
        """Scan document for existing caption-styled paragraphs."""
        for p in self.model._doc.paragraphs:
            if p.style and 'caption' in p.style.name.lower():
                return p.style.name
        for p in self.model._doc.paragraphs:
            if p.style and any(kw in p.style.name for kw in ('图注', '表注', '插图', '表格')):
                return p.style.name
        return None

    # ------------------------------------------------------------------
    # Sacred save_zip logic
    # ------------------------------------------------------------------

    def _build_rels_xml(self):
        """Rebuild relationships XML from current document state."""
        NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
        root = etree.Element(f'{{{NS}}}Relationships')
        for rId, rel in self.model._doc.part.rels.items():
            child = etree.SubElement(root, f'{{{NS}}}Relationship')
            child.set('Id', rId)
            child.set('Type', rel.reltype)
            child.set('Target', rel.target_ref)
        return etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

    def _save_zip_impl(self, output_path: str) -> str:
        """Protected save_zip implementation. Preserves formulas/images."""
        path = os.path.abspath(output_path)

        xml_bytes = etree.tostring(
            self.model._doc.element,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True,
        )
        rels_xml = self._build_rels_xml()

        output_dir = os.path.dirname(path)
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".docx", dir=output_dir)
        os.close(tmp_fd)

        try:
            with zipfile.ZipFile(self._original_path, "r") as zin:
                with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
                    written = set()
                    for item in zin.infolist():
                        if item.filename in written:
                            continue
                        written.add(item.filename)

                        if item.filename == "word/document.xml":
                            zout.writestr(item, xml_bytes)
                        elif item.filename == "word/_rels/document.xml.rels":
                            zout.writestr(item, rels_xml)
                        else:
                            if item.filename in self._media_overrides:
                                zout.writestr(item, self._media_overrides[item.filename])
                            else:
                                zout.writestr(item, zin.read(item))

                    # Preserve any in-memory blobs (images, etc.)
                    for rel in self.model._doc.part.rels.values():
                        if not hasattr(rel, 'target_part'):
                            continue
                        target_ref = rel.target_ref
                        if target_ref.startswith('/'):
                            target_ref = target_ref[1:]
                        elif target_ref.startswith('../'):
                            target_ref = target_ref[3:]
                        if not target_ref.startswith('word/'):
                            target_ref = f'word/{target_ref}'
                        if target_ref in written:
                            continue
                        written.add(target_ref)
                        try:
                            if hasattr(rel.target_part, 'blob'):
                                zout.writestr(target_ref, rel.target_part.blob)
                            elif hasattr(rel.target_part, '_element'):
                                part_xml = etree.tostring(
                                    rel.target_part._element,
                                    xml_declaration=True, encoding='UTF-8', standalone=True)
                                zout.writestr(target_ref, part_xml)
                        except Exception as e:
                            import warnings
                            warnings.warn(f'save_zip: 无法写入 {target_ref}: {e}')

            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        return path
