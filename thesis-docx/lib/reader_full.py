"""全文地图 — read-full 命令，产出结构地图 + 可选展开"""
import re
from lxml import etree as _etree


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

    def _find_annotation_section(para_idx):
        if para_idx in para_to_section:
            info = para_to_section[para_idx]
            for child in _iter_children(info.get("children", [])):
                cs, ce = child["para_range"]
                if cs <= para_idx <= ce:
                    return child["title"]
            return info["title"]
        best = None
        for p in doc.paragraphs:
            if p["level"] is not None and p["index"] <= para_idx:
                best = p["text"]
        return best or "（无标题区域）"

    def _iter_children(nodes):
        for node in nodes:
            yield node
            yield from _iter_children(node.get("children", []))

    images = doc.images
    tables = doc.tables
    formula_placeholder = re.compile(r'FORMULA_\d+_\d+')
    formula_paras = []
    for p in doc.paragraphs:
        if formula_placeholder.search(p["text"]):
            formula_paras.append(p["index"])
        elem = doc.raw_paragraphs[p["index"]]._element
        xml_str = str(_etree.tostring(elem, encoding='unicode'))
        if 'm:oMath' in xml_str or 'm:oMathPara' in xml_str:
            formula_paras.append(p["index"])

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

    expand_section = None
    expand_range = None
    if section:
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

    lines = []
    total_chars = sum(p["char_count"] for p in doc.paragraphs)

    lines.append(f"论文全文地图 | 总字数:{total_chars} 段落:{len(doc.paragraphs)} "
                 f"图片:{len(images)} 表格:{len(tables)} 公式:{len(annotations['formulas'])}")

    preface_titles = {"封面", "声明", "原创性声明", "授权声明"}
    skip_titles = preface_titles | {"目  录", "目录"}
    abstract_zh_idx = None
    abstract_en_idx = None
    ref_section_start = None

    for p in doc.paragraphs:
        text = p["text"].strip()
        if text in ("摘  要", "摘要") and p["level"] == 1:
            abstract_zh_idx = p["index"]
        if text == "ABSTRACT" and p["level"] == 1:
            abstract_en_idx = p["index"]
        if "参考文献" in text and p["level"] == 1:
            ref_section_start = p["index"]

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

    def _build_section_output(nodes, depth=0):
        for node in nodes:
            title = node["title"]
            cc = node["char_count"]
            start, end = node["para_range"]
            indent = "  " * depth

            heading_para = doc.get_para(node["para_index"])
            zone = _section_zone(heading_para) if heading_para else None

            skip_content = zone in ("preface", "toc")

            node_ann = {"images": [], "tables": [], "formulas": []}
            for cat in annotations:
                for a in annotations[cat]:
                    sec_title = a.get("section", "")
                    in_range = (start <= a["para_index"] <= end) if "para_index" in a else False
                    if sec_title == title or in_range:
                        node_ann[cat].append(a)

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

            children = node.get("children", [])
            if children:
                _build_section_output(children, depth + 1)

            is_expanded = (expand_range and expand_section and
                           (title == expand_section or expand_section in title))
            if is_expanded:
                for pi in range(start, end + 1):
                    p = doc.get_para(pi)
                    if p is None or p["level"] is not None:
                        continue
                    if p["index"] in [c.get("para_index") for c in children]:
                        continue
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

    preface_found = False
    for p in doc.paragraphs:
        text = p["text"].strip()
        if text in preface_titles and p["level"] is not None:
            preface_found = True
            break
    if not preface_found:
        for p in doc.paragraphs[:15]:
            text = p["text"].strip()
            if text in preface_titles:
                lines.append(f"▎ {text} — PREFACE（跳过详细内容）")

    if doc.sections_tree:
        _build_section_output(doc.sections_tree)

    ref_result = list_references(doc)
    if "error" not in ref_result and ref_result.get("references"):
        lines.append("")
        lines.append(f"── 参考文献（{ref_result['total']}条）")
        for r in ref_result["references"][:30]:
            short = r["text"][:120]
            if len(r["text"]) > 120:
                short += "…"
            lines.append(f"  {short}")

    result_text = "\n".join(lines)

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
