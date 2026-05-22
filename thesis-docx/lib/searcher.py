"""搜索模块 — 纯库函数"""
import re


def search(doc, query=None, query_file=None, regex=False, chapter=None, section=None, context=0, limit=20):
    """搜索关键词/正则，返回匹配段落列表。"""
    if query_file:
        with open(query_file, 'r', encoding='utf-8') as f:
            query = f.read().strip()
    if not query:
        return {"error": "请提供 --query 或 --query-file"}

    results = []
    if section:
        sec = doc.find_section(title=section)
        if not sec:
            return {"error": f"未找到章节: {section}"}
        para_range = sec["para_range"]
    else:
        para_range = None

    for p in doc.paragraphs:
        if chapter is not None:
            path = p.get("chapter_path", "")
            if not path or not path.startswith(str(chapter)):
                continue
        if para_range and (p["index"] < para_range[0] or p["index"] > para_range[1]):
            continue
        text = p["text"]
        if not text:
            continue
        try:
            if regex:
                found = bool(re.search(query, text))
            else:
                found = query in text
        except re.error:
            found = query in text
        if found:
            entry = {
                "para_index": p["index"],
                "text": text[:200],
                "style": p["style"],
                "level": p["level"],
                "chapter": p.get("chapter_path", ""),
            }
            if context > 0:
                start = max(0, p["index"] - context)
                end = min(len(doc.paragraphs), p["index"] + context + 1)
                entry["context"] = [
                    {"index": cp["index"], "text": cp["text"][:200]}
                    for cp in doc.paragraphs[start:end]
                ]
            results.append(entry)
            if len(results) >= limit:
                break

    return {"total": len(results), "results": results}


def search_by_style(doc, style):
    """按样式名搜索段落"""
    results = []
    for p in doc.paragraphs:
        if p["style"] == style or (style == "heading" and p["level"] is not None):
            results.append({
                "para_index": p["index"],
                "text": p["text"][:200],
                "style": p["style"],
                "level": p["level"],
            })
    return {"total": len(results), "results": results}


def search_format(doc, target='all'):
    """格式一致性检查 — 找出同一样式中格式不统一的段落"""
    from lib.styles import classify_paragraph
    issues = []
    if target in ('all', 'headings'):
        for p in doc.paragraphs:
            if p["level"] is None:
                continue
            runs = p.get("runs", [])
            if not runs:
                continue
            base = runs[0]
            for r in runs[1:]:
                if r.get("font_size") != base.get("font_size"):
                    issues.append({
                        "para_index": p["index"],
                        "type": "heading_font_inconsistent",
                        "text": p["text"][:50],
                        "detail": f"段落内字号不一致: {base.get('font_size')}pt vs {r.get('font_size')}pt",
                    })
                    break
    if target in ('all', 'body'):
        for p in doc.paragraphs:
            role = classify_paragraph(p["text"].strip())
            if role is not None:
                continue
            if p["style"] not in ("Normal", "Body Text"):
                continue
            runs = p.get("runs", [])
            if not runs:
                continue
            base = runs[0]
            for r in runs[1:]:
                if r.get("font_size") and base.get("font_size") and abs((r.get("font_size") or 0) - (base.get("font_size") or 0)) > 1:
                    issues.append({
                        "para_index": p["index"],
                        "type": "body_font_inconsistent",
                        "text": p["text"][:50],
                        "detail": f"段落内字号不一致: {base.get('font_size')}pt vs {r.get('font_size')}pt",
                    })
                    break
    return {"total_issues": len(issues), "issues": issues[:50]}
