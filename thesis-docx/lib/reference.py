"""引用管理模块 — 纯库函数"""
import re
import copy
from lxml import etree
from lib.utils import NSMAP, get_output_path

CITATION_PATTERN = re.compile(r'\[(\d+(?:\s*[,，]\s*\d+)*)\]')
REF_NUM_PATTERN = re.compile(r'^\[(\d+)\]\s*')


def list_citations(doc):
    citations = []
    for p in doc.paragraphs:
        text = p["text"]
        if not text:
            continue
        for match in CITATION_PATTERN.finditer(text):
            nums_str = match.group(1)
            nums = [int(n.strip()) for n in re.split(r'[,，]', nums_str) if n.strip()]
            for num in nums:
                citations.append({
                    "ref_num": num, "para_index": p["index"],
                    "text": text[:200], "match": match.group(0),
                })
    first_appearance = {}
    for c in citations:
        num = c["ref_num"]
        if num not in first_appearance:
            first_appearance[num] = len(first_appearance) + 1
    order = sorted(first_appearance.keys(), key=lambda n: first_appearance[n])
    return {"citations": citations, "first_appearance_order": order}


def list_references(doc, verify=False):
    refs = _find_reference_section(doc)
    if not refs:
        return {"error": "未找到参考文献部分"}
    ref_list = []
    auto_number = 0
    for p in refs:
        text = p["text"].strip()
        if not text:
            continue
        m = REF_NUM_PATTERN.match(text)
        if m:
            ref_list.append({
                "number": int(m.group(1)), "text": text,
                "para_index": p["index"],
            })
        elif _looks_like_reference(text):
            auto_number += 1
            ref_list.append({
                "number": auto_number, "text": text,
                "para_index": p["index"],
                "note": "缺少编号前缀 [N]，已自动编号",
            })
    result = {"total": len(ref_list), "references": ref_list}
    if verify:
        result["verify"] = _verify_references(doc, ref_list)
    return result


def _verify_references(doc, ref_list):
    citations_result = list_citations(doc)
    all_cited_nums = set()
    for c in citations_result["citations"]:
        all_cited_nums.add(c["ref_num"])
    ref_nums = set(r["number"] for r in ref_list)
    unreferenced = sorted(ref_nums - all_cited_nums)
    undefined = sorted(all_cited_nums - ref_nums)
    issues = []
    if not all_cited_nums and ref_nums:
        issues.append({
            "type": "no_citations",
            "detail": f"正文无任何引用标记，但参考文献列表有 {len(ref_nums)} 条记录",
        })
    order = citations_result["first_appearance_order"]
    prev = 0
    for num in order:
        if num < prev:
            for c in citations_result["citations"]:
                if c["ref_num"] == num:
                    issues.append({
                        "type": "not_in_order",
                        "detail": f"正文第{c['para_index']}段: [{num}]出现在[{prev}]之前",
                    })
                    break
        prev = num
    for num in unreferenced:
        issues.append({"type": "missing_in_text", "detail": f"参考文献[{num}]在正文中未被引用"})
    for num in undefined:
        issues.append({"type": "missing_in_list", "detail": f"正文引用了[{num}]，但参考文献列表中不存在"})
    return issues


def check_references(doc):
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
        issues.insert(0, {
            "type": "no_citations", "severity": "error",
            "detail": f"正文无任何引用标记，但参考文献列表有 {len(ref_nums)} 条记录",
            "fix": "检查正文中是否遗漏了引用标记 [N]",
        })
    order = citations_result["first_appearance_order"]
    prev = 0
    for num in order:
        if num < prev:
            for c in citations_result["citations"]:
                if c["ref_num"] == num:
                    issues.append({
                        "type": "not_in_order",
                        "detail": f"正文第{c['para_index']}段: [{num}]出现在[{prev}]之前",
                        "fix": "运行 renumber-references 自动重编引用号",
                        "auto_fix": "renumber-references",
                    })
                    break
        prev = num
    for num in unreferenced:
        issues.append({
            "type": "missing_in_text",
            "detail": f"参考文献[{num}]在正文中未被引用",
            "fix": "在正文中添加引用或在参考文献中删除",
        })
    for num in undefined:
        issues.append({
            "type": "missing_in_list",
            "detail": f"正文引用了[{num}]，但参考文献列表中不存在",
            "fix": f"添加参考文献[{num}]",
        })
    return {
        "issues": issues,
        "stats": {
            "refs_in_text": sorted(all_cited_nums),
            "refs_in_list": sorted(ref_nums),
            "unreferenced": unreferenced,
            "undefined": undefined,
        },
    }


