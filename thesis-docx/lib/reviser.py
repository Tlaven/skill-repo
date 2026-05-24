# -*- coding: utf-8 -*-
"""接受/拒绝修订标记 — 支持全量 + 单条操作。

工作流：
  detect-revisions → 逐条判断 → accept_revision / reject_revision

Agent 必须逐条操作，不得绕过判断直接调用 accept_all。
"""
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'


# ── 内部工具 ──

def _get_ins_text(ins):
    """获取 <w:ins> 内的全部文本。"""
    return ''.join(t.text or '' for t in ins.findall('.//' + w('t')))


def _get_del_text(d):
    """获取 <w:del> 内的被删文本。"""
    return ''.join(t.text or '' for t in d.findall('.//' + w('delText')))


def _find_para_elem(doc, para_index):
    """按索引获取段落 XML 元素。"""
    try:
        return doc.raw_paragraphs[para_index]._element
    except IndexError:
        raise IndexError(f"段落索引 {para_index} 超出范围 (0-{len(doc.raw_paragraphs)-1})")


def _accept_ins(ins):
    """接受一条插入：保留子元素，删除包装。"""
    parent = ins.getparent()
    idx = list(parent).index(ins)
    for child in list(ins):
        parent.insert(idx, child)
        idx += 1
    parent.remove(ins)


def _reject_ins(ins):
    """拒绝一条插入：删除元素及其子内容。"""
    ins.getparent().remove(ins)


def _accept_del(d):
    """接受一条删除：删除元素及其子内容。"""
    d.getparent().remove(d)


def _reject_del(d):
    """拒绝一条删除：保留子元素，删除包装。"""
    parent = d.getparent()
    idx = list(parent).index(d)
    for child in list(d):
        parent.insert(idx, child)
        idx += 1
    parent.remove(d)


# ── 全量操作 ──

def _process_para(p_elem, mode="accept"):
    """处理单个段落的所有修订。"""
    if mode == "accept":
        for ins in list(p_elem.findall(w('ins'))):
            _accept_ins(ins)
        for d in list(p_elem.findall(w('del'))):
            _accept_del(d)
    else:
        for ins in list(p_elem.findall(w('ins'))):
            _reject_ins(ins)
        for d in list(p_elem.findall(w('del'))):
            _reject_del(d)


def accept_all_revisions(doc):
    """接受文档中所有修订标记。"""
    body = doc.doc.element.body
    for p_elem in body.iter(w('p')):
        _process_para(p_elem, "accept")
    for tbl in body.iter(w('tbl')):
        for p_elem in tbl.iter(w('p')):
            _process_para(p_elem, "accept")


def reject_all_revisions(doc):
    """拒绝文档中所有修订标记。"""
    body = doc.doc.element.body
    for p_elem in body.iter(w('p')):
        _process_para(p_elem, "reject")
    for tbl in body.iter(w('tbl')):
        for p_elem in tbl.iter(w('p')):
            _process_para(p_elem, "reject")


# ── 单条操作 ──

def accept_revision(doc, para_index, match_text):
    """接受一条修订：按段落索引 + 文本内容匹配。

    返回 {"accepted": True, "type": "insertion|deletion", "para_index": N, "text": "..."}
    或 {"accepted": False, "error": "未找到匹配的修订"}。
    """
    p_elem = _find_para_elem(doc, para_index)
    for ins in p_elem.findall(w('ins')):
        if match_text in _get_ins_text(ins):
            _accept_ins(ins)
            return {
                "accepted": True, "type": "insertion",
                "para_index": para_index, "text": match_text,
            }
    for d in p_elem.findall(w('del')):
        if match_text in _get_del_text(d):
            _accept_del(d)
            return {
                "accepted": True, "type": "deletion",
                "para_index": para_index, "text": match_text,
            }
    return {"accepted": False, "error": f"在段落 {para_index} 中未找到匹配 '{match_text[:30]}' 的修订"}


def reject_revision(doc, para_index, match_text):
    """拒绝一条修订：按段落索引 + 文本内容匹配。

    返回 {"rejected": True, "type": "insertion|deletion", "para_index": N, "text": "..."}
    或 {"rejected": False, "error": "未找到匹配的修订"}。
    """
    p_elem = _find_para_elem(doc, para_index)
    for ins in p_elem.findall(w('ins')):
        if match_text in _get_ins_text(ins):
            _reject_ins(ins)
            return {
                "rejected": True, "type": "insertion",
                "para_index": para_index, "text": match_text,
            }
    for d in p_elem.findall(w('del')):
        if match_text in _get_del_text(d):
            _reject_del(d)
            return {
                "rejected": True, "type": "deletion",
                "para_index": para_index, "text": match_text,
            }
    return {"rejected": False, "error": f"在段落 {para_index} 中未找到匹配 '{match_text[:30]}' 的修订"}
