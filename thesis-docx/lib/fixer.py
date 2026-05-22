"""格式修复模块 — 纯库函数，无 argparse 依赖"""
from docx.shared import Pt, Cm
from lxml import etree
from lib.utils import NSMAP, get_output_path, str_to_alignment, find_toc_range
from lib.styles import classify_paragraph, ROLE_TO_WORD_STYLE, resolve_style
from lib.rules import load_rules


def clear_direct_formatting(para):
    """清除段落上的直接格式，让 Word 样式完全接管。跳过含图片或超链接的段落。"""
    p_element = para._element
    if p_element.findall(f'.//{{{NSMAP["w"]}}}drawing'):
        return False
    if p_element.findall(f'{{{NSMAP["w"]}}}hyperlink'):
        return False
    pPr = p_element.find(f'{{{NSMAP["w"]}}}pPr')
    if pPr is not None:
        for tag in ('ind', 'spacing', 'jc', 'rPr'):
            elem = pPr.find(f'{{{NSMAP["w"]}}}{tag}')
            if elem is not None:
                pPr.remove(elem)
    for run_elem in p_element.findall(f'{{{NSMAP["w"]}}}r'):
        rPr = run_elem.find(f'{{{NSMAP["w"]}}}rPr')
        if rPr is not None:
            run_elem.remove(rPr)
    return True


def assign_styles(doc, rules=None, preset=None, output=None, backup=False):
    """自动识别段落角色并分配 Word 样式，清除直接格式让样式接管。"""
    output_path = get_output_path(doc, output=output, backup=backup)
    assignments = _assign_styles_impl(doc, rules, preset)
    if not assignments:
        return {"total_assigned": 0, "assignments": [], "output": None}
    doc.save(output_path)
    return {"total_assigned": len(assignments), "assignments": assignments[:50], "output": output_path}


def _assign_styles_impl(doc, rules_path=None, preset=None, preserve_style_defs=False):
    """preserve_style_defs=True 时跳过样式定义覆盖（用于模板样式已替换的场景）。"""
    toc_start, toc_end = find_toc_range(doc)
    assignments = []
    for p in doc.paragraphs:
        text = p["text"].strip()
        idx = p["index"]
        style = p["style"]
        if not text:
            continue
        if idx < 13:
            continue
        if toc_start is not None and toc_end is not None:
            if toc_start <= idx < toc_end:
                continue
        role = classify_paragraph(text, index=idx)
        if role is None:
            if idx >= 26 and style in ("Normal", "Body Text"):
                role = "body_text"
            else:
                continue
        word_style = ROLE_TO_WORD_STYLE.get(role)
        if word_style and word_style != style:
            assignments.append({
                "index": idx, "role": role, "old_style": style,
                "new_style": word_style, "text": text[:50],
            })
    all_needed = set(ROLE_TO_WORD_STYLE.values())
    if not preserve_style_defs:
        ensure_word_styles(doc.doc, all_needed, rules_path, preset)
    if not assignments:
        return assignments
    for a in assignments:
        para = doc.raw_paragraphs[a["index"]]
        try:
            para.style = doc.doc.styles[a["new_style"]]
        except KeyError:
            continue
        clear_direct_formatting(para)
    return assignments


def ensure_word_styles(doc, style_names, rules_path=None, preset=None):
    """确保文档中存在所需的 Word 样式对象，并设置正确格式。"""
    _WORD_STYLE_TO_DEF = {}
    for role, ws in ROLE_TO_WORD_STYLE.items():
        if ws in style_names:
            _WORD_STYLE_TO_DEF[ws] = role
    for word_style_name in style_names:
        role = _WORD_STYLE_TO_DEF.get(word_style_name, "body")
        resolved = resolve_style(role, rules_path=rules_path, preset=preset)
        style = get_or_create_style(doc, word_style_name)
        if style is None:
            continue
        configure_style(style, resolved)


def get_or_create_style(doc, style_name):
    """获取或创建 Word 样式对象。"""
    try:
        return doc.styles[style_name]
    except KeyError:
        pass
    builtin_ids = {
        "Heading 1": 1, "Heading 2": 2, "Heading 3": 3, "Heading 4": 4,
        "Body Text": 67, "Caption": -40, "Header": -2, "Footer": -3,
    }
    try:
        from docx.enum.style import WD_STYLE_TYPE
        style = doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH, builtin_ids.get(style_name))
        try:
            base = doc.styles['Normal']
            style.base_style = base
        except Exception:
            pass
        return style
    except Exception:
        return None


