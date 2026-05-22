"""文本提取模块 — 纯库函数"""
import json
from lib.utils import emu_to_cm


def extract_text(doc, start=None, end=None, section=None, output=None):
    para_range = None
    if section:
        sec = doc.find_section(title=section)
        if sec is None:
            return {"error": f"未找到章节: {section}"}
        para_range = sec["para_range"]
    paragraphs = []
    for p in doc.paragraphs:
        idx = p["index"]
        if start is not None and idx < start: continue
        if end is not None and idx > end: continue
        if para_range and (idx < para_range[0] or idx > para_range[1]): continue
        paragraphs.append({
            "index": p["index"], "text": p["text"], "style": p["style"],
            "level": p["level"], "chapter_path": p.get("chapter_path", ""),
        })
    style_defs = _extract_style_definitions(doc)
    page_setup = _extract_page_setup(doc)
    tables = [{"index": t["index"], "header": t["header"], "rows": t["rows"], "cols": t["cols"]} for t in doc.tables]
    result = {
        "total_paragraphs": len(paragraphs),
        "paragraphs": paragraphs,
        "style_definitions": style_defs,
        "page_setup": page_setup,
        "tables": tables,
    }
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def _extract_style_definitions(doc):
    NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    styles = {}
    for style in doc.doc.styles:
        if not hasattr(style, 'type') or style.type is None: continue
        if str(style.type) != 'PARAGRAPH (1)' and style.type != 1: continue
        name = style.name
        info = {}
        font = style.font; pf = style.paragraph_format
        rPr = style.element.find(f'{NS}rPr')
        if rPr is not None:
            rFonts = rPr.find(f'{NS}rFonts')
            if rFonts is not None:
                east = rFonts.get(f'{NS}eastAsia')
                ascii_f = rFonts.get(f'{NS}ascii')
                if ascii_f: info["font_ascii"] = ascii_f
                if east: info["font_eastAsia"] = east
        if font.name and "font_ascii" not in info: info["font_ascii"] = font.name
        if font.size and font.size.pt: info["size_pt"] = round(font.size.pt, 1)
        if font.bold is not None: info["bold"] = font.bold
        if font.italic is not None: info["italic"] = font.italic
        if pf and pf.alignment is not None:
            from lib.utils import alignment_to_str
            info["alignment"] = alignment_to_str(pf.alignment)
        if pf and pf.line_spacing: info["line_spacing"] = pf.line_spacing
        if pf and pf.first_line_indent:
            cm = emu_to_cm(pf.first_line_indent)
            if cm: info["first_line_indent_cm"] = cm
        pPr = style.element.find(f'{NS}pPr')
        if pPr is not None:
            spacing = pPr.find(f'{NS}spacing')
            if spacing is not None:
                before = spacing.get(f'{NS}before')
                after = spacing.get(f'{NS}after')
                if before: info["space_before_pt"] = round(int(before) / 20.0, 1)
                if after: info["space_after_pt"] = round(int(after) / 20.0, 1)
        if info: styles[name] = info
    return styles


def _extract_page_setup(doc):
    sections = []
    for i, sec in enumerate(doc.doc.sections):
        sections.append({
            "page_width_cm": emu_to_cm(sec.page_width),
            "page_height_cm": emu_to_cm(sec.page_height),
            "margin_top_cm": emu_to_cm(sec.top_margin),
            "margin_bottom_cm": emu_to_cm(sec.bottom_margin),
            "margin_left_cm": emu_to_cm(sec.left_margin),
            "margin_right_cm": emu_to_cm(sec.right_margin),
        })
    return sections


def extract_rules(doc, output=None):
    page = _extract_page_setup(doc)
    styles = _extract_style_definitions(doc)
    result = {"page": page[0] if page else {}, "styles": styles}
    if output:
        try:
            import yaml
            with open(output, 'w', encoding='utf-8') as f:
                yaml.dump(result, f, allow_unicode=True, default_flow_style=False)
        except ImportError:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    return result
