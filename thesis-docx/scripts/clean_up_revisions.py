# -*- coding: utf-8 -*-
"""清理跟踪修订：接受所有实质性修订，按列表删除审阅批注。

用法:
  python clean_up_revisions.py <filepath> [-o output.docx] [--comment-list file.json]

--comment-list: JSON 文件，每项为要删除的字符串（默认为内置审阅批注列表）

流程:
  1. 接受所有 w:ins → 剥离标签保留文字
  2. 接受所有 w:del → 删除元素及内容
  3. 逐段删除匹配的批注字符串（replace-inline delete 模式）
"""
import sys, os, json, copy
from lxml import etree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.core import ThesisDoc

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'
NSMAP = {'w': W_NS}

# 默认审阅批注列表（来自实际论文分析）
DEFAULT_COMMENTS = [
    # 摘要 para 23
    '（写得太简单，按摘要模板重复写）',
    # 摘要 para 25
    '摘要参考模板：',

    # 1.1 para 38 — 审阅意见
    '（从人才能力描述方法）',
    # 1.1 para 40 — 审阅意见
    '（从人才匹配的角度讲，算法不行，导致需求和人才难以精确匹配）',
    # 1.1 para 43 — 审阅意见
    '（3）缺乏对人员队伍整体素质的量化评估',

    # 1.4 para 72 — 审阅意见
    '画一张图，描述各章之间的关系。',
    '画一张图，描述各章之间的关系',

    # 2.1 para 74
    '（画一张图便于直观理解什么叫主成分分析）',
    # 2.2 para 78
    '（画一张图便于直观理解什么叫聚类）',
    # 2.3 para 81
    '（画一张图便于直观理解什么叫Embedding）',
    # 2.4 para 84
    '（列点公式）',

    # 3.1 para 96
    '（模型一般都要用图来直观表示）',

    # 4.1 para 133
    '（用图来直观表示什么群体画像与个体画像）',

    # 6.1 para 213
    '（系统设计分为四个层次，哪些属于前端，哪些属于后端，要说清楚，在图中最好用框框起来，便于后面6.2、6.3的内容理解）',
    # 6.5 para 254
    '（分几个小节，分别介绍实验环境、评价指标体系、实验内容、实验结果）',
]


def accept_revisions(doc):
    """Step 1: 接受所有跟踪修订（w:ins unwrap, w:del remove）"""
    body = doc.doc.element.find(w('body'))
    stats = {"ins_accepted": 0, "del_removed": 0}

    for p_elem in body.iter(w('p')):
        # Accept insertions: unwrap <w:ins>, move its children up
        ins_nodes = list(p_elem.findall(w('ins')))
        for ins in ins_nodes:
            children = list(ins)
            for child in children:
                # Strip revision coloring from accepted runs
                rPr = child.find(w('rPr'))
                if rPr is not None:
                    for tag in ('color', 'highlight', 'rPr_ins', 'rPr_del'):
                        attr = rPr.find(w(tag))
                        if attr is not None:
                            rPr.remove(attr)
                ins.addprevious(child)
            p_elem.remove(ins)
            stats["ins_accepted"] += 1

        # Accept deletions: remove <w:del> elements entirely
        del_nodes = list(p_elem.findall(w('del')))
        for d in del_nodes:
            p_elem.remove(d)
            stats["del_removed"] += 1

    return stats


def clean_first_line_comment_paragraphs(doc):
    """修复段落只有批注的问题（形如 '（批注内容）' 或空段落）"""
    body = doc.doc.element.find(w('body'))
    removed = 0
    for p_elem in list(body.iter(w('p'))):
        text = ''.join(t.text or '' for t in p_elem.findall('.//' + w('t')))
        text = text.strip()
        if not text:
            continue
        # 如果段落全部内容都是括号批注，清空它
        if text.startswith('（') and text.endswith('）') and len(text) < 100:
            for t in p_elem.findall('.//' + w('t')):
                parent_t = t.getparent() if t is not None else None
                if parent_t is not None:
                    parent_t.remove(t)
            removed += 1
    return removed


