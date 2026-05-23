"""thesis.docx — 第二批修复

chk 2.3  图3-1 缺少正文引用 — 在3.2节标题后插入"如图3-1所示"
chk 4.1  表编号 7-x → 4-x（第4章的表格 7-1/7-2/7-3/7-4）
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from api import ThesisEditor

SRC = r"C:\Users\TL\.claude\skills\thesis-docx\test-case\thesis.docx"

with ThesisEditor(SRC) as ed:
    # 1. 插入正文引用：图3-1
    print("1/5  插入正文引用「如图3-1所示」...")
    after_idx = ed.doc.find_paragraph_by_text("3.2 QGCG框架总体设计")
    if after_idx is not None:
        ed.insert_paragraph(
            after=after_idx,
            text="QGCG框架的总体架构如图3-1所示。",
            style="body",
        )
        print(f"     在段落 #{after_idx} 后插入")
    else:
        print("     ⚠ 未找到锚定段落")


    # 2. 表7-1 → 表4-1 (para 72 正文)
    print("2/5  表7-1 → 表4-1 ...")
    ed.replace_inline(by_text="如表7-1所示", old="表7-1", new="表4-1")
    print("     完成")

    # 3. 表7-2 → 表4-2 (para 78 正文)
    print("3/5  表7-2 → 表4-2 ...")
    ed.replace_inline(by_text="表7-2展示了", old="表7-2", new="表4-2")
    print("     完成")

    # 4. 表7-3 → 表4-3 (para 79 Caption)
    print("4/5  表7-3 → 表4-3 ...")
    ed.replace_inline(by_text="表7-3 不同方法", old="表7-3", new="表4-3")
    print("     完成")

    # 5. 表7-4 → 表4-4 (para 86 Caption)
    print("5/5  表7-4 → 表4-4 ...")
    ed.replace_inline(by_text="表7-4 消融实验", old="表7-4", new="表4-4")
    print("     完成")

    ed.doc._build_index()
    ed.save()
    print("已保存!")

print("=" * 60)
print("第二批修复完成！")
