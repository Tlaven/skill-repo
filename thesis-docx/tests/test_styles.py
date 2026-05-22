"""测试：段落分类、样式解析"""
import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.styles import (
    classify_paragraph, resolve_style, get_default_rules,
    ROLE_TO_STYLE, STYLE_DEFS,
)
from tests.conftest import create_test_doc, create_doc_with_headings, cleanup


class TestClassifyParagraph(unittest.TestCase):
    """测试 classify_paragraph 的段落角色识别。"""

    def test_chapter_title(self):
        """'1 绪论' 格式 → chapter_title（当前只支持 'N 标题' 格式，不支持 '第N章'）"""
        self.assertEqual(classify_paragraph('1 绪论'), 'chapter_title')
        self.assertEqual(classify_paragraph('2 相关工作'), 'chapter_title')
        # '第N章' 格式暂不支持
        self.assertIsNone(classify_paragraph('第1章 绪论'))

    def test_section_title(self):
        """'1.1 研究背景' → section_title"""
        self.assertEqual(classify_paragraph('1.1 研究背景'), 'section_title')
        self.assertEqual(classify_paragraph('2.3 实验设计'), 'section_title')

    def test_subsection_title(self):
        """'2.2.1 编码器' → subsection_title"""
        self.assertEqual(classify_paragraph('2.2.1 编码器'), 'subsection_title')

    def test_abstract_title(self):
        """'摘  要' → abstract_zh_title"""
        self.assertEqual(classify_paragraph('摘  要'), 'abstract_zh_title')
        self.assertEqual(classify_paragraph('摘要'), 'abstract_zh_title')

    def test_reference_entry(self):
        """'[1] 作者. 标题...' → reference_entry"""
        self.assertEqual(classify_paragraph('[1] 张三. 深度学习研究. 计算机学报, 2024.'), 'reference_entry')

    def test_figure_caption(self):
        """'图3-1 系统架构' → figure_caption"""
        self.assertEqual(classify_paragraph('图3-1 系统架构图'), 'figure_caption')
        self.assertEqual(classify_paragraph('图 4-2 实验结果'), 'figure_caption')

    def test_table_caption(self):
        """'表4-1 实验结果' → table_caption"""
        self.assertEqual(classify_paragraph('表4-1 实验结果对比'), 'table_caption')
        self.assertEqual(classify_paragraph('表 5-3 参数设置'), 'table_caption')

    # ====== 下面是 bug 修复的测试 ======

    def test_long_text_starting_with_table_pattern(self):
        """BUG: '表4-1展示了...' (>=60字) 当前被误判为 table_caption。
        
        lessons.md §11: classify_paragraph 不考虑长度。
        修复后应返回 None（这是普通正文，不是表标题）。
        """
        long_text = '表4-1展示了不同方法在测试集上的性能对比，从表中可以看出，本文提出的方法在准确率和召回率上均有显著提升，证明了本方法的有效性。'
        self.assertGreaterEqual(len(long_text), 60)
        result = classify_paragraph(long_text)
        self.assertIsNone(result, f'BUG: 长文本({len(long_text)}字)被误识别为 {result}，应为 None')

    def test_long_text_starting_with_figure_pattern(self):
        """BUG: '图3-2展示了...' (>=60字) 当前被误判为 figure_caption。"""
        long_text = '图3-2展示了模型的训练曲线，横轴表示迭代次数，纵轴表示损失值，从图中可以看出模型在训练过程中快速收敛，验证了本方法的有效性。'
        self.assertGreaterEqual(len(long_text), 60)
        result = classify_paragraph(long_text)
        self.assertIsNone(result, f'BUG: 长文本({len(long_text)}字)被误识别为 {result}，应为 None')

    def test_short_table_caption(self):
        """短文本 '表4-1 实验结果' 应正常匹配为 table_caption（<=60字）"""
        short = '表4-1 实验结果对比'
        self.assertLessEqual(len(short), 60)
        self.assertEqual(classify_paragraph(short), 'table_caption')

    def test_short_figure_caption(self):
        """短文本 '图3-1 系统架构' 应正常匹配为 figure_caption（<=60字）"""
        short = '图3-1 系统架构'
        self.assertLessEqual(len(short), 60)
        self.assertEqual(classify_paragraph(short), 'figure_caption')

    def test_empty_text(self):
        """空文本返回 None"""
        self.assertIsNone(classify_paragraph(''))
        self.assertIsNone(classify_paragraph('   '))

    def test_normal_body_text(self):
        """普通正文段落返回 None（无法识别）"""
        self.assertIsNone(classify_paragraph('本文提出了一种基于深度学习的方法来解决这一问题。'))


class TestStyleResolution(unittest.TestCase):
    """测试样式解析。"""

    def test_h1_default_size(self):
        """h1 默认字号 18pt"""
        resolved = resolve_style('h1')
        self.assertEqual(resolved.get('size_pt'), 18)

    def test_body_default_font(self):
        """body 默认字体"""
        resolved = resolve_style('body')
        self.assertEqual(resolved.get('font'), 'Times New Roman')
        self.assertEqual(resolved.get('font_east'), '宋体')

    def test_gb_academic_preset(self):
        """gb-academic 预设缩小字号"""
        resolved = resolve_style('body', preset='gb-academic')
        self.assertEqual(resolved.get('size_pt'), 10.5)
        resolved_h1 = resolve_style('h1', preset='gb-academic')
        self.assertEqual(resolved_h1.get('size_pt'), 12)

    def test_caption_figure_alignment(self):
        """图标题默认居中"""
        resolved = resolve_style('caption_figure')
        self.assertEqual(resolved.get('alignment'), 'center')


class TestAssignStyles(unittest.TestCase):
    """测试 assign_styles 在真实文档上的行为。"""

    def setUp(self):
        self.doc, self.path = create_doc_with_headings()

    def tearDown(self):
        cleanup(self.path)

    def test_structure_has_sections(self):
        """文档应包含章节结构"""
        sections = self.doc.sections_tree
        self.assertGreater(len(sections), 0)
        titles = [s['title'] for s in sections]
        self.assertIn('第1章 绪论', titles)

    def test_structure_has_subsections(self):
        """章节应有子节"""
        sections = self.doc.sections_tree
        for s in sections:
            if s['title'] == '第1章 绪论':
                children = s.get('children', [])
                self.assertGreater(len(children), 0)
                self.assertIn('1.1 研究背景', [c['title'] for c in children])


if __name__ == '__main__':
    unittest.main()