def remove_comment_strings(doc, comment_list):
    """Step 2: 删除段内匹配的批注字符串（replace-inline delete）"""
    stats = {"total_removed": 0, "paras_affected": 0}
    affected = set()

    # Pre-scan: build para_element list (stable identity across iterations)
    body = doc.doc.element.find(w('body'))
    all_paras = list(body.iter(w('p')))

    for comment in comment_list:
        if not comment:
            continue
        for p_elem in all_paras:
            # Collect all text in order
            text_parts = []
            text_positions = []  # (element, start_offset, length)
            for t in p_elem.findall('.//' + w('t')):
                txt = t.text or ''
                start = len(''.join(text_parts))
                text_parts.append(txt)
                text_positions.append((t, start, len(txt)))

            full_text = ''.join(text_parts)
            if comment not in full_text:
                continue

            # Found the comment string - need to remove it from runs
            comment_len = len(comment)
            search_start = 0
            while True:
                idx = full_text.find(comment, search_start)
                if idx == -1:
                    break
                search_start = idx + 1
                affected.add(id(p_elem))
                # Remove matching chars from runs
                remaining = comment_len
                cut_pos = idx
                for t, t_start, t_len in text_positions:
                    if remaining <= 0:
                        break
                    t_end = t_start + t_len
                    if cut_pos >= t_end:
                        continue  # this run is before our match
                    # Calculate overlap
                    overlap_start = max(cut_pos, t_start)
                    overlap_end = min(cut_pos + remaining, t_end)
                    if overlap_start >= overlap_end:
                        continue
                    # Modify this run's text
                    t_text = t.text or ''
                    before = t_text[:overlap_start - t_start]
                    after = t_text[overlap_end - t_start:]
                    new_text = before + after
                    t.text = new_text if new_text else None
                    # Adjust remaining
                    removed_chars = overlap_end - overlap_start
                    remaining -= removed_chars
                    cut_pos = overlap_end

                stats["total_removed"] += 1

        # Recalculate full text after removal for next comment
        # full_text 已被改变但 text_parts 是旧的，recalc 太复杂，break 后重新开始对每个 comment 独立处理
        # 所以我们对每个 comment 重新扫描一次 body
        # 已由外层循环保证

    stats["paras_affected"] = len(affected)
    return stats


def clean_empty_paragraphs(doc):
    """删除 text 为空或只有空格的段落（保留标题）"""
    body = doc.doc.element.find(w('body'))
    removed = 0
    for p_elem in list(body.findall(w('p'))):
        text = ''.join(t.text or '' for t in p_elem.findall('.//' + w('t')))
        if text.strip():
            continue
        # Check if it's a heading
        pPr = p_elem.find(w('pPr'))
        if pPr is not None:
            pStyle = pPr.find(w('pStyle'))
            if pStyle is not None:
                style_val = pStyle.get(f'{{{W_NS}}}val', '')
                if 'Heading' in style_val or 'heading' in style_val:
                    continue  # Keep empty headings
        body.remove(p_elem)
        removed += 1
    return removed


def clean_up(filepath, output_path=None, comment_list=None):
    doc = ThesisDoc(filepath)
    if comment_list is None:
        comment_list = DEFAULT_COMMENTS

    print(f"Processing: {filepath}")
    
    # Step 1: Accept revisions
    accept_stats = accept_revisions(doc)
    print(f"  Accept revisions: {accept_stats['ins_accepted']} insertions accepted, {accept_stats['del_removed']} deletions removed")

    # Step 1.5: Clean paragraphs that are only reviewer comments
    cleaned_first = clean_first_line_comment_paragraphs(doc)
    print(f"  Cleaned {cleaned_first} paragraphs that were only reviewer comments")

    # Step 2: Remove comment strings from paragraphs
    remove_stats = remove_comment_strings(doc, comment_list)
    print(f"  Removed {remove_stats['total_removed']} comment instances from {remove_stats['paras_affected']} paragraphs")

    # Step 3: Clean empty paragraphs
    empty_removed = clean_empty_paragraphs(doc)
    print(f"  Removed {empty_removed} empty paragraphs")

    # Save
    save_path = output_path or filepath
    doc.save_zip(save_path)
    print(f"  Saved to: {save_path}")

    return {
        "accept": accept_stats,
        "first_line_cleaned": cleaned_first,
        "remove": remove_stats,
        "empty_removed": empty_removed,
        "output": save_path
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="清理跟踪修订和审阅批注")
    parser.add_argument("filepath", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（默认覆盖原文件）")
    parser.add_argument("--comment-list", help="批注字符串列表 JSON 文件")
    args = parser.parse_args()

    comment_list = None
    if args.comment_list:
        with open(args.comment_list, 'r', encoding='utf-8') as f:
            comment_list = json.load(f)

    result = clean_up(args.filepath, args.output, comment_list)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
    else:
        print(__doc__)
