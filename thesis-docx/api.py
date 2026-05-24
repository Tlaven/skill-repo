"""ThesisDocx Python API — 编程接口，直接调用 lib/，无 argparse 依赖

用法:
    from api import ThesisEditor
    with ThesisEditor("论文.docx") as editor:
        editor.replace_text(43, "新内容")
        editor.save()
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.core import ThesisDoc


class ThesisEditor:
    """论文文档编辑器 — 编程接口，支持上下文管理器。"""

    def __init__(self, filepath):
        self.filepath = os.path.abspath(filepath)
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"文件不存在: {self.filepath}")
        self.doc = ThesisDoc(self.filepath)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    # ==================== 读取 ====================

    def read_structure(self, format='tree', verify=False):
        from lib.reader import read_structure
        return read_structure(self.doc, format=format, verify=verify)

    def read_paragraph(self, index, with_format=False, deep=False):
        from lib.reader import read_paragraph
        return read_paragraph(self.doc, index=index, with_format=with_format, deep=deep)

    def read_paragraphs(self, start, end, with_format=False):
        from lib.reader import read_paragraphs
        return read_paragraphs(self.doc, start=start, end=end, with_format=with_format)

    def read_section(self, title=None, level=None, index=None, deep=False, verify=False):
        from lib.reader import read_section
        return read_section(self.doc, title=title, level=level, index=index, deep=deep, verify=verify)

    def read_stats(self):
        from lib.reader import read_stats
        return read_stats(self.doc)

    def read_images(self):
        from lib.reader import read_images
        return read_images(self.doc)

    def read_image(self, id, extract=False, output_dir=None, deep=False):
        from lib.reader import read_image
        return read_image(self.doc, id=id, extract=extract, output_dir=output_dir, deep=deep)

    def read_tables(self):
        from lib.reader import read_tables
        return read_tables(self.doc)

    def read_table(self, index, deep=False):
        from lib.reader import read_table
        return read_table(self.doc, index=index, deep=deep)

    def read_table_context(self, index):
        from lib.reader import read_table_context
        return read_table_context(self.doc, index=index)

    def read_page_setup(self, verify=False):
        from lib.reader import read_page_setup
        return read_page_setup(self.doc, verify=verify)

    def read_comments(self):
        from lib.reader import read_comments
        return read_comments(self.doc)

    def read_full(self, section=None, paragraphs=None):
        from lib.reader import read_full
        return read_full(self.doc, section=section, paragraphs=paragraphs)

    def read_formulas(self, summary=False):
        from lib.reader import read_formulas
        return read_formulas(self.doc, summary=summary)

    def read_location(self, paragraph):
        from lib.reader import read_location
        return read_location(self.doc, paragraph=paragraph)

    # ==================== 搜索 ====================

    def search(self, query, regex=False, chapter=None, section=None, context=0, limit=20):
        from lib.searcher import search
        return search(self.doc, query=query, regex=regex, chapter=chapter,
                      section=section, context=context, limit=limit)

    def search_by_style(self, style):
        from lib.searcher import search_by_style
        return search_by_style(self.doc, style=style)

    def search_format(self, target='all'):
        from lib.searcher import search_format
        return search_format(self.doc, target=target)

    # ==================== 编辑 ====================

    def _resolve_by_text(self, by_text):
        if by_text is None:
            return None
        for i, p in enumerate(self.doc.raw_paragraphs):
            if by_text in (p.text or ""):
                return i
        return None

    def replace_text(self, index, text):
        from lib.editor import replace_text
        return replace_text(self.doc, paragraph=index, text=text)

    def replace_inline(self, paragraph=None, by_text=None, old=None, new=None,
                       bold=None, font=None, font_east=None, size=None, color=None):
        from lib.editor import replace_inline
        if paragraph is None and by_text is not None:
            paragraph = self._resolve_by_text(by_text)
            if paragraph is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        return replace_inline(self.doc, paragraph=paragraph, old=old, new=new or "",
                              bold=bold, font=font, font_east=font_east,
                              size=size, color=color)

    def format_inline(self, paragraph=None, by_text=None, target=None,
                      bold=None, font=None, font_east=None, size=None, color=None):
        from lib.editor import format_inline
        if paragraph is None and by_text is not None:
            paragraph = self._resolve_by_text(by_text)
            if paragraph is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        return format_inline(self.doc, paragraph=paragraph, target=target,
                             bold=bold, font=font, font_east=font_east,
                             size=size, color=color)

    def replace_batch(self, pairs, chapter=None):
        from lib.editor import replace_batch
        return replace_batch(self.doc, pairs=pairs, chapter=chapter)

    def replace_batch_by_index(self, pairs):
        import json, tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({str(k): v for k, v in pairs.items()}, f, ensure_ascii=False)
            tmp_path = f.name
        try:
            from lib.editor import replace_batch_by_index
            return replace_batch_by_index(self.doc, pairs_file=tmp_path)
        finally:
            os.unlink(tmp_path)

    def insert_paragraph(self, after, text=None, style='body'):
        from lib.editor import insert_paragraph
        result = insert_paragraph(self.doc, after=after, text=text, style=style)
        self.doc._build_index()
        return result

    def write_paragraphs(self, after, data):
        from lib.editor import write_paragraphs
        result = write_paragraphs(self.doc, after=after, data=data)
        self.doc._build_index()
        return result

    def delete_paragraph(self, index=None, by_text=None):
        from lib.editor import delete_paragraph
        if index is None and by_text is not None:
            index = self._resolve_by_text(by_text)
            if index is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        if index is None:
            return {"error": "请提供 index 或 by_text"}
        result = delete_paragraph(self.doc, paragraph=index)
        self.doc._build_index()
        return result

    def accept_revisions(self, start, end):
        from lib.reviser import _process_para, _find_para_elem
        count = 0
        for idx in range(start, end + 1):
            try:
                p = _find_para_elem(self.doc, idx)
                ins_list = p.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ins')
                del_list = p.findall('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}del')
                if ins_list or del_list:
                    _process_para(p, "accept")
                    count += len(ins_list) + len(del_list)
            except IndexError:
                break
        from lib.detector import detect_revisions
        after = detect_revisions(self.doc)
        return {"accepted": count, "revisions_remaining": after["summary"]["total_revisions"]}

    def detect_revisions(self):
        from lib.detector import detect_revisions
        return detect_revisions(self.doc)

    def set_format(self, style, paragraph=None, start=None, end=None, target=None, rules=None):
        from lib.editor import set_format
        return set_format(self.doc, style=style, paragraph=paragraph, start=start,
                         end=end, target=target, rules=rules)

    def replace_table(self, index, data):
        from lib.editor import replace_table
        return replace_table(self.doc, index=index, data=data)

    def insert_table(self, after, data=None):
        from lib.editor import insert_table
        result = insert_table(self.doc, after=after, data=data)
        self.doc._build_index()
        return result

    def insert_image(self, after, image=None, width=None, caption=None):
        from lib.editor import insert_image
        result = insert_image(self.doc, after=after, image=image, width=width,
                              caption=caption)
        self.doc._build_index()
        return result

    def replace_image(self, image, caption=None, paragraph=None, media=None):
        from lib.editor import replace_image
        return replace_image(self.doc, image=image, caption=caption,
                            paragraph=paragraph, media=media)

    def delete_comments(self):
        from lib.fixer import delete_comments
        return delete_comments(self.doc)

    # ==================== 格式修复 ====================

    def assign_styles(self, rules=None, preset=None):
        from lib.fixer import assign_styles
        return assign_styles(self.doc, rules=rules, preset=preset)

    def fix_format(self, rules=None, preset=None):
        from lib.fixer import fix_format
        return fix_format(self.doc, rules=rules, preset=preset)

    def fix_page_setup(self, rules=None):
        from lib.fixer import fix_page_setup
        return fix_page_setup(self.doc, rules=rules)

    def apply_template(self, template_path):
        from lib.fixer import apply_template
        return apply_template(self.doc, template_path=template_path)

    # ==================== 页面布局 ====================

    def set_page_setup(self, width=None, height=None,
                       margin_top=None, margin_bottom=None,
                       margin_left=None, margin_right=None):
        from lib.layout import set_page_setup
        return set_page_setup(self.doc, width=width, height=height,
                             margin_top=margin_top, margin_bottom=margin_bottom,
                             margin_left=margin_left, margin_right=margin_right)

    def insert_page_break(self, after):
        from lib.layout import insert_page_break
        result = insert_page_break(self.doc, after=after)
        self.doc._build_index()
        return result

    def set_header(self, text, font='宋体', size='9'):
        from lib.layout import set_header
        return set_header(self.doc, text=text, font=font, size=size)

    def set_footer(self, text=None, page_number=False, align='center', font='宋体', size='9'):
        from lib.layout import set_footer
        return set_footer(self.doc, text=text, page_number=page_number,
                         align=align, font=font, size=size)

    def renumber_figures(self):
        from lib.layout import renumber_figures
        return renumber_figures(self.doc)

    # ==================== 引用 ====================

    def list_citations(self):
        from lib.reference import list_citations
        return list_citations(self.doc)

    def list_references(self, verify=False):
        from lib.reference import list_references
        return list_references(self.doc, verify=verify)

    def renumber_references(self, output):
        from lib.reference import renumber_references
        return renumber_references(self.doc, output=output)

    def add_reference(self, text, position=None):
        from lib.reference import add_reference
        return add_reference(self.doc, text=text, position=position)

    def remove_reference(self, number):
        from lib.reference import remove_reference
        return remove_reference(self.doc, number=number)

    # ==================== 公式 ====================

    def insert_formula(self, after, latex=None, number=None):
        from lib.formula import insert_formula
        result = insert_formula(self.doc, after_index=after, latex_str=latex, eq_number=number)
        self.doc._build_index()
        return result

    def insert_formulas(self, formulas):
        from lib.formula import insert_formulas_batch
        result = insert_formulas_batch(self.doc, formulas=formulas)
        self.doc._build_index()
        return result

    def list_formulas(self):
        """已弃用，请用 read_formulas(summary=True)。"""
        from lib.formula import list_formulas
        return list_formulas(self.doc)

    # ==================== 导出 ====================

    def export_markdown(self, output=None):
        from lib.exporter import export_markdown
        return export_markdown(self.doc, output=output)

    def export_section(self, title, output=None):
        from lib.exporter import export_section
        return export_section(self.doc, title=title, output=output)

    def export_images(self, output_dir):
        from lib.exporter import export_images
        return export_images(self.doc, output_dir=output_dir)

    def export_diff(self, file_new, output=None):
        from lib.exporter import export_diff
        return export_diff(self.doc, file_new=file_new, output=output)

    # ==================== 提取 ====================

    def extract_text(self, start=None, end=None, section=None, output=None):
        from lib.extractor import extract_text
        return extract_text(self.doc, start=start, end=end, section=section, output=output)

    def extract_rules(self, output=None):
        from lib.extractor import extract_rules
        return extract_rules(self.doc, output=output)

    # ==================== 保存 ====================

    def save(self, output_path=None):
        path = self.doc.save_zip(output_path or self.filepath)
        return path

    def save_zip(self, output_path=None):
        return self.doc.save_zip(output_path)

    # ==================== 属性 ====================

    @property
    def paragraphs(self):
        return self.doc.paragraphs

    @property
    def sections(self):
        return self.doc.sections_tree
