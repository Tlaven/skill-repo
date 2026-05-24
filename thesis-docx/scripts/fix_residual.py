# -*- coding: utf-8 -*-
"""Remove comment runs from heading, fix EN abstract."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.core import ThesisDoc
from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
w = lambda tag: f'{{{W_NS}}}{tag}'

doc = ThesisDoc(r"C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx")

# Fix 1: Remove comment runs from heading (para 23)
# Keep only first 3 runs (摘, 空格, 要), remove runs 3+
p = doc.raw_paragraphs[23]
runs = list(p._element.findall(w('r')))
print(f"Heading has {len(runs)} runs, keeping first 3, removing {len(runs)-3}")
for r in runs[3:]:
    p._element.remove(r)

text = ''.join(t.text or '' for t in p._element.iter(w('t')))
print(f"Heading now: [{text}]")

# Fix 2: Fix EN abstract cosine wording
pa = doc.raw_paragraphs[27]
for r in pa._element.findall(w('r')):
    t = r.find(w('t'))
    if t is not None and t.text and "cosine" in t.text:
        t.text = t.text.replace("cosine粗筛", "cosine similarity matching")
        print(f"Fixed: {t.text[:60]}...")

doc.save_zip()
print("Done")
