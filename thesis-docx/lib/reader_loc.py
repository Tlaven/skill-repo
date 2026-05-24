"""段落定位 — 查询段落索引所在的章节路径和附近元素"""
import re
from lxml import etree as _etree


def read_location(doc, paragraph):
    """查询段落索引所在的章节路径。"""
    if paragraph < 0 or paragraph >= len(doc.paragraphs):
        return {"error": f"段落索引 {paragraph} 超出范围 (0-{len(doc.paragraphs)-1})"}

    p = doc.get_para(paragraph)
    if p is None:
        return {"error": f"段落 {paragraph} 不存在"}

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

    nearby = {"images": [], "tables": [], "formulas": []}
    for img in doc.images:
        if abs(img["para_index"] - paragraph) <= 5:
            nearby["images"].append({"para_index": img["para_index"], "caption": img.get("nearby_caption", "")})
    for tbl in doc.tables:
        if abs(tbl["para_index_approx"] - paragraph) <= 5:
            nearby["tables"].append({"index": tbl["index"], "shape": f"{tbl['rows']}x{tbl['cols']}", "header": tbl["header"][:3]})
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
