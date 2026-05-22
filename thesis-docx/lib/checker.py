"""检查模块 — 纯库函数，无 argparse 依赖"""
import os
import re
from lib.utils import emu_to_cm, get_heading_level, find_toc_range
from lib.styles import get_default_rules, load_rules_with_defaults, classify_paragraph, CLASSIFY_PATTERNS
from lib.rules import load_rules

DEFAULT_RULES = get_default_rules()


def check_format(doc, rules=None):
    """综合格式检查"""
    _rules = load_rules(rules) if rules else DEFAULT_RULES
    issues = []
    total_checked = 0

    page_issues, page_count = _check_page_setup_rules(doc, _rules)
    issues.extend(page_issues); total_checked += page_count

    heading_issues, heading_count = _check_heading_rules(doc, _rules)
    issues.extend(heading_issues); total_checked += heading_count

    body_issues, body_count = _check_body_rules(doc, _rules)
    issues.extend(body_issues); total_checked += body_count

    caption_issues, caption_count = _check_caption_rules(doc, _rules)
    issues.extend(caption_issues); total_checked += caption_count

    errors = sum(1 for i in issues if i["severity"] == "error")
    warnings = sum(1 for i in issues if i["severity"] == "warning")

    return {
        "total_issues": len(issues), "issues": issues[:50],
        "summary": {"errors": errors, "warnings": warnings, "passed": max(0, total_checked - len(issues))},
    }


def check_headings(doc, rules=None):
    _rules = load_rules(rules) if rules else DEFAULT_RULES
    issues, count = _check_heading_rules(doc, _rules)
    return {"total_issues": len(issues), "issues": issues, "checked": count}


def check_body(doc, rules=None):
    _rules = load_rules(rules) if rules else DEFAULT_RULES
    issues, count = _check_body_rules(doc, _rules)
    return {"total_issues": len(issues), "issues": issues, "checked": count}


def check_captions(doc, rules=None):
    _rules = load_rules(rules) if rules else DEFAULT_RULES
    issues, count = _check_caption_rules(doc, _rules)
    return {"total_issues": len(issues), "issues": issues, "checked": count}


def check_page_setup(doc, rules=None):
    _rules = load_rules(rules) if rules else DEFAULT_RULES
    issues, count = _check_page_setup_rules(doc, _rules)
    return {"total_issues": len(issues), "issues": issues, "checked": count}


def _check_page_setup_rules(doc, rules):
    issues = []
    count = 0
    page_rules = rules.get("page", {})
    for section in doc.doc.sections:
        count += 1
        width = emu_to_cm(section.page_width)
        height = emu_to_cm(section.page_height)
        if page_rules.get("width_cm") and abs(width - page_rules["width_cm"]) > 0.1:
            issues.append({"type": "page_width", "severity": "error",
                           "expected": page_rules["width_cm"], "actual": width,
                           "fix": f"将页面宽度从 {width}cm 改为 {page_rules['width_cm']}cm"})
        if page_rules.get("height_cm") and abs(height - page_rules["height_cm"]) > 0.1:
            issues.append({"type": "page_height", "severity": "error",
                           "expected": page_rules["height_cm"], "actual": height,
                           "fix": f"将页面高度从 {height}cm 改为 {page_rules['height_cm']}cm"})
        for margin_name, attr in [
            ("margin_top_cm", "top_margin"), ("margin_bottom_cm", "bottom_margin"),
            ("margin_left_cm", "left_margin"), ("margin_right_cm", "right_margin"),
        ]:
            expected = page_rules.get(margin_name)
            if expected:
                actual = emu_to_cm(getattr(section, attr))
                if actual and abs(actual - expected) > 0.1:
                    issues.append({"type": f"page_{margin_name}", "severity": "warning",
                                   "expected": expected, "actual": actual,
                                   "fix": f"将 {margin_name} 从 {actual}cm 改为 {expected}cm"})
    return issues, count


def _detect_heading_level(text):
    text = text.strip()
    if not text: return None
    role = classify_paragraph(text)
    if role == "chapter_title": return 1
    if role == "section_title": return 2
    if role == "subsection_title": return 3
    if role in ("abstract_zh_title", "abstract_en_title", "toc_title",
                "reference_title", "appendix_title", "acknowledgement_title", "conclusion_title"):
        return 1
    return None


