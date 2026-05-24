# -*- coding: utf-8 -*-
"""Fix remaining issues: heading comment and EN abstract wording."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.core import ThesisDoc
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'

doc = ThesisDoc(r"C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx")

para = doc.raw_paragraphs[23]
for r in list(para._element.findall(w('r'))):
    t = r.find(w('t'))
    if t is not None and t.text and ("写得太简单" in t.text or "摘要模板" in t.text):
        para._element.remove(r)
        print(f"Removed: {t.text}")

para_en = doc.raw_paragraphs[27]
for r in para_en._element.findall(w('r')):
    t = r.find(w('t'))
    if t is not None and t.text and "cosine" in t.text and "筛" in t.text:
        t.text = t.text.replace("cosine粗筛", "cosine similarity filtering")
        print(f"Fixed EN text")

doc.save_zip()
print("Done")
