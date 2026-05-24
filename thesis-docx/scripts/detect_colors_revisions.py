# -*- coding: utf-8 -*-
"""检测 .docx 中带颜色的文本、修订标记（tracked changes）、高亮。
用法: python detect_colors_revisions.py <filepath> [-o output.json]
"""
import sys, os, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.core import ThesisDoc

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NSMAP = {'w': W_NS}

def detect(filepath):
    doc = ThesisDoc(filepath)
    results = {
        "file": os.path.basename(filepath),
        "colored_text": [],
        "highlighted_text": [],
        "revisions": [],
        "total_paragraphs": len(doc.paragraphs),
    }

    default_color = "000000"

    # 1. Check run colors from parsed dicts
    for p in doc.paragraphs:
        p_idx = p["index"]
        for r in p.get("runs", []):
            color = r.get("color")
            if color and color.upper() != default_color:
                results["colored_text"].append({
                    "para_index": p_idx,
                    "style": p.get("style"),
                    "color": color,
                    "text": p.get("text", "")[:120]
                })
                break

    # 2. Check tracked changes from raw paragraphs (XML)
    for para in doc.raw_paragraphs:
        try:
            p_elem = para._element
        except Exception:
            continue

        # w:ins (insertions)
        ins_nodes = p_elem.findall('.//w:ins', NSMAP)
        for ins in ins_nodes:
            texts = []
            for t in ins.findall('.//w:t', NSMAP):
                if t.text:
                    texts.append(t.text)
            if texts:
                author = ins.get('{%s}author' % W_NS, '')
                date = ins.get('{%s}date' % W_NS, '')
                results["revisions"].append({
                    "para_index": para._element.getparent().index(para._element) if hasattr(para._element, 'getparent') and para._element.getparent() is not None else 0,
                    "type": "insertion",
                    "author": author,
                    "date": date,
                    "text": ''.join(texts)[:200]
                })

        # w:del (deletions)
        del_nodes = p_elem.findall('.//w:del', NSMAP)
        for d in del_nodes:
            texts = []
            for t in d.findall('.//w:delText', NSMAP):
                if t.text:
                    texts.append(t.text)
            if texts:
                author = d.get('{%s}author' % W_NS, '')
                date = d.get('{%s}date' % W_NS, '')
                results["revisions"].append({
                    "para_index": para._element.getparent().index(para._element) if hasattr(para._element, 'getparent') and para._element.getparent() is not None else 0,
                    "type": "deletion",
                    "author": author,
                    "date": date,
                    "text": ''.join(texts)[:200]
                })

    # Summary
    total_revisions = len(results["revisions"])
    insertions = sum(1 for r in results["revisions"] if r["type"] == "insertion")
    deletions = sum(1 for r in results["revisions"] if r["type"] == "deletion")

    # Group by paragraph
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

if __name__ == '__main__':
    filepath = sys.argv[1]
    result = detect(filepath)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if len(sys.argv) > 2 and sys.argv[2] == '-o' and len(sys.argv) > 3:
        with open(sys.argv[3], 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Output written to {sys.argv[3]}")
    else:
        print(output)
