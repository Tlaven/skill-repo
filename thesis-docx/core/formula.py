"""
core/formula.py — LaTeX → OMML conversion and formula insertion.

Pipeline: LaTeX string → latex2mathml → MathML XML → MathMLToOMML → OMML XML → insert into document.

Ported from the original lib/formula.py with minimal changes.
"""

from __future__ import annotations
import re

from lxml import etree
from latex2mathml.converter import convert as _latex_to_mathml
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def _m(tag):
    return f'{{{M_NS}}}{tag}'


def _w(tag):
    return f'{{{W_NS}}}{tag}'


def _ox(tag):
    """Create an OxmlElement with the given namespace-prefixed tag (e.g. 'w:p')."""
    return OxmlElement(tag)


def _make_wrpr(italic=False, bold=False):
    wrpr = etree.Element(_w('rPr'))
    fonts = etree.SubElement(wrpr, _w('rFonts'))
    fonts.set(_w('hint'), 'default')
    fonts.set(_w('ascii'), 'Cambria Math')
    fonts.set(_w('hAnsi'), 'Cambria Math')
    fonts.set(_w('eastAsia'), '宋体')
    fonts.set(_w('cs'), 'Times New Roman')
    etree.SubElement(wrpr, _w('b')).set(_w('val'), 'true' if bold else '0')
    if italic:
        etree.SubElement(wrpr, _w('i'))
    else:
        etree.SubElement(wrpr, _w('i')).set(_w('val'), '0')
    etree.SubElement(wrpr, _w('sz')).set(_w('val'), '24')
    return wrpr


def _make_math_run(text, italic=False, normal=True):
    mr = etree.Element(_m('r'))
    mrpr = etree.SubElement(mr, _m('rPr'))
    if normal:
        etree.SubElement(mrpr, _m('nor'))
    mr.append(_make_wrpr(italic=italic))
    mt = etree.SubElement(mr, _m('t'))
    mt.text = text
    return mr


def _make_ctrl_pr(italic=False):
    ctrl = etree.Element(_m('ctrlPr'))
    ctrl.append(_make_wrpr(italic=italic))
    return ctrl


