# -*- coding: utf-8 -*-
"""Debug heading paragraph 23."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.core import ThesisDoc
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'

doc = ThesisDoc(r"C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx")
p = doc.raw_paragraphs[23]
print(f"Full text: {repr(p.text)}")
print(f"Run count: {len(p._element.findall(w('r')))}")
for i, r in enumerate(p._element.findall(w('r'))):
    t = r.find(w('t'))
    txt = t.text if t is not None else None
    print(f"  Run {i}: {repr(txt)}")