def renumber_references(doc, output):
    citations_result = list_citations(doc)
    order = citations_result["first_appearance_order"]
    old_to_new = {}
    for new_num, old_num in enumerate(order, 1):
        old_to_new[old_num] = new_num
    refs_result = list_references(doc)
    if "error" in refs_result:
        return refs_result
    ref_nums = [r["number"] for r in refs_result["references"]]
    next_num = len(old_to_new) + 1
    for num in ref_nums:
        if num not in old_to_new:
            old_to_new[num] = next_num
            next_num += 1
    for p_info in doc.paragraphs:
        if not p_info["text"]:
            continue
        para = doc.raw_paragraphs[p_info["index"]]
        _renumber_para_citations(para, old_to_new)
    _reorder_references(doc, old_to_new, refs_result["references"])
    doc.save(output)
    return {"mapping": old_to_new, "output": output}


def _renumber_para_citations(para, old_to_new):
    for run in para.runs:
        if not run.text:
            continue
        new_text = CITATION_PATTERN.sub(
            lambda m: _replace_citation_nums(m, old_to_new), run.text)
        if new_text != run.text:
            run.text = new_text


def _replace_citation_nums(match, old_to_new):
    nums_str = match.group(1)
    nums = [int(n.strip()) for n in re.split(r'[,，]', nums_str) if n.strip()]
    new_nums = [str(old_to_new.get(n, n)) for n in nums]
    return f"[{','.join(new_nums)}]"


def _reorder_references(doc, old_to_new, ref_list):
    ref_paras = _find_reference_section(doc)
    if not ref_paras:
        return
    sorted_refs = sorted(ref_list, key=lambda r: old_to_new.get(r["number"], 999))
    for ref in sorted_refs:
        para = doc.raw_paragraphs[ref["para_index"]]
        for run in para.runs:
            if run.text:
                old_label = f"[{ref['number']}]"
                new_label = f"[{old_to_new.get(ref['number'], ref['number'])}]"
                if run.text.startswith(old_label):
                    run.text = run.text.replace(old_label, new_label, 1)


def add_reference(doc, text, position=None, output=None, backup=False):
    output_path = get_output_path(doc, output=output, backup=backup)
    refs_result = list_references(doc)
    if "error" in refs_result:
        return refs_result
    if position is None:
        position = max(r["number"] for r in refs_result["references"]) + 1 if refs_result["references"] else 1
    ref_text = f"[{position}] {text}"
    last_ref = max(refs_result["references"], key=lambda r: r["para_index"]) if refs_result["references"] else None
    if last_ref:
        ref_para = doc.raw_paragraphs[last_ref["para_index"]]
        new_para = copy.deepcopy(ref_para._element)
        for r in new_para.findall(f'{{{NSMAP["w"]}}}r'):
            new_para.remove(r)
        new_run = etree.SubElement(new_para, f'{{{NSMAP["w"]}}}r')
        t = etree.SubElement(new_run, f'{{{NSMAP["w"]}}}t')
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t.text = ref_text
        ref_para._element.addnext(new_para)
    else:
        return {"error": "无法确定插入位置"}
    doc.save(output_path)
    return {"number": position, "text": ref_text, "output": output_path}


def remove_reference(doc, number, output=None, backup=False):
    output_path = get_output_path(doc, output=output, backup=backup)
    refs_result = list_references(doc)
    if "error" in refs_result:
        return refs_result
    target = None
    for r in refs_result["references"]:
        if r["number"] == number:
            target = r
            break
    if target is None:
        return {"error": f"未找到参考文献 [{number}]"}
    para = doc.raw_paragraphs[target["para_index"]]
    para._element.getparent().remove(para._element)
    doc.save(output_path)
    return {"removed": target, "output": output_path}


def _find_reference_section(doc):
    ref_section = doc.find_section(title="参考文献")
    if ref_section:
        return doc.get_section_paras(ref_section)
    for p in doc.paragraphs:
        if p["level"] == 1 and "参考文献" in p["text"]:
            section = doc.find_section(title="参考文献")
            if section:
                return doc.get_section_paras(section)
    ref_start = None
    ref_end = None
    for p in doc.paragraphs:
        text = p.get("text", "").strip()
        if ref_start is None:
            if "参考文献" in text and len(text) < 20:
                ref_start = p["index"]
                continue
        else:
            if p.get("level") is not None:
                ref_end = p["index"]
                break
            if text in ("致谢", "附录") or text.startswith("致谢") or text.startswith("附录"):
                ref_end = p["index"]
                break
    if ref_start is not None:
        end = ref_end if ref_end is not None else len(doc.paragraphs)
        return [p for p in doc.paragraphs if ref_start < p["index"] < end]
    refs = []
    in_ref_section = False
    for p in doc.paragraphs:
        if "参考文献" in p["text"] and p["level"] is not None:
            in_ref_section = True
            continue
        if in_ref_section:
            if p["level"] is not None:
                break
            refs.append(p)
    return refs


def _looks_like_reference(text):
    if len(text) < 15:
        return False
    if re.search(r'\b(19|20)\d{2}\b', text):
        return True
    if re.search(r'\[J\]|\[C\]|\[M\]|\[D\]|\[EB', text):
        return True
    return False
