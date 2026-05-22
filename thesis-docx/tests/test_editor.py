"""测试：编辑操作"""
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.editor import (
    replace_text, replace_batch, insert_paragraph, delete_paragraph,
)
from lib.reader import read_structure
from lib.core import ThesisDoc
from tests.conftest import create_test_doc, create_doc_with_headings, cleanup


class TestReplaceText(unittest.TestCase):
    """测试文字替换。"""

    def setUp(self):
        self.doc, self.path = create_test_doc()

    def tearDown(self):
        cleanup(self.path)

    def test_replace_updates_text(self):
        """替换后段落文字应变更"""
        for p in self.doc.paragraphs:
            if p['text'].strip() and p['style'] == 'Body Text':
                idx = p['index']
                old = p['text']
                break
        result = replace_text(self.doc, idx, '新内容')
        self.assertEqual(result['old_text'], old)
        self.assertEqual(result['new_text'], '新内容')
        # Re-verify by re-reading
        doc2 = ThesisDoc(self.path)
        self.assertEqual(doc2.paragraphs[idx]['text'], '新内容')

    def test_replace_preserves_paragraph_count(self):
        """替换不改变段落总数"""
        count_before = len(self.doc.paragraphs)
        for p in self.doc.paragraphs:
            if p['text'].strip() and p['style'] == 'Body Text':
                replace_text(self.doc, p['index'], '测试')
                break
        doc2 = ThesisDoc(self.path)
        self.assertEqual(len(doc2.paragraphs), count_before)


class TestInsertDelete(unittest.TestCase):
    """测试插入和删除段落。"""

    def setUp(self):
        self.doc, self.path = create_test_doc()

    def tearDown(self):
        cleanup(self.path)

    def test_insert_increases_count(self):
        """插入段落后段落数 +1"""
        count_before = len(self.doc.paragraphs)
        insert_paragraph(self.doc, after=5, text='新插入的段落')
        doc2 = ThesisDoc(self.path)
        self.assertEqual(len(doc2.paragraphs), count_before + 1)

    def test_delete_decreases_count(self):
        """删除段落后段落数 -1"""
        count_before = len(self.doc.paragraphs)
        if count_before > 5:
            delete_paragraph(self.doc, paragraph=5)
            doc2 = ThesisDoc(self.path)
            self.assertEqual(len(doc2.paragraphs), count_before - 1)


class TestReadStructure(unittest.TestCase):
    """测试章节结构读取。"""

    def setUp(self):
        self.doc, self.path = create_doc_with_headings()

    def tearDown(self):
        cleanup(self.path)

    def test_read_structure_has_sections(self):
        """read_structure 应返回章节树"""
        result = read_structure(self.doc)
        self.assertIn('sections', result)
        self.assertGreater(len(result['sections']), 0)

    def test_flat_format(self):
        """flat 格式返回一维数组"""
        result = read_structure(self.doc, format='flat')
        self.assertIn('sections', result)
        for s in result['sections']:
            self.assertIn('para_index', s)


if __name__ == '__main__':
    unittest.main()