class MathMLToOMML:
    """Convert MathML XML to OMML XML (Word math formula format)."""

    def convert(self, mathml_str):
        root = etree.fromstring(mathml_str.encode('utf-8'))
        omath = etree.Element(_m('oMath'))
        for c in self._convert_children(root):
            omath.append(c)
        return omath

    def _local(self, elem):
        tag = elem.tag
        return tag.split('}')[1] if '}' in tag else tag

    def _convert_children(self, parent):
        results = []
        for child in parent:
            results.extend(self._convert_elem(child))
        return results

    def _convert_elem(self, elem):
        local = self._local(elem)
        method = getattr(self, f'_conv_{local}', None)
        if method:
            result = method(elem)
            if result is not None:
                return result if isinstance(result, list) else [result]
        return self._convert_children(elem)

    # Pass-through elements
    def _conv_mrow(self, elem): return self._convert_children(elem)
    def _conv_mstyle(self, elem): return self._convert_children(elem)
    def _conv_mpadded(self, elem): return self._convert_children(elem)
    def _conv_mphantom(self, elem): return self._convert_children(elem)

    # Basic tokens
    def _conv_mn(self, elem): return _make_math_run(elem.text or '', italic=False, normal=True)
    def _conv_mi(self, elem):
        text = elem.text or ''
        return _make_math_run(text, italic=len(text.strip()) == 1, normal=not (len(text.strip()) == 1))
    def _conv_mo(self, elem): return _make_math_run(elem.text or '', italic=False, normal=True)
    def _conv_mtext(self, elem): return _make_math_run(elem.text or '', italic=False, normal=True)
    def _conv_mspace(self, elem): return _make_math_run(' ', italic=False, normal=True)

    # Fraction
    def _conv_mfrac(self, elem):
        children = list(elem)
        if len(children) < 2: return None
        frac = etree.Element(_m('f'))
        etree.SubElement(frac, _m('fPr')).append(_make_ctrl_pr())
        num = etree.SubElement(frac, _m('num'))
        for c in self._convert_elem(children[0]): num.append(c)
        den = etree.SubElement(frac, _m('den'))
        for c in self._convert_elem(children[1]): den.append(c)
        return frac

    # Subscript / Superscript / SubSup
    def _conv_msub(self, elem):
        children = list(elem)
        if len(children) < 2: return None
        ssub = etree.Element(_m('sSub'))
        etree.SubElement(ssub, _m('sSubPr')).append(_make_ctrl_pr())
        base = etree.SubElement(ssub, _m('e'))
        for c in self._convert_elem(children[0]): base.append(c)
        sub = etree.SubElement(ssub, _m('sub'))
        for c in self._convert_elem(children[1]): sub.append(c)
        sub.append(_make_ctrl_pr())
        return ssub

    def _conv_msup(self, elem):
        children = list(elem)
        if len(children) < 2: return None
        ssup = etree.Element(_m('sSup'))
        etree.SubElement(ssup, _m('sSupPr')).append(_make_ctrl_pr())
        base = etree.SubElement(ssup, _m('e'))
        for c in self._convert_elem(children[0]): base.append(c)
        sup = etree.SubElement(ssup, _m('sup'))
        for c in self._convert_elem(children[1]): sup.append(c)
        sup.append(_make_ctrl_pr())
        return ssup

    def _conv_msubsup(self, elem):
        children = list(elem)
        if len(children) < 3: return None
        sss = etree.Element(_m('sSubSup'))
        etree.SubElement(sss, _m('sSubSupPr')).append(_make_ctrl_pr())
        base = etree.SubElement(sss, _m('e'))
        for c in self._convert_elem(children[0]): base.append(c)
        sub = etree.SubElement(sss, _m('sub'))
        for c in self._convert_elem(children[1]): sub.append(c)
        sub.append(_make_ctrl_pr())
        sup = etree.SubElement(sss, _m('sup'))
        for c in self._convert_elem(children[2]): sup.append(c)
        sup.append(_make_ctrl_pr())
        return sss

    # Radical (sqrt / nth-root)
    def _conv_msqrt(self, elem):
        rad = etree.Element(_m('rad'))
        pr = etree.SubElement(rad, _m('radPr'))
        etree.SubElement(pr, _m('degHide'))
        pr.append(_make_ctrl_pr())
        deg = etree.SubElement(rad, _m('deg'))
        deg.append(_make_ctrl_pr())
        e = etree.SubElement(rad, _m('e'))
        for c in self._convert_children(elem): e.append(c)
        return rad

    def _conv_mroot(self, elem):
        children = list(elem)
        if len(children) < 2: return None
        rad = etree.Element(_m('rad'))
        etree.SubElement(rad, _m('radPr')).append(_make_ctrl_pr())
        deg = etree.SubElement(rad, _m('deg'))
        for c in self._convert_elem(children[1]): deg.append(c)
        deg.append(_make_ctrl_pr())
        e = etree.SubElement(rad, _m('e'))
        for c in self._convert_elem(children[0]): e.append(c)
        return rad

    # N-ary (sum, integral, etc.)
    def _conv_munderover(self, elem):
        children = list(elem)
        if len(children) < 3: return self._convert_children(elem)
        nary = etree.Element(_m('nary'))
        npr = etree.SubElement(nary, _m('naryPr'))
        etree.SubElement(npr, _m('chr')).set(_m('val'), children[0].text or '∑')
        etree.SubElement(npr, _m('limLoc')).set(_m('val'), 'undOvr')
        npr.append(_make_ctrl_pr())
        sub = etree.SubElement(nary, _m('sub'))
        for c in self._convert_elem(children[1]): sub.append(c)
        sub.append(_make_ctrl_pr())
        sup = etree.SubElement(nary, _m('sup'))
        for c in self._convert_elem(children[2]): sup.append(c)
        sup.append(_make_ctrl_pr())
        return nary

    def _conv_munder(self, elem):
        children = list(elem)
        if len(children) < 2: return self._convert_children(elem)
        ssub = etree.Element(_m('sSub'))
        etree.SubElement(ssub, _m('sSubPr')).append(_make_ctrl_pr())
        base = etree.SubElement(ssub, _m('e'))
        for c in self._convert_elem(children[0]): base.append(c)
        sub = etree.SubElement(ssub, _m('sub'))
        for c in self._convert_elem(children[1]): sub.append(c)
        sub.append(_make_ctrl_pr())
        return ssub

    def _conv_mover(self, elem):
        children = list(elem)
        if len(children) < 2: return self._convert_children(elem)
        ssup = etree.Element(_m('sSup'))
        etree.SubElement(ssup, _m('sSupPr')).append(_make_ctrl_pr())
        base = etree.SubElement(ssup, _m('e'))
        for c in self._convert_elem(children[0]): base.append(c)
        sup = etree.SubElement(ssup, _m('sup'))
        for c in self._convert_elem(children[1]): sup.append(c)
        sup.append(_make_ctrl_pr())
        return ssup

    # Fenced (parentheses, brackets)
    def _conv_mfenced(self, elem):
        open_p = elem.get('open', '(')
        close_p = elem.get('close', ')')
        seps = elem.get('separators', ',')
        results = [_make_math_run(open_p, italic=False, normal=True)]
        for i, child in enumerate(list(elem)):
            if i > 0:
                sep = seps[i - 1] if i - 1 < len(seps) else ','
                results.append(_make_math_run(sep, italic=False, normal=True))
            results.extend(self._convert_children(child))
        results.append(_make_math_run(close_p, italic=False, normal=True))
        return results


def latex_to_omml(latex_str: str) -> etree._Element:
    """Convert a LaTeX string to an OMML XML element."""
    try:
        mathml = _latex_to_mathml(latex_str)
    except Exception as e:
        raise ValueError(f"LaTeX 解析失败: {e}")
    return MathMLToOMML().convert(mathml)


def create_formula_paragraph(omath_element, eq_number: str | None = None, centered: bool = True):
    """Create a detached <w:p> element containing the OMML formula."""
    new_p = etree.Element(_w('p'))
    pPr = etree.SubElement(new_p, _w('pPr'))

    if eq_number:
        tabs = etree.SubElement(pPr, _w('tabs'))
        tab = etree.SubElement(tabs, _w('tab'))
        tab.set(_w('val'), 'right')
        tab.set(_w('pos'), '8300')

    if centered:
        jc = etree.SubElement(pPr, _w('jc'))
        jc.set(_w('val'), 'center')

    omp = etree.SubElement(new_p, _m('oMathPara'))
    omppr = etree.SubElement(omp, _m('oMathParaPr'))
    if centered:
        mjc = etree.SubElement(omppr, _m('jc'))
        mjc.set(_m('val'), 'center')
    omp.append(omath_element)

    if eq_number:
        xml_space = '{http://www.w3.org/XML/1998/namespace}space'
        tab_run = etree.SubElement(new_p, _w('r'))
        etree.SubElement(tab_run, _w('tab'))
        num_run = etree.SubElement(new_p, _w('r'))
        t = etree.SubElement(num_run, _w('t'))
        t.set(xml_space, 'preserve')
        t.text = eq_number

    return new_p
