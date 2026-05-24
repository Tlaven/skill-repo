# -*- coding: utf-8 -*-
"""Fix §1.1 三大痛点: remove editorial comments from titles, add (3) description, remove empty paras."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.core import ThesisDoc
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'

def set_text(para, text):
    elem = para._element
    for r in list(elem.findall(w('r'))):
        elem.remove(r)
    for ins in list(elem.findall(w('ins'))):
        elem.remove(ins)
    for d in list(elem.findall(w('del'))):
        elem.remove(d)
    run = etree.SubElement(elem, w('r'))
    t = etree.SubElement(run, w('t'))
    t.text = text
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

def del_para(para):
    para._element.getparent().remove(para._element)

doc = ThesisDoc(r"C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx")

# Find paragraphs by content
paras = doc.raw_paragraphs

# Identify target paragraphs
p1_title = None   # (1) 人才"隐形"化 + comment
p2_title = None   # (2) 人才匹配精度低 + comment
p3_title = None   # (3) 缺乏对人员队伍整体素质的量化评估
empty_paras = []

for i, p in enumerate(paras):
    text = p.text.strip() if p.text else ""
    if text.startswith("（1）人才") and "从人才" in text:
        p1_title = i
    elif text.startswith("（2）人才") and "从人才" in text:
        p2_title = i
    elif text.startswith("（3）缺乏"):
        p3_title = i

# Find empty Body Text paragraphs between (3) and "因此"
found_p3 = False
for i, p in enumerate(paras):
    text = p.text.strip() if p.text else ""
    style = p.style.name if p.style else ""
    if i == p3_title:
        found_p3 = True
        continue
    if found_p3 and "因此" in text:
        break
    if found_p3 and text == "" and style == "Body Text":
        empty_paras.append(i)

print(f"p1_title (1): para {p1_title}")
print(f"p2_title (2): para {p2_title}")
print(f"p3_title (3): para {p3_title}")
print(f"Empty paras between (3) and conclusion: {empty_paras}")

# Fix 1: Clean (1) title
if p1_title is not None:
    set_text(paras[p1_title], "（1）人才\u201c隐形\u201d化")
    print("Fixed (1) title")

# Fix 2: Clean (2) title
if p2_title is not None:
    set_text(paras[p2_title], "（2）人才匹配精度低")
    print("Fixed (2) title")

# Fix 3: Add description for (3)
if p3_title is not None:
    # Insert after p3_title
    NEW_DESC = (
        "现行人员评价主要依赖结构化指标（军衔、岗位、专业等），"
        "缺少对综合素质和隐性能力的系统性评估手段，"
        "难以形成对队伍整体能力的清晰认知，阻碍了精确化的人岗匹配。"
    )
    p3_elem = paras[p3_title]._element
    new_p = etree.fromstring(
        f'<w:p xmlns:w="{W_NS}"><w:r><w:t xml:space="preserve">{NEW_DESC}</w:t></w:r></w:p>'
    )
    p3_elem.addnext(new_p)
    print(f"Added description after (3) at para {p3_title}")

# Fix 4: Delete empty paragraphs (from last to first)
for i in sorted(empty_paras, reverse=True):
    del_para(paras[i])
    print(f"Deleted empty para {i}")

doc.save_zip()
print("Done")
