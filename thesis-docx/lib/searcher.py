"""搜索模块 — 纯库函数"""
import re


WRITING_STYLE_RULES = [
    {"id": "connector_pile", "name": "连接词堆砌", "desc": "同时出现多个列举式连接词",
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


def search(doc, query=None, query_file=None, regex=False, writing_style=False,
           chapter=None, section=None, context=0, limit=20):
    """搜索关键词/正则/写作风格。writing_style=True 时忽略 query/regex。"""
    if writing_style:
        return _search_writing_style(doc, chapter=chapter, section=section, limit=limit)

    if query_file:
        with open(query_file, 'r', encoding='utf-8') as f:
            query = f.read().strip()
    if not query:
        return {"error": "请提供 --query 或 --from-file"}

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


def _search_writing_style(doc, chapter=None, section=None, limit=20):
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
        text = p.get("text", "").strip()
        if not text or len(text) < 10:
            continue
        style = p.get("style", "")
        if style.startswith("toc") or style.startswith("TOC") or style.startswith("Heading"):
            continue
        for rule in WRITING_STYLE_RULES:
            for pattern in rule.get("patterns", []):
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    results.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "desc": rule["desc"],
                        "severity": rule["severity"],
                        "para_index": p["index"],
                        "matched": match.group()[:80],
                        "text": text[:200],
                        "chapter": p.get("chapter_path", ""),
                    })
                    if len(results) >= limit:
                        return {"total": len(results), "results": results}
                    break

    # Abstract length check
    from lib.checker import find_abstract_paragraphs
    abstract_paras = find_abstract_paragraphs(doc)
    if abstract_paras and len(results) < limit:
        abstract_text = "".join(p.get("text", "") for p in abstract_paras)
        char_count = len(abstract_text)
        if char_count > 400:
            results.append({
                "rule_id": "abstract_length",
                "rule_name": "摘要过长",
                "desc": f"摘要当前{char_count}字，建议控制在100-200字",
                "severity": "warning",
                "para_index": abstract_paras[0]["index"],
                "matched": f"{char_count}字",
                "text": abstract_text[:200],
                "chapter": abstract_paras[0].get("chapter_path", ""),
            })

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