def configure_style(style, resolved):
    """将 resolved 属性字典写入 Word 样式对象。"""
    font_latin = resolved.get("font", "Times New Roman")
    font_east = resolved.get("font_east", "宋体")
    style.font.name = font_latin
    style.font.size = Pt(resolved.get("size_pt", 12))
    style.font.bold = resolved.get("bold", False)
    style.font.italic = resolved.get("italic", False)
    color = resolved.get("color", "000000")
    if color:
        from docx.shared import RGBColor
        style.font.color.rgb = RGBColor.from_string(color)
    from docx.oxml.ns import qn
    rPr = style.element.find(qn('w:rPr'))
    if rPr is None:
        rPr = etree.SubElement(style.element, qn('w:rPr'))
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = etree.SubElement(rPr, qn('w:rFonts'))
    rFonts.set(qn('w:ascii'), font_latin)
    rFonts.set(qn('w:hAnsi'), font_latin)
    rFonts.set(qn('w:eastAsia'), font_east)
    rFonts.set(qn('w:cs'), font_latin)
    for attr in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        full_attr = qn(f'w:{attr}')
        if rFonts.get(full_attr) is not None:
            del rFonts.attrib[full_attr]
    pf = style.paragraph_format
    align = resolved.get("alignment")
    if align:
        pf.alignment = str_to_alignment(align)
    indent = resolved.get("first_line_indent_cm")
    if indent is not None:
        pf.first_line_indent = Cm(indent)
    else:
        pf.first_line_indent = None
    spacing = resolved.get("line_spacing")
    if spacing is not None:
        spacing_rule = resolved.get("line_spacing_rule")
        if spacing_rule == "fixed":
            from docx.enum.text import WD_LINE_SPACING
            pf.line_spacing = Pt(spacing)
            pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        else:
            pf.line_spacing = spacing
    else:
        pf.line_spacing = None
    sb = resolved.get("space_before_pt")
    if sb is not None: pf.space_before = Pt(sb)
    sa = resolved.get("space_after_pt")
    if sa is not None: pf.space_after = Pt(sa)


def fix_format(doc, rules=None, preset=None, output=None, backup=False):
    """综合格式修复：分配样式 + 清除直接格式 + 修复页面设置 + 重编引用。"""
    output_path = get_output_path(doc, output=output, backup=backup)
    fixed = []
    assignments = _assign_styles_impl(doc, rules, preset)
    if assignments:
        fixed.append({"type": "styles_assigned", "count": len(assignments)})
    _rules = load_rules(rules)
    from lib.checker import _check_page_setup_rules
    page_issues, _ = _check_page_setup_rules(doc, _rules)
    page_fixed = _fix_page_setup(doc, page_issues, _rules)
    if page_fixed:
        fixed.extend(page_fixed)
    from lib.reference import list_citations, list_references, _renumber_para_citations, _reorder_references
    from lib.checker import check_references as _check_refs
    ref_result = _check_refs(doc)
    ref_issues = ref_result.get("issues", [])
    not_in_order = [i for i in ref_issues if i.get("type") == "not_in_order"]
    if not_in_order:
        citations_result = list_citations(doc)
        order = citations_result["first_appearance_order"]
        old_to_new = {}
        for new_num, old_num in enumerate(order, 1):
            old_to_new[old_num] = new_num
        refs_result = list_references(doc)
        if "references" in refs_result:
            ref_nums = [r["number"] for r in refs_result["references"]]
            next_num = len(old_to_new) + 1
            for num in ref_nums:
                if num not in old_to_new:
                    old_to_new[num] = next_num; next_num += 1
        for p_info in doc.paragraphs:
            if not p_info["text"]: continue
            para = doc.raw_paragraphs[p_info["index"]]
            _renumber_para_citations(para, old_to_new)
        if "references" in refs_result:
            _reorder_references(doc, old_to_new, refs_result["references"])
        fixed.append({"type": "references_renumbered", "count": len(not_in_order), "mapping": old_to_new})
    if fixed:
        doc.save(output_path)
    return {"total_fixed": len(fixed), "fixes": fixed[:100], "output": output_path if fixed else None}


