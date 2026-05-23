"""检查辅助函数（内部使用，无 argparse 依赖）

公共 check-* 命令已移除：改为对应 read-*/list-* 的 --verify。

被其他模块引用的内部函数：
  _check_page_setup_rules  — fixer.py / reader.py 引用
  _check_heading_rules     — reader.py (--verify) 引用
  _check_body_rules        — reader.py (--verify) 引用

曾存在但已删除的（需 Agent 结合 search/上下文判断，不宜程序硬检查）：
  check_paragraphs   check_placeholders  check_all
  check_references   check_figure_references  check_formula_references
"""
import re
from lib.utils import emu_to_cm, get_heading_level, find_toc_range
from lib.styles import get_default_rules, load_rules_with_defaults, classify_paragraph
from lib.rules import load_rules

DEFAULT_RULES = get_default_rules()


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




