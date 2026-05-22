"""导出模块 — 纯库函数"""
import os
import json
from lib.core import ThesisDoc


def export_markdown(doc, output=None):
    output_path = output or doc.filepath.replace('.docx', '.md')
    lines = []
    for p in doc.paragraphs:
        text = p["text"]
        if not text.strip():
            lines.append(""); continue
        level = p["level"]
        if level is not None:
            lines.append("#" * (level + 1) + " " + text)
        elif p["style"] == "Caption":
            lines.append(f"*{text}*")
        elif p["has_image"]:
            lines.append(f"![图片]({p['image_ids'][0]})")
        else:
            lines.append(text)
    md_content = "\n".join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    return {"output": output_path, "lines": len(lines), "size_bytes": len(md_content.encode('utf-8'))}


def export_section(doc, title, output=None):
    output_path = output or doc.filepath.replace('.docx', f'_section_{title or "export"}.md')
    section = doc.find_section(title=title)
    if not section:
        return {"error": f"未找到章节: {title}"}
    paras = doc.get_section_paras(section)
    lines = [f"{'#' * (section['level'] + 1)} {section['title']}", ""]
    for p in paras:
        text = p["text"]
        if not text.strip():
            lines.append(""); continue
        level = p["level"]
        if level is not None:
            lines.append("#" * (level + 1) + " " + text)
        elif p["style"] == "Caption":
            lines.append(f"*{text}*")
        elif p["has_image"]:
            lines.append(f"![图片]({p['image_ids'][0] if p['image_ids'] else ''})")
        else:
            lines.append(text)
    md_content = "\n".join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    return {"section": section["title"], "output": output_path, "lines": len(lines)}


def export_images(doc, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    extracted = []
    for img in doc.images:
        r_id = img["r_id"]
        for rel in doc.doc.part.rels.values():
            if rel.rId == r_id:
                try:
                    target = rel.target_part
                    filename = os.path.basename(img["filename"])
                    filepath = os.path.join(output_dir, filename)
                    counter = 1
                    base, ext = os.path.splitext(filename)
                    while os.path.exists(filepath):
                        filepath = os.path.join(output_dir, f"{base}_{counter}{ext}"); counter += 1
                    with open(filepath, 'wb') as f:
                        f.write(target.blob)
                    extracted.append({"r_id": r_id, "filename": os.path.basename(filepath),
                                      "size_bytes": len(target.blob), "para_index": img["para_index"]})
                except Exception as e:
                    extracted.append({"r_id": r_id, "error": str(e)})
                break
    return {"output_dir": output_dir, "total": len(extracted), "extracted": extracted}


def export_diff(doc, file_new, output=None):
    old_file = doc.filepath
    output_path = output or old_file.replace('.docx', '_diff.json')
    if not os.path.exists(file_new):
        return {"error": f"文件不存在: {file_new}"}
    doc_old = doc
    doc_new = ThesisDoc(file_new)
    old_paras = {p["index"]: p["text"] for p in doc_old.paragraphs}
    new_paras = {p["index"]: p["text"] for p in doc_new.paragraphs}
    max_idx = max(max(old_paras.keys(), default=0), max(new_paras.keys(), default=0))
    diffs = []
    for i in range(max_idx + 1):
        old_text = old_paras.get(i, ""); new_text = new_paras.get(i, "")
        if old_text == new_text: continue
        if old_text and not new_text:
            diffs.append({"index": i, "type": "deleted", "old_text": old_text[:200]})
        elif not old_text and new_text:
            diffs.append({"index": i, "type": "added", "new_text": new_text[:200]})
        else:
            diffs.append({"index": i, "type": "modified", "old_text": old_text[:200], "new_text": new_text[:200]})
    result = {"old_file": old_file, "new_file": file_new, "total_diffs": len(diffs), "diffs": diffs[:100]}
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    return result