def fix_page_setup(doc, rules=None, output=None, backup=False):
    from lib.checker import _check_page_setup_rules
    _rules = load_rules(rules)
    output_path = get_output_path(doc, output=output, backup=backup)
    issues, _ = _check_page_setup_rules(doc, _rules)
    fixed = _fix_page_setup(doc, issues, _rules)
    if fixed:
        doc.save(output_path)
    return {"total_fixed": len(fixed), "fixes": fixed, "output": output_path if fixed else None}


def _fix_page_setup(doc, issues, rules):
    fixed = []
    page_rules = rules.get("page", {})
    for issue in issues:
        itype = issue["type"]
        section = None
        for sec in doc.doc.sections:
            if itype == "page_width" and page_rules.get("width_cm"):
                sec.page_width = Cm(page_rules["width_cm"]); section = sec
            elif itype == "page_height" and page_rules.get("height_cm"):
                sec.page_height = Cm(page_rules["height_cm"]); section = sec
            elif itype.startswith("page_margin_"):
                margin_attr = {
                    "page_margin_top_cm": "top_margin", "page_margin_bottom_cm": "bottom_margin",
                    "page_margin_left_cm": "left_margin", "page_margin_right_cm": "right_margin",
                }.get(itype)
                if margin_attr and page_rules.get(itype.replace("page_", "").replace("_cm", "_cm")):
                    expected = issue["expected"]
                    setattr(sec, margin_attr, Cm(expected)); section = sec
        if section:
            fixed.append({"type": itype, "action": "fixed", "fix": issue.get("fix", "")})
    return fixed


def apply_template(doc, template_path, output=None, backup=False):
    """将学校模板的样式和页面设置应用到现有论文文档。

    通过 zipfile 替换目标文档中的 styles.xml，然后运行 assign_styles 重新分配。
    保留原文档的内容和段落结构不变。
    """
    import zipfile, tempfile, shutil, os
    from lxml import etree as _etree
    from lib.core import ThesisDoc

    output_path = get_output_path(doc, output=output, backup=backup)
    template_path = os.path.abspath(template_path)

    if not os.path.exists(template_path):
        return {"error": f"模板文件不存在: {template_path}"}

    # 1. 读取模板的 styles.xml 和 settings.xml
    try:
        with zipfile.ZipFile(template_path, 'r') as zt:
            tmpl_styles = zt.read('word/styles.xml') if 'word/styles.xml' in zt.namelist() else None
            tmpl_settings = zt.read('word/settings.xml') if 'word/settings.xml' in zt.namelist() else None
            tmpl_fonts = {}
            for name in zt.namelist():
                if name.startswith('word/fontTable') or name.startswith('word/stylesWithEffects'):
                    tmpl_fonts[name] = zt.read(name)
    except Exception as e:
        return {"error": f"读取模板失败: {e}"}

    if tmpl_styles is None:
        return {"error": "模板中未找到 styles.xml"}

    # 2. 复制模板样式到目标文档
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.docx', dir=os.path.dirname(output_path))
    os.close(tmp_fd)
    try:
        with zipfile.ZipFile(doc.filepath, 'r') as zin:
            with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.namelist():
                    if item == 'word/styles.xml':
                        zout.writestr(item, tmpl_styles)
                    elif item in tmpl_fonts:
                        zout.writestr(item, tmpl_fonts[item])
                    elif item == 'word/settings.xml' and tmpl_settings:
                        # 保留原文档的 settings 但可以合并
                        zout.writestr(item, tmpl_settings)
                    else:
                        zout.writestr(item, zin.read(item))
        os.replace(tmp_path, output_path)
    except Exception:
        if os.path.exists(tmp_path): os.unlink(tmp_path)
        raise

    # 3. 重新打开并分配样式
    new_doc = ThesisDoc(output_path)
    assignments = _assign_styles_impl(new_doc, preserve_style_defs=True)
    total_assigned = len(assignments)
    new_doc.save_zip(output_path)

    return {
        "template": os.path.basename(template_path),
        "output": output_path,
        "styles_replaced": True,
        "total_assigned": total_assigned,
        "message": f"已应用模板样式，重新分配了 {total_assigned} 个段落的样式",
    }
