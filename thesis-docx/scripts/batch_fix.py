"""thesis.docx — 批量修复脚本

修复项：
1. 页面设置 → A4 (21x29.7cm), 边距 2.5cm
2. 图片编号 图6-1 → 图3-1
3. 公式编号 (4.1)→(2.1), (4.2)→(2.2)
4. 清理 FORMULA_X_X 占位符
5. 删除测试残留段落
6. 删除占位符表格（无实际内容）
7. "已替换摘要" → "摘要"
"""

import sys, os, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from api import ThesisEditor
from lxml import etree

NSMAP = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}

SRC = r"C:\Users\TL\.claude\skills\thesis-docx\test-case\thesis.docx"
BACKUP = SRC.replace(".docx", f"_backup_{int(__import__('time').time())}.docx")

print("=" * 60)
print("1/8  创建备份...")
shutil.copy2(SRC, BACKUP)
print(f"     备份: {BACKUP}")

with ThesisEditor(SRC) as ed:
    # =========================================================
    # 2/8  页面设置 — A4 21x29.7cm, 边距 2.5cm
    # =========================================================
    print("2/8  修复页面设置...")
    result = ed.set_page_setup(
        width=21, height=29.7,
        margin_top=2.5, margin_bottom=2.5,
        margin_left=2.5, margin_right=2.5,
    )
    print(f"     页面设置: width={result.get('width')} height={result.get('height')}")

    # =========================================================
    # 3/8  图片编号 图6-1 → 图3-1 (para 54)
    # =========================================================
    print("3/8  修复图片编号...")
    ed.replace_inline(
        by_text="图6-1 QGCG框架架构图",
        old="图6-1", new="图3-1",
    )
    print(f"     图6-1 → 图3-1")

    # =========================================================
    # 4/8  公式编号 + 清理 FORMULA 占位符
    # =========================================================
    print("4/8  修复公式编号 & 清理 FORMULA 占位符...")

    # para 30: 式(4.1) → 式(2.1), 删除 FORMULA_4_1
    ed.replace_inline(
        by_text="其计算方式如式(4.1)所示",
        old="式(4.1)", new="式(2.1)",
    )
    ed.replace_inline(
        by_text="FORMULA_4_1",
        old="FORMULA_4_1", new="",
    )

    # para 31: 公式编号 (4.1) → (2.1)
    ed.replace_inline(
        by_text="\t(4.1)",
        old="(4.1)", new="(2.1)",
    )

    # para 34: 式(4.2) → 式(2.2), 删除 FORMULA_4_2
    ed.replace_inline(
        by_text="如式(4.2)所示",
        old="式(4.2)", new="式(2.2)",
    )
    ed.replace_inline(
        by_text="FORMULA_4_2",
        old="FORMULA_4_2", new="",
    )

    # para 35: 公式编号 (4.2) → (2.2)
    ed.replace_inline(
        by_text="\t(4.2)",
        old="(4.2)", new="(2.2)",
    )
    print("     公式编号修复完成")

    # =========================================================
    # 5/8  删除测试残留段落（从后往前防索引漂移）
    # =========================================================
    print("5/8  删除测试残留段落...")
    paras_to_delete = []
    for idx, p in enumerate(ed.doc.raw_paragraphs):
        t = p.text.strip()
        if t in ("测试插入段", "核心创新在于模块化设计", "每个模块可独立优化", "测试写入段B", "IMAGE_3_1"):
            paras_to_delete.append(idx)

    # 从后往前删
    for idx in sorted(paras_to_delete, reverse=True):
        ed.doc.raw_paragraphs[idx]._element.getparent().remove(
            ed.doc.raw_paragraphs[idx]._element
        )
        print(f"     删除段落 #{idx}")

    # 删除 "喂，看到了吗？" from para 62 (原索引)
    ed.replace_inline(
        by_text="喂，看到了吗？",
        old="喂，看到了吗？", new="",
    )
    print(f"     删除多余文字 '喂，看到了吗？'")

    # =========================================================
    # 6/8  删除占位符表格
    # =========================================================
    print("6/8  删除占位符表格...")
    body = ed.doc.doc.element.body
    tables_to_delete = []

    # 收集需要删除的表格索引
    # 表1 (index 1): 标题 [a,b] 数据 [c,d] — 占位符
    # 表0 (index 0): 标题 [A,B] 数据 [3,4] — 占位符
    for ti, tbl in enumerate(ed.doc.raw_tables):
        rows = [[c.text.strip() for c in r.cells] for r in tbl.rows]
        header = rows[0] if rows else []
        data = rows[1:] if len(rows) > 1 else []
        is_placeholder = False

        # 表0: A/B/3/4
        if header == ["A", "B"] and data == [["3", "4"]]:
            is_placeholder = True
        # 表1 (index 1): 实际上是第二个表，有指标/数值/准确率/0.95 — 保留
        # 表2 (index 2): a/b/c/d — 占位符
        elif header == ["a", "b"] and data == [["c", "d"]]:
            is_placeholder = True
        # 表3 (index 3): 模型/精度/U-Net/0.92 — 不相关数据，删除
        elif header == ["模型", "精度"] and data == [["U-Net", "0.92"]]:
            is_placeholder = True

        if is_placeholder:
            # 在 body 中找到并删除此表格
            tbl_element = tbl._tbl
            if tbl_element in body:
                body.remove(tbl_element)
                print(f"     删除表格 #{ti}: header={header} data={data}")

    # =========================================================
    # 7/8  "已替换摘要" → "摘要"
    # =========================================================
    print("7/8  修复摘要标题...")
    ed.replace_inline(
        by_text="已替换摘要",
        old="已替换摘要", new="摘要",
    )
    print(f"     '已替换摘要' → '摘要'")

    # =========================================================
    # 8/8  重建索引 + 保存
    # =========================================================
    print("8/8  重建索引 & 保存...")
    ed.doc._build_index()
    ed.save()
    print(f"     已保存: {SRC}")

print("=" * 60)
print("全部修复完成!")
print(f"备份文件: {BACKUP}")
