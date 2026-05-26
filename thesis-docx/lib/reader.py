"""读取模块 — 纯库函数，无 argparse 依赖

子模块：
  reader_loc.py     — read_location（段落定位）
  reader_table.py   — read_table / read_tables / read_table_context + 边框/字体检测
  reader_media.py   — read_image / read_images / read_formulas / read_comments
  reader_full.py    — read_full（全文地图）

本文件保留：chapter/paragraph/section/stats/page_setup 的读取。
"""
import re
from lxml import etree as _etree
from lib.utils import emu_to_cm
from lib.reader_loc import read_location
from lib.reader_table import read_table, read_tables, read_table_context
from lib.reader_media import read_image, read_images, read_formulas, read_comments
from lib.reader_full import read_full

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def read_structure(doc, format='tree', verify=False):
    """输出章节树。format: 'tree' 或 'flat'。verify=True 时附加样式异常标注。"""
    sections = doc.sections_tree
    if format == 'flat':
        flat = []
        def flatten(nodes):
            for node in nodes:
                flat.append({
                    "level": node["level"],
                    "title": node["title"],
                    "para_index": node["para_index"],
                    "char_count": node["char_count"],
                })
                flatten(node["children"])
        flatten(sections)
        result = {"sections": flat}
    else:
        result = {"sections": _clean_sections(sections)}

    if verify:
        from lib.checker import check_heading_rules, check_caption_numbering, check_chapter_sequence
        from lib.styles import get_default_rules
        rules = get_default_rules()
        issues = check_heading_rules(doc, rules)
        for issue in issues:
            idx = issue.get("para_index")
            if idx is not None:
                p = doc.get_para(idx)
                if p:
                    issue["section"] = p.get("chapter_path", "")
        issues += check_caption_numbering(doc)
        issues += check_chapter_sequence(doc)
        result["verify"] = issues if issues else []
    return result


def _clean_sections(nodes):
    result = []
    for node in nodes:
        n = {
            "level": node["level"],
            "title": node["title"],
            "para_index": node["para_index"],
            "char_count": node["char_count"],
        }
        n["children"] = _clean_sections(node["children"]) if node["children"] else []
        result.append(n)
    return result


def read_paragraph(doc, index, with_format=False, deep=False):
    info = doc.get_para(index)
    if info is None:
        return {"error": f"段落索引 {index} 超出范围 (0-{len(doc.paragraphs)-1})"}
    result = {
        "index": info["index"],
        "text": info["text"],
        "style": info["style"],
        "level": info["level"],
    }
    if with_format or deep:
        result.update({
            "alignment": info["alignment"],
            "line_spacing": info["line_spacing"],
            "first_line_indent": info["first_line_indent"],
            "runs": info["runs"],
            "has_image": info["has_image"],
            "image_ids": info["image_ids"],
            "chapter_path": info["chapter_path"],
            "char_count": info["char_count"],
        })
    if deep:
        loc = read_location(doc, index)
        if "error" not in loc:
            result["section_path"] = loc.get("section_path", "")
        context = {}
        for offset in [-1, 1]:
            idx = index + offset
            if 0 <= idx < len(doc.paragraphs):
                cp = doc.get_para(idx)
                if cp and cp["text"].strip():
                    label = "before" if offset == -1 else "after"
                    context[label] = cp["text"][:200]
        if context:
            result["context"] = context
    return result


def read_paragraphs(doc, start, end, with_format=False):
    if start < 0 or end >= len(doc.paragraphs):
        return {"error": f"范围 ({start}-{end}) 超出有效范围 (0-{len(doc.paragraphs)-1})"}
    paras = doc.paragraphs[start:end + 1]
    if with_format:
        items = [{
            "index": p["index"], "text": p["text"], "style": p["style"],
            "level": p["level"], "char_count": p["char_count"],
            "alignment": p["alignment"], "line_spacing": p["line_spacing"],
            "first_line_indent": p["first_line_indent"], "runs": p["runs"],
            "has_image": p["has_image"], "chapter_path": p["chapter_path"],
        } for p in paras]
    else:
        items = [{
            "index": p["index"], "text": p["text"], "style": p["style"],
            "level": p["level"], "char_count": p["char_count"],
        } for p in paras]
    return {"range": [start, end], "count": len(items), "paragraphs": items}


