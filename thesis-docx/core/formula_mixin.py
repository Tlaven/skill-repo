"""
core/formula_mixin.py — Formula write operations for SafeDocument.

Mixin that provides insert_formula and replace_formula.
"""

from __future__ import annotations

from lxml import etree

from .types import Anchor
from .formula import latex_to_omml, create_formula_paragraph, W_NS, M_NS


class FormulaMixin:

    def _make_formula_paragraph_element(self, latex: str,
                                        eq_number: str | None = None,
                                        centered: bool = True):
        """Create a proper python-docx paragraph with OMML formula XML.

        Returns a CT_P element ready for insertion into the document body.
        """
        omath = latex_to_omml(latex)
        new_p_xml = create_formula_paragraph(omath, eq_number, centered)

        # Create a python-docx paragraph to get proper OxmlElement wrapping,
        # then substitute its content with the formula XML.
        # This ensures python-docx's CT_P class wraps the element correctly.
        doc = self.model._doc
        dummy = doc.add_paragraph()
        p_elem = dummy._element

        # Copy formula content into the dummy paragraph
        for child in list(p_elem):
            p_elem.remove(child)
        for child in list(new_p_xml):
            p_elem.append(child)

        # Copy attributes
        for k, v in new_p_xml.attrib.items():
            p_elem.set(k, v)

        # Detach from document
        p_elem.getparent().remove(p_elem)
        return p_elem

    def insert_formula(self, after: Anchor, latex: str,
                       eq_number: str | None = None, centered: bool = True) -> bool:
        """Insert a LaTeX formula as OMML after the specified paragraph. Does NOT call save()."""
        if after.kind != "paragraph" or after.paragraph_index is None:
            return False

        idx = after.paragraph_index
        if idx < 0 or idx >= len(self.model._doc.paragraphs):
            return False

        try:
            p_elem = self._make_formula_paragraph_element(latex, eq_number, centered)
        except ValueError:
            return False

        target = self.model._doc.paragraphs[idx]._element
        target.addnext(p_elem)
        self._rebuild()
        return True

    def insert_formula_chain(self, after: Anchor,
                             formulas: list[tuple[str, str | None]],
                             centered: bool = True) -> int:
        """Insert multiple formulas sequentially after the same anchor.

        Each formula is inserted after the previous one, preserving order.
        Returns the number of formulas successfully inserted.

        Args:
            after: Anchor of the paragraph to insert after.
            formulas: List of (latex, eq_number) tuples.
            centered: Whether to center the formulas.

        Usage:
            safe.insert_formula_chain(anchor, [
                (r"v = W f(x)", "(3.1)"),
                (r"u = W g(y)", "(3.2)"),
            ])
        """
        if after.kind != "paragraph" or after.paragraph_index is None:
            return 0

        count = 0
        idx = after.paragraph_index
        for latex, eq_number in formulas:
            anchor = Anchor(kind="paragraph", paragraph_index=idx,
                            text_snippet=self.model._paragraphs[idx].text[:50] if idx < len(self.model._paragraphs) else "")
            ok = self.insert_formula(anchor, latex, eq_number, centered)
            if ok:
                idx += 1  # new formula is at idx+1, next insert after it
                count += 1
            else:
                break
        return count

    def replace_formula(self, anchor: Anchor, latex: str,
                        eq_number: str | None = None) -> bool:
        """Replace an existing formula paragraph with a new LaTeX formula. Does NOT call save()."""
        if anchor.kind != "formula" or anchor.paragraph_index is None:
            return False

        idx = anchor.paragraph_index
        if idx < 0 or idx >= len(self.model._doc.paragraphs):
            return False

        old_p = self.model._doc.paragraphs[idx]._element

        was_centered = False
        jc = old_p.find(f'{{{W_NS}}}pPr/{{{W_NS}}}jc')
        if jc is not None and jc.get(f'{{{W_NS}}}val') == 'center':
            was_centered = True

        try:
            p_elem = self._make_formula_paragraph_element(latex, eq_number, was_centered)
        except ValueError:
            return False

        old_p.addnext(p_elem)
        old_p.getparent().remove(old_p)
        self._rebuild()
        return True
