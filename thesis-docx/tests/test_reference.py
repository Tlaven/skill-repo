"""测试：引用管理"""
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.reference import (
    list_citations, list_references, check_references,
    CITATION_PATTERN, REF_NUM_PATTERN,
)
from lib.editor import replace_text
from tests.conftest import create_test_doc, create_doc_with_headings, cleanup


class TestCitationPattern(unittest.TestCase):
    """测试引用正则匹配。"""

    def test_single_citation(self):
        self.assertTrue(CITATION_PATTERN.search('如文献[1]所示'))
        m = CITATION_PATTERN.search('[1]')
        self.assertEqual(m.group(1), '1')

    def test_multi_citation(self):
        self.assertTrue(CITATION_PATTERN.search('如[1,2]所示'))
        m = CITATION_PATTERN.search('[1,2]')
        self.assertEqual(m.group(1), '1,2')

    def test_multi_citation_chinese_comma(self):
        self.assertTrue(CITATION_PATTERN.search('如[1，2]所示'))
        m = CITATION_PATTERN.search('[1，2]')
        self.assertEqual(m.group(1), '1，2')

    def test_ref_num_pattern(self):
        m = REF_NUM_PATTERN.match('[1] 张三. 标题.')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '1')

    def test_no_false_positive(self):
        """普通文字不含引用时不应匹配"""
        self.assertIsNone(CITATION_PATTERN.search('这是一个普通段落'))


class TestListCitations(unittest.TestCase):
    """测试引用提取。"""

    def setUp(self):
        self.doc, self.path = create_test_doc()

    def tearDown(self):
        cleanup(self.path)

    def test_citations_in_template(self):
        """模板文档含参考文献占位，应被识别为引用"""
        result = list_citations(self.doc)
        # 模板含 [1] 【参考文献占位】 → 应找到至少 1 个引用
        self.assertGreaterEqual(len(result['citations']), 1)

    def test_citations_after_replace(self):
        """替换文字后应能提取引用"""
        # Find a body paragraph and add citations
        for p in self.doc.paragraphs:
            if p['text'].strip() and p['style'] == 'Body Text':
                replace_text(self.doc, p['index'], '如文献[1][2]所示，该方法[3,4]有效。')
                break
        # Re-read
        from lib.core import ThesisDoc
        doc2 = ThesisDoc(self.path)
        result = list_citations(doc2)
        nums = sorted(set(c['ref_num'] for c in result['citations']))
        self.assertEqual(nums, [1, 2, 3, 4])


class TestListReferences(unittest.TestCase):
    """测试参考文献列表提取。"""

    def setUp(self):
        self.doc, self.path = create_test_doc()

    def tearDown(self):
        cleanup(self.path)

    def test_template_has_references(self):
        """模板文档含参考文献条目"""
        result = list_references(self.doc)
        self.assertNotIn('error', result)
        self.assertGreater(result['total'], 0)


if __name__ == '__main__':
    unittest.main()