def _check_heading_rules(doc, rules):
    issues = []
    count = 0
    heading_rules = rules.get("headings", {})
    skip = _compute_skip_indices(doc)
    toc_start, toc_end = find_toc_range(doc)
    for p in doc.paragraphs:
        text = p["text"].strip()
        if not text: continue
        idx = p["index"]
        if idx in skip: continue
        if toc_start is not None and toc_end is not None:
            if toc_start < idx < toc_end: continue
        level = None
        if p["level"] is not None:
            level = p["level"]
        else:
            level = _detect_heading_level(text)
            if level is None: continue
            issues.append({"type": "heading_missing_style", "severity": "warning",
                           "para_index": idx, "text": (text[:30] + "...") if len(text) > 30 else text,
                           "expected": f"Heading {level}", "actual": p["style"],
                           "fix": f"将样式从 {p['style']} 改为 Heading {level}"})
        count += 1
        rule_key = f"h{level}"
        rule = heading_rules.get(rule_key)
        if not rule: continue
        text_preview = (text[:30] + "...") if len(text) > 30 else text
        for run_info in p["runs"]:
            if rule.get("font"):
                actual_font = run_info.get("font_name") or run_info.get("font_name_east")
                if actual_font and actual_font != rule["font"]:
                    issues.append({"type": "heading_font", "severity": "error", "para_index": idx,
                                   "text": text_preview, "expected": {"font": rule["font"]},
                                   "actual": {"font": actual_font},
                                   "fix": f"将字体从 {actual_font} 改为 {rule['font']}"}); break
            if rule.get("font_east"):
                actual_east = run_info.get("font_name_east")
                if actual_east and actual_east != rule["font_east"]:
                    issues.append({"type": "heading_font_east", "severity": "error", "para_index": idx,
                                   "text": text_preview, "expected": {"font_east": rule["font_east"]},
                                   "actual": {"font_east": actual_east},
                                   "fix": f"将东亚字体从 {actual_east} 改为 {rule['font_east']}"}); break
        if rule.get("size_pt"):
            for run_info in p["runs"]:
                actual_size = run_info.get("font_size")
                if actual_size and abs(actual_size - rule["size_pt"]) > 0.5:
                    issues.append({"type": "heading_size", "severity": "error", "para_index": idx,
                                   "text": text_preview, "expected": {"size": rule["size_pt"]},
                                   "actual": {"size": actual_size},
                                   "fix": f"将字号从 {actual_size}pt 改为 {rule['size_pt']}pt"}); break
        if rule.get("alignment"):
            actual_align = p.get("alignment")
            if actual_align and actual_align != rule["alignment"]:
                issues.append({"type": "heading_alignment", "severity": "warning", "para_index": idx,
                               "text": text_preview, "expected": rule["alignment"],
                               "actual": actual_align, "fix": f"将对齐从 {actual_align} 改为 {rule['alignment']}"})
    return issues, count


def _is_non_body_role(text):
    role = classify_paragraph(text.strip())
    return role is not None