def read_section(doc, title=None, level=None, index=None, deep=False, verify=False):
    """读取章节内容。deep=True 时展开完整格式、表格、图片、公式信息。

    安全限制（防上下文爆炸）：
    - 章节字数 > 3000 时拒绝 deep 模式，提示用更细的子节
    - 段落数 > 40 时同样拒绝
    """
    if deep:
        result = _read_section_deep(doc, title=title, level=level, index=index)
        if "error" in result:
            return result
        if verify:
            result["verify"] = _verify_section_body(doc, result.get("section", {}))
        return result
    section = doc.find_section(title=title, level=level, index=index)
    if section is None:
        return {"error": "未找到匹配的章节"}
    paras = doc.get_section_paras(section)
    result = {
        "section": {
            "level": section["level"], "title": section["title"],
            "para_index": section["para_index"], "para_range": section["para_range"],
            "char_count": section["char_count"],
        },
        "paragraphs": [{
            "index": p["index"], "text": p["text"],
            "style": p["style"], "level": p["level"], "char_count": p["char_count"],
        } for p in paras],
    }
    if verify:
        result["verify"] = _verify_section_body(doc, section)
    return result


def _verify_section_body(doc, section):
    if not section:
        return []
    from lib.checker import check_body_rules
    from lib.styles import get_default_rules
    rules = get_default_rules()
    issues = check_body_rules(doc, rules)
    if not issues:
        return []
    start, end = section.get("para_range", (0, len(doc.paragraphs)))
    return [i for i in issues if start <= i.get("para_index", -1) <= end]


def _read_section_deep(doc, title=None, level=None, index=None):
    """deep 模式：完整展开一节，含格式/表格/图片/公式。"""
    section = doc.find_section(title=title, level=level, index=index)
    if section is None:
        return {"error": "未找到匹配的章节"}

    cc = section["char_count"]
    start, end = section["para_range"]
    para_count = end - start + 1

    from lib.styles import MAX_DEEP_CHARS, MAX_DEEP_PARAS
    max_chars = MAX_DEEP_CHARS
    max_paras = MAX_DEEP_PARAS
    if cc > max_chars or para_count > max_paras:
        issues = []
        if cc > max_chars:
            issues.append(f"章节字数 {cc} > 上限 {max_chars}")
        if para_count > max_paras:
            issues.append(f"段落数 {para_count} > 上限 {max_paras}")
        children = section.get("children", [])
        subs = []
        for c in children:
            subs.append(f"  「{c['title']}」（{c['char_count']}字，{c['para_range'][1]-c['para_range'][0]+1}段）")
        hint = "\n".join(subs) if subs else "  （无更细子节，请用段落范围缩小）"
        return {
            "error": f"章节过大，deep 模式拒绝展开",
            "detail": "；".join(issues),
            "suggestion": f"请用 --section 指定子节：\n{hint}",
            "section_info": {
                "title": section["title"], "char_count": cc,
                "para_count": para_count, "para_range": [start, end],
            },
        }

    paras_info = []
    for pi in range(start, end + 1):
        p = doc.get_para(pi)
        if p is None:
            continue
        text = p["text"]
        info = {
            "index": p["index"],
            "text": text,
            "style": p["style"],
            "level": p["level"],
            "chars": len(text),
        }
        info["runs"] = p["runs"]
        info["alignment"] = p["alignment"]
        info["line_spacing"] = p["line_spacing"]
        info["first_line_indent"] = p["first_line_indent"]
        paras_info.append(info)

    from lib.reader_table import extract_table_borders, extract_table_cell_fonts

    tables_in_range = []
    for tbl in doc.tables:
        tp = tbl["para_index_approx"]
        if start <= tp <= end:
            tables_in_range.append(tbl)

    images_in_range = []
    for img in doc.images:
        if start <= img["para_index"] <= end:
            images_in_range.append(img)

    formulas_in_range = []
    formula_placeholder = re.compile(r'FORMULA_\d+_\d+')
    M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
    for pi in range(start, end + 1):
        p = doc.get_para(pi)
        if p is None:
            continue
        if formula_placeholder.search(p["text"]):
            formulas_in_range.append({
                "para_index": pi, "type": "placeholder",
                "text": p["text"][:100],
            })
        elem = doc.raw_paragraphs[pi]._element
        xml_str = str(_etree.tostring(elem, encoding='unicode'))
        if 'm:oMath' in xml_str or 'm:oMathPara' in xml_str:
            ns = {'m': M_NS}
            math_text = ""
            for omath in elem.findall('.//m:oMath', ns):
                parts = []
                for r in omath.findall('.//m:r', ns):
                    t = r.find('m:t', ns)
                    if t is not None and t.text:
                        parts.append(t.text)
                math_text += ''.join(parts)
            formulas_in_range.append({
                "para_index": pi, "type": "OMML",
                "content": math_text or p["text"][:100],
                "text": p["text"][:100],
            })

    result = {
        "section": {
            "level": section["level"], "title": section["title"],
            "para_index": section["para_index"], "para_range": [start, end],
            "char_count": cc,
        },
        "paragraphs": paras_info,
    }

    if tables_in_range:
        result["tables"] = []
        for t in tables_in_range:
            tbl_info = {
                "index": t["index"], "shape": f"{t['rows']}x{t['cols']}",
                "header": t["header"], "data": t["data"],
            }
            if t["index"] < len(doc.raw_tables):
                raw_tbl = doc.raw_tables[t["index"]]
                borders = extract_table_borders(raw_tbl)
                if borders:
                    tbl_info["format"] = borders
                cell_fonts = extract_table_cell_fonts(raw_tbl)
                if cell_fonts:
                    tbl_info["cell_styles"] = cell_fonts
            result["tables"].append(tbl_info)
    if images_in_range:
        result["images"] = []
        for img in images_in_range:
            img_info = {
                "para_index": img["para_index"], "r_id": img["r_id"],
                "caption": img.get("nearby_caption") or "（无标题）",
                "width_cm": img.get("width_cm"), "height_cm": img.get("height_cm"),
                "format": img["format"],
            }
            pi = img["para_index"]
            if 0 <= pi < len(doc.raw_paragraphs):
                p_elem = doc.raw_paragraphs[pi]._element
                DW_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
                inline_elems = p_elem.findall(f'.//{{{DW_NS}}}inline')
                anchor_elems = p_elem.findall(f'.//{{{DW_NS}}}anchor')
                if inline_elems:
                    img_info["layout"] = "inline"
                elif anchor_elems:
                    img_info["layout"] = "floating"
                else:
                    img_info["layout"] = "unknown"
            p_text_here = doc.get_para(pi)
            is_placeholder = p_text_here and "IMAGE_" in p_text_here["text"]
            if is_placeholder:
                img_info["note"] = "图片占位符（未嵌入实际图片，仅占位文本 IMAGE_X_X）"
            result["images"].append(img_info)
    if formulas_in_range:
        result["formulas"] = formulas_in_range

    result["_deep"] = True
    result["_safeguard"] = {
        "max_chars": max_chars, "max_paras": max_paras,
        "message": f"deep 模式限 {max_chars} 字/{max_paras} 段，"
                   f"过大章节请用 --section 指定子节或 --range",
    }
    return result


