# -*- coding: utf-8 -*-
"""检测修订、彩色文字、高亮等异常标记。"""
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'
NSMAP = {'w': W_NS}

DEFAULT_COLOR = "000000"


def detect_revisions(doc):
    """扫描文档并返回修订、彩色文字、高亮等信息。"""
    results = {
        "colored_text": [],
        "highlighted_text": [],
        "revisions": [],
        "total_paragraphs": len(doc.paragraphs),
    }

    # 1. Check run colors from parsed dicts
    for p in doc.paragraphs:
        p_idx = p["index"]
        for r in p.get("runs", []):
            color = r.get("color")
            if color and color.upper() != DEFAULT_COLOR:
                results["colored_text"].append({
                    "para_index": p_idx,
                    "style": p.get("style"),
                    "color": color,
                    "text": p.get("text", "")[:120]
                })
                break  # one note per para is enough

    # 2. Check tracked changes and highlights from XML
    for para_idx, para in enumerate(doc.raw_paragraphs):
        try:
            p_elem = para._element
        except Exception:
            continue

        # w:ins (insertions)
        ins_nodes = p_elem.findall(w('ins'), NSMAP)
        for ins in ins_nodes:
            texts = []
            for t in ins.findall('.//' + w('t'), NSMAP):
                if t.text:
                    texts.append(t.text)
            if texts:
                author = ins.get(f'{{{W_NS}}}author', '')
                date = ins.get(f'{{{W_NS}}}date', '')
                results["revisions"].append({
                    "para_index": para_idx,
                    "type": "insertion",
                    "author": author,
                    "date": date,
                    "text": ''.join(texts)[:200]
                })

        # w:del (deletions)
        del_nodes = p_elem.findall(w('del'), NSMAP)
        for d in del_nodes:
            texts = []
            for t in d.findall('.//' + w('delText'), NSMAP):
                if t.text:
                    texts.append(t.text)
            if texts:
                author = d.get(f'{{{W_NS}}}author', '')
                date = d.get(f'{{{W_NS}}}date', '')
                results["revisions"].append({
                    "para_index": para_idx,
                    "type": "deletion",
                    "author": author,
                    "date": date,
                    "text": ''.join(texts)[:200]
                })

        # w:rPr/w:highlight
        highlights = p_elem.findall('.//' + w('highlight'), NSMAP)
        for hl in highlights:
            val = hl.get(f'{{{W_NS}}}val', '')
            if val and val != 'none':
                parent_run = hl.getparent().getparent() if hl.getparent() is not None else None
                texts = []
                if parent_run is not None:
                    for t in parent_run.findall('.//' + w('t'), NSMAP):
                        if t.text:
                            texts.append(t.text)
                if texts:
                    results["highlighted_text"].append({
                        "para_index": para_idx,
                        "highlight": val,
                        "text": ''.join(texts)[:120]
                    })

    # Summary
    total_revisions = len(results["revisions"])
    insertions = sum(1 for r in results["revisions"] if r["type"] == "insertion")
    deletions = sum(1 for r in results["revisions"] if r["type"] == "deletion")

    from collections import Counter
    para_counts = Counter(r["para_index"] for r in results["revisions"])

    results["summary"] = {
        "colored_text_paras": len(results["colored_text"]),
        "highlighted_runs": len(results["highlighted_text"]),
        "total_revisions": total_revisions,
        "insertions": insertions,
        "deletions": deletions,
        "paragraphs_with_revisions": len(para_counts),
        "revised_para_indices": sorted(para_counts.keys()),
        "has_issues": total_revisions > 0 or len(results["colored_text"]) > 0 or len(results["highlighted_text"]) > 0
    }
    return results