def _check_body_rules(doc, rules):
    issues = []
    count = 0
    body_rules = rules.get("body", {})
    skip = _compute_skip_indices(doc)
    for p in doc.paragraphs:
        text = p["text"].strip()
        if not text: continue
        if p["index"] in skip: continue
        if p["style"] not in ("Normal", "Body Text"): continue
        if _is_non_body_role(text): continue
        count += 1
        text_preview = (text[:50] + "...") if len(text) > 50 else text
        if body_rules.get("size_pt"):
            for run_info in p["runs"]:
                actual_size = run_info.get("font_size")
                if actual_size and abs(actual_size - body_rules["size_pt"]) > 0.5:
                    issues.append({"type": "body_font_size", "severity": "warning", "para_index": p["index"],
                                   "text": text_preview, "expected": body_rules["size_pt"],
                                   "actual": actual_size, "fix": f"将字号从 {actual_size}pt 改为 {body_rules['size_pt']}pt"}); break
        if body_rules.get("line_spacing"):
            actual_spacing = p.get("line_spacing")
            if actual_spacing and isinstance(actual_spacing, (int, float)):
                if abs(actual_spacing - body_rules["line_spacing"]) > 0.1:
                    issues.append({"type": "body_line_spacing", "severity": "warning", "para_index": p["index"],
                                   "text": text_preview, "expected": body_rules["line_spacing"],
                                   "actual": actual_spacing, "fix": f"将行距从 {actual_spacing} 改为 {body_rules['line_spacing']}"})
        if body_rules.get("first_line_indent_cm"):
            actual_indent = p.get("first_line_indent")
            if actual_indent and isinstance(actual_indent, (int, float)):
                if abs(actual_indent - body_rules["first_line_indent_cm"]) > 0.1:
                    issues.append({"type": "body_first_line_indent", "severity": "warning", "para_index": p["index"],
                                   "text": text_preview, "expected": body_rules["first_line_indent_cm"],
                                   "actual": actual_indent, "fix": f"将首行缩进从 {actual_indent}cm 改为 {body_rules['first_line_indent_cm']}cm"})
    return issues, count


def _check_caption_rules(doc, rules):
    import re
    issues = []
    count = 0
    caption_rules = rules.get("caption", {})
    pattern = caption_rules.get("pattern", r"^图\s*\d+-\d+|^表\s*\d+-\d+")
    skip = _compute_skip_indices(doc)
    for p in doc.paragraphs:
        text = p["text"].strip()
        if not text: continue
        idx = p["index"]
        if idx in skip: continue
        is_caption_style = p["style"] == "Caption"
        is_caption_content = bool(re.match(pattern, text))
        if not is_caption_style and not is_caption_content: continue
        count += 1
        text_preview = (text[:50] + "...") if len(text) > 50 else text
        if is_caption_content and not is_caption_style:
            issues.append({"type": "caption_missing_style", "severity": "warning", "para_index": idx,
                           "text": text_preview, "expected": "Caption", "actual": p["style"],
                           "fix": f"将样式从 {p['style']} 改为 Caption"})
        if not re.match(pattern, text):
            issues.append({"type": "caption_format", "severity": "warning", "para_index": idx,
                           "text": text_preview, "fix": f"图表标题编号格式应符合 {pattern}"})
        if caption_rules.get("size_pt"):
            for run_info in p["runs"]:
                actual_size = run_info.get("font_size")
                if actual_size and abs(actual_size - caption_rules["size_pt"]) > 0.5:
                    issues.append({"type": "caption_size", "severity": "warning", "para_index": idx,
                                   "text": text_preview, "expected": caption_rules["size_pt"],
                                   "actual": actual_size, "fix": f"将字号从 {actual_size}pt 改为 {caption_rules['size_pt']}pt"}); break
        if caption_rules.get("alignment"):
            actual_align = p.get("alignment")
            if actual_align and actual_align != caption_rules["alignment"]:
                issues.append({"type": "caption_alignment", "severity": "warning", "para_index": idx,
                               "text": text_preview, "expected": caption_rules["alignment"],
                               "actual": actual_align, "fix": f"将对齐从 {actual_align} 改为 {caption_rules['alignment']}"})
    return issues, count


