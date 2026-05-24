"""媒体（图片/公式/批注）读取 — 纯库函数"""
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from lxml import etree as _etree
from lib.reader_loc import read_location

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
DW_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'


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
        pi = img["para_index"]
        p_elem = doc.raw_paragraphs[pi]._element
        inline_elems = p_elem.findall(f'.//{{{DW_NS}}}inline')
        anchor_elems = p_elem.findall(f'.//{{{DW_NS}}}anchor')
        img["layout"] = "inline" if inline_elems else ("floating" if anchor_elems else "unknown")
        loc = read_location(doc, pi)
        if "error" not in loc:
            img["section_path"] = loc.get("section_path", "")
        context = {}
        for offset in [-1, 1]:
            idx = pi + offset
            if 0 <= idx < len(doc.paragraphs):
                cp = doc.get_para(idx)
                if cp and cp["text"].strip():
                    context["before" if offset == -1 else "after"] = cp["text"][:150]
        if context:
            img["context"] = context
        p_here = doc.get_para(pi)
        if p_here and "IMAGE_" in p_here["text"]:
            img["note"] = "图片占位符（IMAGE_X_X 文本，未嵌入实际图片）"
    return img


def read_images(doc):
    return {"total": len(doc.images), "images": doc.images}


def read_formulas(doc, summary=False):
    """列出文档中所有公式。

    summary=True 时输出精简格式（类型/位置/数学概要/所在章节）。
    """
    formula_placeholder = re.compile(r'FORMULA_\d+_\d+')
    results = []

    for p_info in doc.paragraphs:
        pi = p_info["index"]
        text = p_info["text"]
        ftype = None
        ole_obj = False

        if formula_placeholder.search(text):
            ftype = "placeholder"
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

        loc = read_location(doc, pi)
        section_path = loc.get("section_path", "") if "error" not in loc else ""

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

    seen = set()
    unique = []
    for r in results:
        key = (r["para_index"], r["type"] if not summary else r["para_index"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return {"total": len(unique), "formulas": unique}


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
