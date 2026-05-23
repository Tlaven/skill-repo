"""读取模块 — 纯库函数，无 argparse 依赖"""
import os
import zipfile
import xml.etree.ElementTree as ET
from lib.core import ThesisDoc
from lib.utils import emu_to_cm

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
        from lib.checker import _check_heading_rules
        from lib.styles import get_default_rules
        rules = get_default_rules()
        issues, _ = _check_heading_rules(doc, rules)
        # Add section path to each issue
        for issue in issues:
            idx = issue.get("para_index")
            if idx is not None:
                p = doc.get_para(idx)
                if p:
                    issue["section"] = p.get("chapter_path", "")
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
        # 章节路径
        loc = read_location(doc, index)
        if "error" not in loc:
            result["section_path"] = loc.get("section_path", "")
        # 上下文段落（前后各 1 段）
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
        if "error" in result or verify:
            return result
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
    from lib.checker import _check_body_rules
    from lib.styles import get_default_rules
    rules = get_default_rules()
    issues, _ = _check_body_rules(doc, rules)
    if not issues:
        return []
    # Filter to issues within this section's range
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

    # 安全限制
    max_chars = 3000
    max_paras = 40
    if cc > max_chars or para_count > max_paras:
        issues = []
        if cc > max_chars:
            issues.append(f"章节字数 {cc} > 上限 {max_chars}")
        if para_count > max_paras:
            issues.append(f"段落数 {para_count} > 上限 {max_paras}")
        # 找子节
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

    # 收集段落信息（含 run 级格式）
    from lxml import etree as _etree
    import re
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
        # 格式信息（deep 模式下始终包含）
        info["runs"] = p["runs"]
        info["alignment"] = p["alignment"]
        info["line_spacing"] = p["line_spacing"]
        info["first_line_indent"] = p["first_line_indent"]
        paras_info.append(info)

    # 收集段落下表格
    tables_in_range = []
    for tbl in doc.tables:
        tp = tbl["para_index_approx"]
        if start <= tp <= end:
            tables_in_range.append(tbl)

    # 收集段落下图片
    images_in_range = []
    for img in doc.images:
        if start <= img["para_index"] <= end:
            images_in_range.append(img)

    # 收集段落下公式（OMML + 占位符）
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
            # 从 OMML 结构提取公式数学内容
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
            # 表格格式：边框 + 单元格文字样式
            if t["index"] < len(doc.raw_tables):
                raw_tbl = doc.raw_tables[t["index"]]
                borders = _extract_table_borders(raw_tbl)
                if borders:
                    tbl_info["format"] = borders
                cell_fonts = _extract_table_cell_fonts(raw_tbl)
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
            # 解析图片布局方式
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
            # 检测是否为占位符（IMAGE_X_X 文本，非真实嵌入图片）
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


def read_image(doc, id, extract=False, output_dir=None, deep=False):
    img = None
    for image in doc.images:
        if image["r_id"] == id:
            img = dict(image)
            break
    if img is None:
        return {"error": f"未找到图片 {id}"}
    if extract and output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for rel in doc.doc.part.rels.values():
            if rel.rId == id:
                target = rel.target_part
                filename = os.path.basename(img["filename"])
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(target.blob)
                img["extracted_to"] = filepath
                break
    if deep:
        # 布局方式
        pi = img["para_index"]
        DW_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
        p_elem = doc.raw_paragraphs[pi]._element
        inline_elems = p_elem.findall(f'.//{{{DW_NS}}}inline')
        anchor_elems = p_elem.findall(f'.//{{{DW_NS}}}anchor')
        img["layout"] = "inline" if inline_elems else ("floating" if anchor_elems else "unknown")
        # 章节位置
        loc = read_location(doc, pi)
        if "error" not in loc:
            img["section_path"] = loc.get("section_path", "")
        # 上下文
        context = {}
        for offset in [-1, 1]:
            idx = pi + offset
            if 0 <= idx < len(doc.paragraphs):
                cp = doc.get_para(idx)
                if cp and cp["text"].strip():
                    context["before" if offset == -1 else "after"] = cp["text"][:150]
        if context:
            img["context"] = context
        # 占位符检测
        p_here = doc.get_para(pi)
        if p_here and "IMAGE_" in p_here["text"]:
            img["note"] = "图片占位符（IMAGE_X_X 文本，未嵌入实际图片）"
    return img