def check_style(doc):
    STYLE_RULES = [
        {"id": "connector_pile", "name": "连接词堆砌", "desc": "段落中同时出现多个列举式连接词",
         "severity": "warning",
         "patterns": [r"首先[，,].+其次[，,]", r"首先[，,].+然后[，,]", r"一方面[，,].+另一方面[，,]"]},
        {"id": "mechanical_listing", "name": "机械列举", "desc": "使用第X/第Y/第Z结构",
         "severity": "warning",
         "patterns": [r"第一[，,].+第二[，,].+第三[，,]", r"（一）.+（二）.+（三）"]},
        {"id": "preview_sentence", "name": "列举预告句", "desc": "先预告再说的冗余句式",
         "severity": "warning",
         "patterns": [r"主要(包括|完成|涵盖|分为|涉及)(了|以下|以下)?(几个|如下|下列|以下)",
                      r"从(以下|以下)几个方面", r"主要包括(如下|以下|几点|几个方面)"]},
        {"id": "cliche_opener", "name": "套路化开头", "desc": "空泛的万能开头",
         "severity": "warning",
         "patterns": [r"随着[^。？]*的(快速|不断|迅猛|蓬勃|飞速)发展",
                      r"在[^.]*领域(展现出|具有|发挥着)(巨大|重要|广泛|深远)(的)?(潜力|作用|价值|意义|前景)"]},
        {"id": "filler_conclusion", "name": "冗余总结", "desc": "万能总结句",
         "severity": "info",
         "patterns": [r"因此[，,]?(该|本|此|上述)[^。]*(具有|有)(重要|较大|一定)(的)?(理论意义|应用价值|参考价值|现实意义)",
                      r"(综上|总之|总而言之|由此可见)[，,]?[^。]*(具有|有)(重要|较大)(的)?(意义|价值|作用)"]},
    ]
    issues = []
    checked = 0
    for p in doc.paragraphs:
        text = p.get("text", "").strip()
        if not text or len(text) < 10: continue
        style = p.get("style", "")
        if style in ("toc 1", "toc 2", "toc 3", "Heading 1", "Heading 2", "Heading 3"): continue
        checked += 1
        text_preview = (text[:60] + "...") if len(text) > 60 else text
        for rule in STYLE_RULES:
            for pattern in rule.get("patterns", []):
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    issues.append({
                        "rule_id": rule["id"], "rule_name": rule["name"], "desc": rule["desc"],
                        "severity": rule["severity"], "para_index": p["index"],
                        "matched": match.group()[:80], "text_preview": text_preview,
                        "fix": _style_fix_hint(rule["id"]),
                    })
                    break
    abstract_paras = _find_abstract_paragraphs(doc)
    if abstract_paras:
        abstract_text = "".join(p.get("text", "") for p in abstract_paras)
        char_count = len(abstract_text)
        if char_count > 400:
            issues.append({
                "rule_id": "abstract_length", "rule_name": "摘要过长",
                "desc": f"摘要当前{char_count}字，建议控制在100-200字",
                "severity": "warning", "para_index": abstract_paras[0]["index"],
                "matched": f"{char_count}字", "fix": "精简摘要",
            })
    return {"total_issues": len(issues), "issues": issues, "checked": checked}


def _find_abstract_paragraphs(doc):
    in_abstract = False
    abstract_paras = []
    for p in doc.paragraphs:
        text = p.get("text", "").strip()
        if text == "摘   要" or text == "摘要":
            in_abstract = True; continue
        if in_abstract:
            if text.startswith("关键词") or text == "ABSTRACT": break
            if text: abstract_paras.append(p)
    return abstract_paras


def _style_fix_hint(rule_id):
    hints = {
        "connector_pile": "将列举式连接词替换为内容逻辑自然过渡",
        "mechanical_listing": "去掉'第一、第二'结构，改为内容本身组织段落",
        "preview_sentence": "删除预告句，直接写具体内容",
        "cliche_opener": "去掉空泛开头，直接切入具体问题",
        "filler_conclusion": "删除万能总结句，或替换为具体结论",
        "abstract_length": "精简摘要，删除重复信息和预告句",
    }
    return hints.get(rule_id, "优化写作风格")


def check_paragraphs(doc, threshold=200, start=None, end=None):
    long_paragraphs = []
    for p in doc.paragraphs:
        text = p.get("text", "").strip()
        if not text: continue
        style = p.get("style", "")
        if style in ("toc 1", "toc 2", "toc 3") or style.startswith("Heading"): continue
        idx = p["index"]
        if start is not None and idx < start: continue
        if end is not None and idx > end: continue
        char_count = len(text)
        if char_count <= threshold: continue
        sentence_ends = [i for i, ch in enumerate(text) if ch in ('。', '！', '？')]
        split_suggestions = []
        if sentence_ends:
            last_pos = 0
            for j, pos in enumerate(sentence_ends):
                segment_chars = pos + 1 - last_pos
                if segment_chars >= threshold * 0.5:
                    context = text[max(0, pos - 10):pos + 11]
                    split_suggestions.append({"after_char": pos + 1, "segment_chars": segment_chars, "context": f"...{context}..."})
                    last_pos = pos + 1
        long_paragraphs.append({
            "para_index": idx, "char_count": char_count,
            "text_preview": (text[:60] + "...") if len(text) > 60 else text,
            "style": style, "split_points": split_suggestions[:5],
        })
    long_paragraphs.sort(key=lambda x: x["char_count"], reverse=True)
    return {
        "threshold": threshold, "total_long": len(long_paragraphs),
        "long_paragraphs": long_paragraphs,
        "summary": {
            "over_300": sum(1 for p in long_paragraphs if p["char_count"] > 300),
            "over_500": sum(1 for p in long_paragraphs if p["char_count"] > 500),
            "max_chars": max((p["char_count"] for p in long_paragraphs), default=0),
        },
    }


