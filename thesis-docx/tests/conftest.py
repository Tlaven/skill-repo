"""测试夹具 — 创建临时 .docx 供测试使用"""
import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.core import ThesisDoc
from lib.creator import create_thesis


def create_test_doc():
    """创建一个标准的测试用论文模板，返回 (ThesisDoc, filepath)。"""
    fd, path = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    doc = ThesisDoc(path, create=True)
    create_thesis(doc)
    # Re-read to build proper index
    doc2 = ThesisDoc(path)
    return doc2, path


def create_doc_with_headings():
    """创建含多层次标题的测试文档。"""
    fd, path = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    doc = ThesisDoc(path, create=True)
    create_thesis(doc)
    from lib.editor import replace_text
    doc2 = ThesisDoc(path)
    replace_text(doc2, 0, "摘  要")
    replace_text(doc2, 8, "第1章 绪论")
    replace_text(doc2, 9, "1.1 研究背景")
    replace_text(doc2, 11, "1.2 研究目标")
    replace_text(doc2, 13, "第2章 方法")
    replace_text(doc2, 14, "2.1 数据采集")
    replace_text(doc2, 16, "2.2 模型设计")
    replace_text(doc2, 18, "2.2.1 编码器")
    replace_text(doc2, 20, "2.2.2 解码器")
    doc3 = ThesisDoc(path)
    return doc3, path


def cleanup(path):
    """删除临时文件。"""
    if os.path.exists(path):
        os.unlink(path)