def read_images(doc):
    return {"total": len(doc.images), "images": doc.images}


def read_table(doc, index, deep=False):
    if index < 0 or index >= len(doc.tables):
        return {"error": f"表格索引 {index} 超出范围 (0-{len(doc.tables)-1})"}
    tbl = doc.tables[index]
    result = {
        "index": tbl["index"], "shape": f"{tbl['rows']}x{tbl['cols']}",
        "header": tbl["header"], "data": tbl["data"],
        "para_index_approx": tbl["para_index_approx"],
    }
    if deep:
        # 边框 + 样式
        if index < len(doc.raw_tables):
            raw_tbl = doc.raw_tables[index]
            borders = _extract_table_borders(raw_tbl)
            if borders:
                result["format"] = borders
            cell_fonts = _extract_table_cell_fonts(raw_tbl)
            if cell_fonts:
                result["cell_styles"] = cell_fonts
        # 所在章节
        loc = read_location(doc, tbl["para_index_approx"])
        if "error" not in loc:
            result["section"] = loc.get("section_path", "")
        # 附近图标题
        caption = None
        for offset in range(-3, 4):
            idx = tbl["para_index_approx"] + offset
            if 0 <= idx < len(doc.paragraphs):
                p = doc.get_para(idx)
                if p and p["style"] == "Caption":
                    caption = p["text"]
                    break
        result["caption"] = caption or "（未找到 Caption 标题）"
        # 上下文段落
        ctx = []
        for offset in [-1, 0, 1]:
            idx = tbl["para_index_approx"] + offset
            if 0 <= idx < len(doc.paragraphs):
                p = doc.get_para(idx)
                if p and p["text"].strip():
                    ctx.append({"index": idx, "text": p["text"][:150], "style": p["style"]})
        if ctx:
            result["context_paragraphs"] = ctx
        result["_deep"] = True
    return result