def check_placeholders(doc):
    PLACEHOLDER_PATTERNS = [
        (r'\bTODO\b', "TODO 标记"), (r'\bFIXME\b', "FIXME 标记"),
        (r'占位', "占位符文本"), (r'待补充', "待补充标记"), (r'待填写', "待填写标记"),
        (r'待完善', "待完善标记"), (r'【[^】]*】', "中文方括号占位符"),
        (r'暂缺', "暂缺标记"), (r'XXX+', "X占位符"),
        (r'FORMULA_\d+_\d+', "公式占位符"), (r'IMAGE_\d+_\d+', "图片占位符"),
        (r'TABLE_\d+_\d+', "表格占位符"),
    ]
    placeholders = []
    for p in doc.paragraphs:
        text = p.get("text", "").strip()
        if not text: continue
        style = p.get("style", "")
        if style.startswith("Heading") or style.startswith("toc") or style.startswith("TOC"): continue
        for pattern, desc in PLACEHOLDER_PATTERNS:
            matches = list(re.finditer(pattern, text))
            if matches:
                placeholders.append({
                    "type": "placeholder", "severity": "warning",
                    "para_index": p["index"], "placeholder_type": desc,
                    "matched": [m.group() for m in matches],
                    "text_preview": (text[:80] + "...") if len(text) > 80 else text,
                    "fix": f"替换或删除占位符内容: {desc}",
                })
    return {"total": len(placeholders), "placeholders": placeholders}


def _compute_skip_indices(doc):
    skip = set()
    body_start = 0
    for p in doc.paragraphs:
        text = p.get("text", "").strip()
        if not text: continue
        role = classify_paragraph(text)
        if role in ("abstract_zh_title", "toc_title", "chapter_title"):
            body_start = p["index"]; break
        if p.get("level") == 1 and text:
            body_start = p["index"]; break
    for p in doc.paragraphs:
        if p["index"] < body_start: skip.add(p["index"])
    decl_start = None; decl_end = None
    for p in doc.paragraphs:
        text = p.get("text", "").strip()
        if "声明" in text and (p.get("level") is not None or "声明" in text[:4]):
            decl_start = p["index"]; continue
        if decl_start is not None and decl_end is None:
            if p.get("level") is not None or classify_paragraph(text) is not None:
                decl_end = p["index"]; break
    if decl_start is not None:
        end = decl_end if decl_end is not None else len(doc.paragraphs)
        for idx in range(decl_start, end): skip.add(idx)
    return skip