def read_stats(doc):
    paras = doc.paragraphs
    total_chars = sum(p["char_count"] for p in paras)
    styles_used = {}
    for p in paras:
        style = p["style"]
        styles_used[style] = styles_used.get(style, 0) + 1
    h_counts = {}
    for p in paras:
        if p["level"] is not None:
            key = f"h{p['level']}_count"
            h_counts[key] = h_counts.get(key, 0) + 1
    chapter_breakdown = []
    for section in doc.sections_tree:
        chapter_breakdown.append({
            "title": section["title"], "level": section["level"],
            "char_count": section["char_count"], "para_index": section["para_index"],
        })
        for child in section.get("children", []):
            chapter_breakdown.append({
                "title": child["title"], "level": child["level"],
                "char_count": child["char_count"], "para_index": child["para_index"],
            })
    body_paras = [p for p in paras if p["style"] == "Normal" and p["text"].strip()]
    avg_body_len = round(sum(p["char_count"] for p in body_paras) / max(len(body_paras), 1), 1)
    numbered_captions = 0
    unnumbered_captions = 0
    for p in paras:
        if p["style"] == "Caption":
            if re.match(r'^(图|表)\s*\d', p["text"]):
                numbered_captions += 1
            else:
                unnumbered_captions += 1
    ref_count = 0
    try:
        from lib.reference import list_references
        ref_result = list_references(doc)
        ref_count = ref_result.get("total", 0) if "error" not in ref_result else 0
    except Exception:
        pass
    return {
        "total_paragraphs": len(paras),
        "total_chars": total_chars,
        "total_images": len(doc.images),
        "total_tables": len(doc.tables),
        "total_references": ref_count,
        "sections": h_counts,
        "styles_used": styles_used,
        "chapter_breakdown": chapter_breakdown[:30],
        "body_paragraphs": len(body_paras),
        "avg_body_paragraph_length": avg_body_len,
        "numbered_captions": numbered_captions,
        "unnumbered_captions": unnumbered_captions,
    }


def read_page_setup(doc, verify=False):
    result = []
    for i, section in enumerate(doc.doc.sections):
        result.append({
            "section_index": i,
            "page_width_cm": emu_to_cm(section.page_width),
            "page_height_cm": emu_to_cm(section.page_height),
            "margin_top_cm": emu_to_cm(section.top_margin),
            "margin_bottom_cm": emu_to_cm(section.bottom_margin),
            "margin_left_cm": emu_to_cm(section.left_margin),
            "margin_right_cm": emu_to_cm(section.right_margin),
            "header_distance_cm": emu_to_cm(section.header_distance),
            "footer_distance_cm": emu_to_cm(section.footer_distance),
            "orientation": str(section.orientation) if section.orientation else "portrait",
        })
    out = {"sections": result}
    if verify:
        from lib.checker import check_page_setup_rules
        from lib.styles import get_default_rules
        rules = get_default_rules()
        issues = check_page_setup_rules(doc, rules)
        out["verify"] = issues if issues else []
    return out