def read_tables(doc):
    return {
        "total": len(doc.tables),
        "tables": [{
            "index": t["index"], "rows": t["rows"], "cols": t["cols"],
            "header": t["header"], "para_index_approx": t["para_index_approx"],
        } for t in doc.tables],
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
        from lib.checker import _check_page_setup_rules
        from lib.styles import get_default_rules
        rules = get_default_rules()
        issues, _ = _check_page_setup_rules(doc, rules)
        out["verify"] = issues if issues else []
    return out


def read_stats(doc):
    import re as _re
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
            if _re.match(r'^(图|表)\s*\d', p["text"]):
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


def read_comments(doc):
    filepath = doc.filepath
    with zipfile.ZipFile(filepath) as z:
        if 'word/comments.xml' not in z.namelist():
            return {"total": 0, "comments": []}
        with z.open('word/comments.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
        comments = []
        for c in root.findall(f'{{{W_NS}}}comment'):
            cid = c.get(f'{{{W_NS}}}id', '')
            author = c.get(f'{{{W_NS}}}author', '')
            date = c.get(f'{{{W_NS}}}date', '')
            initials = c.get(f'{{{W_NS}}}initials', '')
            texts = []
            for t in c.iter(f'{{{W_NS}}}t'):
                if t.text:
                    texts.append(t.text)
            comments.append({
                "id": cid, "author": author, "date": date,
                "initials": initials, "text": ''.join(texts),
            })
        with z.open('word/document.xml') as df:
            doctree = ET.parse(df)
            docroot = doctree.getroot()
        body = docroot.find(f'.//{{{W_NS}}}body')
        comment_ranges = {}
        comment_para_map = {}
        active = set()
        if body is not None:
            for pi, p_elem in enumerate(body.findall(f'{{{W_NS}}}p')):
                for elem in p_elem.iter():
                    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if tag == 'commentRangeStart':
                        cid = elem.get(f'{{{W_NS}}}id', '')
                        active.add(cid)
                        comment_ranges.setdefault(cid, [])
                    elif tag == 'commentRangeEnd':
                        cid = elem.get(f'{{{W_NS}}}id', '')
                        active.discard(cid)
                    elif tag == 'commentReference':
                        cid = elem.get(f'{{{W_NS}}}id', '')
                        if cid not in comment_para_map:
                            comment_para_map[cid] = pi
                    elif tag == 't' and elem.text:
                        for cid in list(active):
                            comment_ranges.setdefault(cid, []).append(elem.text)
        paras = doc.paragraphs
        result = []
        for c in comments:
            cid = c["id"]
            ref_text = ''.join(comment_ranges.get(cid, []))
            para_idx = comment_para_map.get(cid)
            ctx = None
            if para_idx is not None:
                ctx_parts = {}
                if para_idx > 0 and paras[para_idx - 1]["text"].strip():
                    ctx_parts["before"] = paras[para_idx - 1]["text"][:200]
                ctx_parts["anchor"] = paras[para_idx]["text"][:200]
                if para_idx < len(paras) - 1 and paras[para_idx + 1]["text"].strip():
                    ctx_parts["after"] = paras[para_idx + 1]["text"][:200]
                ctx = ctx_parts
            result.append({
                "id": int(cid), "author": c["author"], "date": c["date"],
                "initials": c["initials"], "selected_text": ref_text or None,
                "comment": c["text"], "paragraph_index": para_idx, "context": ctx,
            })
        result.sort(key=lambda x: x["id"])
        return {"total": len(result), "comments": result}


def read_location(doc, paragraph):
    """查询段落索引所在的章节路径。"""
    if paragraph < 0 or paragraph >= len(doc.paragraphs):
        return {"error": f"段落索引 {paragraph} 超出范围 (0-{len(doc.paragraphs)-1})"}

    p = doc.get_para(paragraph)
    if p is None:
        return {"error": f"段落 {paragraph} 不存在"}

    # 找到最近的在前面的标题
    def _find_path(nodes, depth=0):
        for node in nodes:
            start, end = node["para_range"]
            if start <= paragraph <= end:
                path = {"title": node["title"], "level": node["level"], "para_range": [start, end]}
                children = node.get("children", [])
                for child in children:
                    cs, ce = child["para_range"]
                    if cs <= paragraph <= ce:
                        sub = _find_path([child], depth + 1)
                        if sub:
                            return {"node": path, "child": sub}
                return {"node": path}
        return None

    tree = doc.sections_tree
    loc = _find_path(tree) if tree else None

    # 构建路径字符串
    path_str = ""
    path_list = []
    if loc:
        n = loc
        while True:
            path_list.append(n["node"]["title"])
            if "child" in n:
                n = n["child"]
            else:
                break
        path_str = " > ".join(path_list)

    # 附近的图表公式
    nearby = {"images": [], "tables": [], "formulas": []}
    for img in doc.images:
        if abs(img["para_index"] - paragraph) <= 5:
            nearby["images"].append({"para_index": img["para_index"], "caption": img.get("nearby_caption", "")})
    for tbl in doc.tables:
        if abs(tbl["para_index_approx"] - paragraph) <= 5:
            nearby["tables"].append({"index": tbl["index"], "shape": f"{tbl['rows']}x{tbl['cols']}", "header": tbl["header"][:3]})
    import re
    from lxml import etree as _etree
    formula_placeholder = re.compile(r'FORMULA_\d+_\d+|IMAGE_\d+_\d+|TABLE_\d+_\d+')
    if formula_placeholder.search(p["text"]):
        nearby["formulas"].append({"para_index": paragraph, "type": "placeholder"})
    elem = doc.raw_paragraphs[paragraph]._element
    xml_str = str(_etree.tostring(elem, encoding='unicode'))
    if 'm:oMath' in xml_str or 'm:oMathPara' in xml_str:
        nearby["formulas"].append({"para_index": paragraph, "type": "OMML"})

    result = {
        "paragraph": paragraph,
        "text": p["text"][:200],
        "style": p["style"],
        "level": p["level"],
        "chars": len(p["text"]),
        "section_path": path_str or "（不在章节树中）",
    }
    if any(nearby.values()):
        result["nearby"] = {k: v for k, v in nearby.items() if v}
    return result


def read_formulas(doc, summary=False):
    """列出文档中所有公式。
    
    summary=True 时输出精简格式（类型/位置/数学概要/所在章节）。
    """
    import re
    from lxml import etree as _etree
    M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

    formula_placeholder = re.compile(r'FORMULA_\d+_\d+')
    results = []

    for p_info in doc.paragraphs:
        pi = p_info["index"]
        text = p_info["text"]
        ftype = None
        ole_obj = False

        # 检测占位符
        if formula_placeholder.search(text):
            ftype = "placeholder"
        # 检测 OMML
        elem = doc.raw_paragraphs[pi]._element
        xml_str = str(_etree.tostring(elem, encoding='unicode'))
        ommal_content = ""
        if 'm:oMath' in xml_str or 'm:oMathPara' in xml_str:
            ftype = "OMML"
            ns2 = {'m': M_NS}
            math_parts = []
            for omath in elem.findall('.//m:oMath', ns2):
                parts = []
                for r in omath.findall('.//m:r', ns2):
                    t = r.find('m:t', ns2)
                    if t is not None and t.text:
                        parts.append(t.text)
                math_parts.append(''.join(parts))
            ommal_content = ''.join(math_parts)
        # 检测 OLE 对象
        if 'w:object' in xml_str or 'o:OLEObject' in xml_str:
            ole_obj = True
            if not ftype:
                ftype = "OLE"

        if not ftype:
            continue

        if summary:
            results.append({
                "para_index": pi,
                "type": ftype,
                "text": ommal_content[:100] if ommal_content else (text[:80] if text else ""),
                "chapter": p_info.get('chapter_path', ''),
            })
            continue

        # 章节位置
        loc = read_location(doc, pi)
        section_path = loc.get("section_path", "") if "error" not in loc else ""

        # 上下文（前后段落摘要）
        context = {}
        for offset in [-1, 1]:
            idx = pi + offset
            if 0 <= idx < len(doc.paragraphs):
                rp = doc.get_para(idx)
                if rp and rp["text"].strip():
                    label = "before" if offset == -1 else "after"
                    context[label] = rp["text"][:150]

        entry = {
            "para_index": pi,
            "type": ftype,
            "section": section_path or "（未定位）",
            "text": text[:200] if text else "",
        }
        if ftype == "OMML" and ommal_content:
            entry["content"] = ommal_content
        if context:
            entry["context"] = context
        results.append(entry)

    # 去重（OMML + 占位符可能指向同一段落）
    seen = set()
    unique = []
    for r in results:
        key = (r["para_index"], r["type"] if not summary else r["para_index"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return {"total": len(unique), "formulas": unique}


def read_table_context(doc, index):
    """读取指定表格及其上下文（标题、数据、所在章节）。"""
    if index < 0 or index >= len(doc.tables):
        return {"error": f"表格索引 {index} 超出范围 (0-{len(doc.tables)-1})"}

    tbl = doc.tables[index]
    tp = tbl["para_index_approx"]

    # 查找表格所在章节
    loc_result = read_location(doc, tp)
    section_path = loc_result.get("section_path", "") if "error" not in loc_result else ""

    # 查找附近 Caption（前后 3 段）
    caption_text = None
    for offset in range(-3, 4):
        idx = tp + offset
        if 0 <= idx < len(doc.paragraphs):
            p = doc.get_para(idx)
            if p and p["style"] == "Caption":
                caption_text = p["text"]
                break

    # 上下文段落（前后各 1 段）
    context_paras = []
    for offset in [-1, 0, 1]:
        idx = tp + offset
        if 0 <= idx < len(doc.paragraphs):
            p = doc.get_para(idx)
            if p and p["text"].strip():
                context_paras.append({"index": idx, "text": p["text"][:150], "style": p["style"]})

    return {
        "table_index": index,
        "shape": f"{tbl['rows']}x{tbl['cols']}",
        "header": tbl["header"],
        "data": tbl["data"],
        "section": section_path,
        "caption": caption_text or "（未找到 Caption 标题）",
        "context_paragraphs": context_paras,
        "para_index_approx": tp,
    }


def read_full(doc, section=None, paragraphs=None):
    """输出论文完整地图或展开某一节。

    Args:
        doc: ThesisDoc 实例
        section: 展开的章节标题子串（None = 只输出地图）
        paragraphs: (start, end) 段落索引范围（覆盖 section）

    Returns:
        dict: {"map": ..., "sections": [...], "annotations": {...}}
    """
    from lib.reference import list_references
    from lib.styles import CLASSIFY_PATTERNS

    # 构建全段落索引 → 所在章节的映射
    para_to_section = {}
    def _map_sections(nodes, parent_path=""):
        for node in nodes:
            start, end = node["para_range"]
            path = node["title"]
            for i in range(start, end + 1):
                para_to_section[i] = {"title": path, "level": node["level"],
                                      "para_index": node["para_index"],
                                      "children": node.get("children", [])}
            _map_sections(node.get("children", []), path)
    _map_sections(doc.sections_tree)

    # 收集图片/表格/公式的段落索引 → 所属章节
    def _find_annotation_section(para_idx):
        """找到段落所属的最细粒度标题。"""
        if para_idx in para_to_section:
            info = para_to_section[para_idx]
            # 尝试定位到子节
            for child in _iter_children(info.get("children", [])):
                cs, ce = child["para_range"]
                if cs <= para_idx <= ce:
                    return child["title"]
            return info["title"]
        # 遍历所有标题找最近的在前面的标题
        best = None
        for p in doc.paragraphs:
            if p["level"] is not None and p["index"] <= para_idx:
                best = p["text"]
        return best or "（无标题区域）"

    def _iter_children(nodes):
        for node in nodes:
            yield node
            yield from _iter_children(node.get("children", []))

    # 收集所有非正文元素
    images = doc.images
    tables = doc.tables
    # 公式检测：OMML 和 FORMULA_X_X 占位符
    formula_paras = []
    import re
    from lxml import etree as _etree
    formula_placeholder = re.compile(r'FORMULA_\d+_\d+')
    for p in doc.paragraphs:
        if formula_placeholder.search(p["text"]):
            formula_paras.append(p["index"])
        # 也检测 OMML 公式
        elem = doc.raw_paragraphs[p["index"]]._element
        xml_str = str(_etree.tostring(elem, encoding='unicode'))
        if 'm:oMath' in xml_str or 'm:oMathPara' in xml_str:
            formula_paras.append(p["index"])

    # 构建标注索引
    annotations = {"images": [], "tables": [], "formulas": []}
    seen_formula_paras = set()
    for img in images:
        sec = _find_annotation_section(img["para_index"])
        annotations["images"].append({
            "section": sec, "para_index": img["para_index"],
            "caption": img.get("nearby_caption", ""),
            "r_id": img["r_id"],
        })
    for tbl in tables:
        sec = _find_annotation_section(tbl["para_index_approx"])
        annotations["tables"].append({
            "section": sec, "para_index": tbl["para_index_approx"],
            "header": tbl["header"][:3],
            "rows": tbl["rows"], "cols": tbl["cols"],
        })
    for fp in formula_paras:
        if fp not in seen_formula_paras:
            seen_formula_paras.add(fp)
            sec = _find_annotation_section(fp)
            annotations["formulas"].append({
                "section": sec, "para_index": fp,
            })

    # 判断是否展开模式
    expand_section = None
    expand_range = None
    if section:
        # 找匹配的章节节点
        def _find_node(nodes):
            for n in nodes:
                if section in n["title"]:
                    return n
                child = _find_node(n.get("children", []))
                if child:
                    return child
            return None
        sec_root = doc.sections_tree
        expand_node = _find_node(sec_root) if sec_root else None
        if expand_node:
            expand_range = expand_node["para_range"]
            expand_section = expand_node["title"]
    if paragraphs:
        expand_range = (paragraphs[0], paragraphs[1])
        expand_section = f"段落 {paragraphs[0]}-{paragraphs[1]}"

    # 构建地图输出
    lines = []
    total_chars = sum(p["char_count"] for p in doc.paragraphs)

    # === 页眉 ===
    lines.append(f"论文全文地图 | 总字数:{total_chars} 段落:{len(doc.paragraphs)} "
                 f"图片:{len(images)} 表格:{len(tables)} 公式:{len(annotations['formulas'])}")

    # === 前置部分 ===
    preface_titles = {"封面", "声明", "原创性声明", "授权声明"}
    skip_titles = preface_titles | {"目  录", "目录"}
    abstract_zh_idx = None
    abstract_en_idx = None
    ref_section_start = None

    # 找摘要和参考文献位置
    for p in doc.paragraphs:
        text = p["text"].strip()
        if text in ("摘  要", "摘要") and p["level"] == 1:
            abstract_zh_idx = p["index"]
        if text == "ABSTRACT" and p["level"] == 1:
            abstract_en_idx = p["index"]
        if "参考文献" in text and p["level"] == 1:
            ref_section_start = p["index"]

    # 判断一个标题段落是否属于前置/正文/后置
    def _section_zone(para):
        text = para["text"].strip()
        if para["level"] != 1:
            return None
        if text in preface_titles:
            return "preface"
        if text in ("摘  要", "摘要", "ABSTRACT"):
            return "abstract"
        if text in ("目  录", "目录"):
            return "toc"
        if "参考文献" in text:
            return "references"
        if "致谢" in text or "致  谢" in text:
            return "acknowledgements"
        if "附录" in text:
            return "appendix"
        return "chapter"

    # 输出正文结构（按 section tree）
    def _build_section_output(nodes, depth=0):
        for node in nodes:
            title = node["title"]
            cc = node["char_count"]
            start, end = node["para_range"]
            indent = "  " * depth

            # 判断区域
            heading_para = doc.get_para(node["para_index"])
            zone = _section_zone(heading_para) if heading_para else None

            # 跳过封面/声明/目录的内容
            skip_content = zone in ("preface", "toc")

            # 收集本节点下的标注
            node_ann = {"images": [], "tables": [], "formulas": []}
            for cat in annotations:
                for a in annotations[cat]:
                    sec_title = a.get("section", "")
                    # 标注章节在当前节点范围内则归属之
                    in_range = (start <= a["para_index"] <= end) if "para_index" in a else False
                    if sec_title == title or in_range:
                        node_ann[cat].append(a)

            # 输出标题行
            prefix = {"preface": "▎", "abstract": "▎", "toc": "▎",
                      "references": "▎", "acknowledgements": "▎",
                      "appendix": "▎", "chapter": "──"}.get(zone, "──")
            if skip_content:
                lines.append(f"{indent}{prefix} {title} — {zone.upper()}（跳过详细内容）")
            else:
                ann_str = ""
                if node_ann["images"]:
                    ann_str += f" [图×{len(node_ann['images'])}]"
                if node_ann["tables"]:
                    ann_str += f" [表×{len(node_ann['tables'])}]"
                if node_ann["formulas"]:
                    ann_str += f" [公式×{len(node_ann['formulas'])}]"
                lines.append(f"{indent}{prefix} {title}（{cc}字）{ann_str}")

            # 递归子节点
            children = node.get("children", [])
            if children:
                _build_section_output(children, depth + 1)

            # 展开模式：输出本节点下的正文段落
            is_expanded = (expand_range and expand_section and
                           (title == expand_section or expand_section in title))
            if is_expanded:
                for pi in range(start, end + 1):
                    p = doc.get_para(pi)
                    if p is None or p["level"] is not None:
                        continue
                    if p["index"] in [c.get("para_index") for c in children]:
                        continue  # 子标题段落已由递归处理
                    text = p["text"].strip()
                    if not text:
                        continue
                    ann_inline = ""
                    for cat in ("images", "tables", "formulas"):
                        for a in annotations[cat]:
                            if a.get("para_index") == pi:
                                if cat == "images" and a.get("caption"):
                                    ann_inline += f" [图: {a['caption']}]"
                                elif cat == "tables":
                                    ann_inline += f" [表: {' / '.join(str(h) for h in a.get('header', [])[:3])}]"
                                elif cat == "formulas":
                                    ann_inline += " [公式]"
                    display = text[:600]
                    if len(text) > 600:
                        display += "…"
                    lines.append(f"{indent}  {display}{ann_inline}")

    # 检测前置标题段落（无 heading level 的封面/声明等）
    preface_found = False
    for p in doc.paragraphs:
        text = p["text"].strip()
        if text in preface_titles and p["level"] is not None:
            preface_found = True
            break
    # 如果 sections_tree 没有包含封面/声明，手动标注
    if not preface_found:
        for p in doc.paragraphs[:15]:
            text = p["text"].strip()
            if text in preface_titles:
                lines.append(f"▎ {text} — PREFACE（跳过详细内容）")

    # 输出正文树
    if doc.sections_tree:
        _build_section_output(doc.sections_tree)

    # 输出参考文献展开
    ref_result = list_references(doc)
    if "error" not in ref_result and ref_result.get("references"):
        lines.append("")
        lines.append(f"── 参考文献（{ref_result['total']}条）")
        for r in ref_result["references"][:30]:
            short = r["text"][:120]
            if len(r["text"]) > 120:
                short += "…"
            lines.append(f"  {short}")

    # 返回数据
    result_text = "\n".join(lines)

    # 收集标注汇总
    ann_summary = {}
    for cat in ("images", "tables", "formulas"):
        if annotations[cat]:
            ann_summary[cat] = []
            for a in annotations[cat]:
                entry = {"section": a["section"], "para_index": a["para_index"]}
                if cat == "images" and a.get("caption"):
                    entry["caption"] = a["caption"]
                if cat == "tables":
                    entry["header"] = a["header"]
                    entry["shape"] = f"{a['rows']}x{a['cols']}"
                ann_summary[cat].append(entry)

    return {
        "map": result_text,
        "stats": {
            "total_chars": total_chars,
            "total_paragraphs": len(doc.paragraphs),
            "total_images": len(images),
            "total_tables": len(tables),
            "total_formulas": len(annotations["formulas"]),
        },
        "annotations": ann_summary if ann_summary else None,
        "expand_section": expand_section if expand_section else None,
        "expand_range": list(expand_range) if expand_range else None,
    }


def _extract_table_borders(table):
    """提取 Word 表格的边框信息，判断是否为三线表。"""
    W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    tblPr = table._tbl.find(f'{{{W}}}tblPr')
    if tblPr is None:
        return {"note": "无 tblPr"}

    # 检查是否有命名表格样式
    tblStyle = tblPr.find(f'{{{W}}}tblStyle')
    style_name = tblStyle.get(f'{{{W}}}val') if tblStyle is not None else None

    borders = tblPr.find(f'{{{W}}}tblBorders')
    if borders is None:
        if style_name:
            return {"style": style_name, "note": "边框由表格样式控制（未在 tblPr 显式定义）"}
        return {"note": "无显式边框设置（默认无边框）"}

    result = {"style": style_name} if style_name else {}
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        elem = borders.find(f'{{{W}}}{side}')
        if elem is not None:
            val = elem.get(f'{{{W}}}val')
            sz = elem.get(f'{{{W}}}sz')
            if val and val != 'none':
                result[side] = {"style": val, "size": int(sz) if sz else 0}
            else:
                result[side] = {"style": "none"}

    # 判断三线表：top+bottom+insideH 有框线，left+right+insideV 无框线
    has_top = result.get('top', {}).get('style') not in (None, 'none')
    has_bottom = result.get('bottom', {}).get('style') not in (None, 'none')
    has_insideH = result.get('insideH', {}).get('style') not in (None, 'none')
    no_left = result.get('left', {}).get('style') in (None, 'none')
    no_right = result.get('right', {}).get('style') in (None, 'none')
    no_insideV = result.get('insideV', {}).get('style') in (None, 'none')
    result['_is_three_line'] = has_top and has_bottom and has_insideH and no_left and no_right and no_insideV
    return result


def _extract_table_cell_fonts(table):
    """提取表格各行的文字样式（字体/字号/加粗），判断内容样式是否统一。"""
    from lib.utils import get_run_font_info
    W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    rows = table._tbl.findall(f'{{{W}}}tr')
    if not rows:
        return None

    sample_rows = []
    # 取第1行+第2行（头行 + 首条数据行）
    for ri in [0, 1]:
        if ri >= len(rows):
            continue
        row = rows[ri]
        cells = row.findall(f'{{{W}}}tc')
        cell_fonts = []
        for ci, cell in enumerate(cells):
            if ci >= 3:  # 最多取前3列
                break
            paras = cell.findall(f'{{{W}}}p')
            for p in paras:
                runs = p.findall(f'{{{W}}}r')
                for r in runs[:1]:  # 每单元格取第一个 run
                    from lxml import etree as _etree
                    rPr = r.find(f'{{{W}}}rPr')
                    font_info = {"font": None, "font_east": None, "size": None, "bold": None}
                    if rPr is not None:
                        rFonts = rPr.find(f'{{{W}}}rFonts')
                        if rFonts is not None:
                            font_info["font"] = rFonts.get(f'{{{W}}}ascii')
                            font_info["font_east"] = rFonts.get(f'{{{W}}}eastAsia')
                        sz = rPr.find(f'{{{W}}}sz')
                        if sz is not None:
                            val = sz.get(f'{{{W}}}val')
                            if val:
                                font_info["size"] = round(int(val) / 2, 1)
                        b = rPr.find(f'{{{W}}}b')
                        if b is not None:
                            b_val = b.get(f'{{{W}}}val')
                            font_info["bold"] = b_val != '0' if b_val else True
                    cell_fonts.append(font_info)
        sample_rows.append({"row": ri, "cells": cell_fonts})

    # 判断所有单元格字体是否一致
    all_fonts = set()
    all_sizes = set()
    for row_data in sample_rows:
        for c in row_data["cells"]:
            if c["font"]: all_fonts.add(c["font"])
            if c["font_east"]: all_fonts.add(c["font_east"])
            if c["size"]: all_sizes.add(c["size"])

    uniform = len(all_fonts) <= 1 and len(all_sizes) <= 1
    common_font = list(all_fonts)[0] if len(all_fonts) == 1 else (all_fonts if all_fonts else "（全部继承表格样式）")
    common_size = list(all_sizes)[0] if len(all_sizes) == 1 else (all_sizes if all_sizes else "（全部继承表格样式）")
    return {
        "samples": sample_rows,
        "uniform": uniform,
        "common_font": common_font,
        "common_size": common_size,
        "note": "null = 继承表格样式，非直接设置" if uniform and not all_fonts else None,
    }