def check_figure_references(doc):
    figure_refs = {}
    caption_pattern = re.compile(r'^图\s*(\d+[-‐–—.]\d+)')
    for img in doc.images:
        caption = img.get("nearby_caption", "")
        m = caption_pattern.match(caption) if caption else None
        fig_num = m.group(1) if m else None
        figure_refs[img["para_index"]] = fig_num
    if not figure_refs:
        return {"total_issues": 0, "issues": [], "figures_checked": 0}
    issues = []
    ref_pattern = re.compile(r'图\s*\d+[-‐–—.]\d+')
    for img_para_idx, fig_num in figure_refs.items():
        has_before_ref = False; has_before_heading = False
        for offset in range(1, 6):
            idx = img_para_idx - offset
            if idx < 0: break
            p = doc.get_para(idx)
            if p is None: continue
            text = p["text"].strip()
            if not text: continue
            if p["level"] is not None:
                has_before_heading = True; break
            if fig_num:
                if re.search(r'图\s*' + re.escape(fig_num), text):
                    has_before_ref = True; break
            elif ref_pattern.search(text):
                has_before_ref = True; break
        if has_before_heading and not has_before_ref:
            issues.append({
                "type": "figure_no_text_before", "severity": "warning",
                "para_index": img_para_idx, "figure_number": fig_num,
                "message": f"图片（图{fig_num}）前缺少引用文字",
                "fix": f"在标题后、图片前添加引用文字，如'如图{fig_num}所示'",
            })
        after_start = img_para_idx + 1
        caption_idx = None
        for img_info in doc.images:
            if img_info["para_index"] == img_para_idx:
                caption_idx = img_info.get("caption_para_index"); break
        if caption_idx and caption_idx >= after_start:
            after_start = caption_idx + 1
        has_after_text = False; has_after_heading = False
        for offset in range(0, 4):
            idx = after_start + offset
            p = doc.get_para(idx)
            if p is None: continue
            text = p["text"].strip()
            if not text: continue
            if p["level"] is not None:
                has_after_heading = True; break
            has_after_text = True; break
        if has_after_heading and not has_after_text:
            issues.append({
                "type": "figure_no_text_after", "severity": "warning",
                "para_index": img_para_idx, "figure_number": fig_num,
                "message": f"图片（图{fig_num}）后缺少分析文字",
                "fix": "在图片标题后添加分析文字",
            })
    return {"total_issues": len(issues), "issues": issues, "figures_checked": len(figure_refs)}


def check_references(doc):
    from lib.reference import list_citations, list_references
    citations_result = list_citations(doc)
    all_cited_nums = set()
    for c in citations_result["citations"]:
        all_cited_nums.add(c["ref_num"])
    refs_result = list_references(doc)
    if "error" in refs_result:
        return refs_result
    ref_nums = set(r["number"] for r in refs_result["references"])
    unreferenced = sorted(ref_nums - all_cited_nums)
    undefined = sorted(all_cited_nums - ref_nums)
    issues = []
    if not all_cited_nums and ref_nums:
        issues.insert(0, {"type": "no_citations", "severity": "error",
                          "detail": f"正文无任何引用标记，但参考文献列表有 {len(ref_nums)} 条记录",
                          "fix": "检查正文中是否遗漏了引用标记 [N]"})
    order = citations_result["first_appearance_order"]
    prev = 0
    for num in order:
        if num < prev:
            for c in citations_result["citations"]:
                if c["ref_num"] == num:
                    issues.append({"type": "not_in_order",
                                   "detail": f"正文第{c['para_index']}段: [{num}]出现在[{prev}]之前",
                                   "fix": "运行 renumber-references 自动重编引用号",
                                   "auto_fix": "renumber-references"}); break
        prev = num
    for num in unreferenced:
        issues.append({"type": "missing_in_text",
                       "detail": f"参考文献[{num}]在正文中未被引用",
                       "fix": "在正文中添加引用或在参考文献中删除"})
    for num in undefined:
        issues.append({"type": "missing_in_list",
                       "detail": f"正文引用了[{num}]，但参考文献列表中不存在",
                       "fix": f"添加参考文献[{num}]"})
    return {"issues": issues,
            "stats": {"refs_in_text": sorted(all_cited_nums), "refs_in_list": sorted(ref_nums),
                      "unreferenced": unreferenced, "undefined": undefined}}


