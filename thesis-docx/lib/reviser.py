# -*- coding: utf-8 -*-
"""接受/拒绝修订标记。配合 detector.py 使用。
detect-revisions → 检测；accept/reject-revisions → 执行。
"""
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'


def _process_para(p_elem, mode="accept"):
    """处理单个段落的修订，mode='accept' 或 'reject'。"""
    if mode == "accept":
        # <w:ins>: 保留子元素，删除包装
        for ins in list(p_elem.findall(w('ins'))):
            parent = ins.getparent()
            idx = list(parent).index(ins)
            for child in list(ins):
                parent.insert(idx, child)
                idx += 1
            parent.remove(ins)
        # <w:del>: 删除元素及其子内容
        for d in list(p_elem.findall(w('del'))):
            d.getparent().remove(d)
    else:  # reject
        # <w:ins>: 删除元素及其子内容（插入的内容不要了）
        for ins in list(p_elem.findall(w('ins'))):
            ins.getparent().remove(ins)
        # <w:del>: 保留子元素（恢复被删的原文），删除包装
        for d in list(p_elem.findall(w('del'))):
            parent = d.getparent()
            idx = list(parent).index(d)
            for child in list(d):
                parent.insert(idx, child)
                idx += 1
            parent.remove(d)


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
