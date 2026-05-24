# -*- coding: utf-8 -*-
"""Tidy up §1.1: remove remaining empty para, fix style of new description."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.core import ThesisDoc
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'

doc = ThesisDoc(r"C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx")
paras = doc.raw_paragraphs

# Find and delete empty para between (2) description and (3)
for i, p in enumerate(paras):
    text = p.text.strip() if p.text else ""
    if text == "（3）缺乏对人员队伍整体素质的量化评估":
        # Check paragraph before (3) title
        prev = paras[i - 1]
        prev_text = prev.text.strip() if prev.text else ""
        if prev_text == "":
            prev._element.getparent().remove(prev._element)
            print(f"Removed empty para before (3) at index {i-1}")
        break

# Find the new description and fix its style
for i, p in enumerate(paras):
    text = p.text.strip() if p.text else ""
    if text.startswith("现行人员评价主要依赖"):
        if p.style.name != "Body Text":
            p.style = doc.doc.styles["Body Text"]
            print(f"Fixed style of new description at para {i}")
        break

doc.save_zip()
print("Done")