def check_formula_references(doc):
    """检查公式前后是否有文字引用。

    规则：
    - 公式前应有至少一个段落引用该公式（如"如式(3.1)所示"）
    - 公式后应有至少一个段落解释公式中的变量（如"其中，w1为..."）
    """
    import re
    from lxml import etree as _etree
    M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

    # 收集公式段落索引（OMML 和 FORMULA_ 占位符）
    formula_paras = []
    formula_placeholder = re.compile(r'FORMULA_\d+_\d+')
    for p in doc.paragraphs:
        text = p["text"]
        if formula_placeholder.search(text):
            formula_paras.append(p["index"])
        elem = doc.raw_paragraphs[p["index"]]._element
        xml_str = str(_etree.tostring(elem, encoding='unicode'))
        if 'm:oMath' in xml_str or 'm:oMathPara' in xml_str:
            formula_paras.append(p["index"])

    if not formula_paras:
        return {"total_issues": 0, "issues": [], "formulas_checked": 0}

    # 尝试提取公式编号（从段落文本中找 (X.Y)）
    num_pattern = re.compile(r'\((\d+[.\-]\d+)\)')
    ref_pattern = re.compile(r'式\s*\(?\d+[.\-]\d+\)?')
    explain_pattern = re.compile(r'其中[，,]')

    issues = []
    for fp in formula_paras:
        # 获取公式所在段落自身的文本（可能内联包含引用和解释）
        self_p = doc.get_para(fp)
        self_text = self_p["text"] if self_p else ""

        # 向前搜索（含自身段落）：公式前或同段内是否有引用文字
        has_before_ref = ref_pattern.search(self_text) if self_text else False
        if not has_before_ref:
            for offset in range(1, 5):
                idx = fp - offset
                if idx < 0: break
                p = doc.get_para(idx)
                if p is None: continue
                text = p["text"].strip()
                if not text: continue
                if p["level"] is not None: break
                if ref_pattern.search(text):
                    has_before_ref = True
                    break

        # 向后搜索（含自身段落）：公式后或同段内是否有变量解释
        has_after_explain = False
        if self_text and (explain_pattern.search(self_text) or "表示" in self_text):
            # 自身段落已包含解释文字
            has_after_explain = True
        if not has_after_explain:
            for offset in range(1, 4):
                idx = fp + offset
                p = doc.get_para(idx)
                if p is None: break
                text = p["text"].strip()
                if not text: continue
                if p["level"] is not None: break
                if explain_pattern.search(text) or "表示" in text[:50]:
                    has_after_explain = True
                    break

        if not has_before_ref:
            issues.append({
                "type": "formula_no_ref_before",
                "severity": "warning",
                "para_index": fp,
                "message": "公式前缺少引用文字（如'如式(X.Y)所示'）",
                "fix": "在公式前的段落末尾添加引用语，如'如式(3.1)所示'",
            })
        if not has_after_explain:
            issues.append({
                "type": "formula_no_explain_after",
                "severity": "info",
                "para_index": fp,
                "message": "公式后缺少变量解释（如'其中，w1为...'）",
                "fix": "在公式后的段落中解释各变量的含义",
            })

    return {"total_issues": len(issues), "issues": issues, "formulas_checked": len(formula_paras)}


def check_all(doc, rules=None, threshold=200):
    from argparse import Namespace
    results = {}
    total_issues = 0
    fmt_result = check_format(doc, rules)
    results["format"] = fmt_result
    total_issues += fmt_result.get("total_issues", 0)
    style_result = check_style(doc)
    results["style"] = style_result
    total_issues += style_result.get("total_issues", 0)
    para_result = check_paragraphs(doc, threshold=threshold)
    results["paragraphs"] = para_result
    total_issues += para_result.get("total_long", 0)
    ref_result = check_references(doc)
    results["references"] = ref_result
    total_issues += len(ref_result.get("issues", []))
    placeholder_result = check_placeholders(doc)
    results["placeholders"] = placeholder_result
    total_issues += placeholder_result.get("total", 0)
    figref_result = check_figure_references(doc)
    results["figure_references"] = figref_result
    total_issues += figref_result.get("total_issues", 0)
    fmref_result = check_formula_references(doc)
    results["formula_references"] = fmref_result
    total_issues += fmref_result.get("total_issues", 0)
    return {
        "total_issues": total_issues, "categories": list(results.keys()),
        "summary": {
            "format_issues": fmt_result.get("total_issues", 0),
            "style_issues": style_result.get("total_issues", 0),
            "long_paragraphs": para_result.get("total_long", 0),
            "reference_issues": len(ref_result.get("issues", [])),
            "placeholders": placeholder_result.get("total", 0),
            "figure_reference_issues": figref_result.get("total_issues", 0),
            "formula_reference_issues": fmref_result.get("total_issues", 0),
        }, "results": results,
    }
