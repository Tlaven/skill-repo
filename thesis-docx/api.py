"""ThesisDocx Python API — 编程接口，直接调用 lib/，无 argparse 依赖

用法:
    from api import ThesisEditor
    with ThesisEditor("论文.docx") as editor:
        editor.replace_paragraph(43, "新内容")
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

    # ========== 读取 ==========

    def read_structure(self, format='tree'):
        from lib.reader import read_structure
        return read_structure(self.doc, format=format)

    def read_paragraph(self, index, with_format=False):
        from lib.reader import read_paragraph
        return read_paragraph(self.doc, index=index, with_format=with_format)

    def read_paragraphs(self, start, end, with_format=False):
        from lib.reader import read_paragraphs
        return read_paragraphs(self.doc, start=start, end=end, with_format=with_format)

    def read_section(self, title=None, level=None, index=None):
        from lib.reader import read_section
        return read_section(self.doc, title=title, level=level, index=index)

    def read_stats(self):
        from lib.reader import read_stats
        return read_stats(self.doc)

    def read_images(self):
        from lib.reader import read_images
        return read_images(self.doc)

    def read_tables(self):
        from lib.reader import read_tables
        return read_tables(self.doc)

    def read_page_setup(self):
        from lib.reader import read_page_setup
        return read_page_setup(self.doc)

    def read_comments(self):
        from lib.reader import read_comments
        return read_comments(self.doc)

    def read_full(self, section=None, paragraphs=None):
        from lib.reader import read_full
        return read_full(self.doc, section=section, paragraphs=paragraphs)

    def read_formulas(self):
        from lib.reader import read_formulas
        return read_formulas(self.doc)

    def read_location(self, paragraph):
        from lib.reader import read_location
        return read_location(self.doc, paragraph=paragraph)

    # ========== 搜索 ==========

    def search(self, query, regex=False, chapter=None, section=None, context=0, limit=20):
        from lib.searcher import search
        return search(self.doc, query=query, regex=regex, chapter=chapter,
                      section=section, context=context, limit=limit)

    # ========== 编辑 ==========

    def replace_paragraph(self, index, text):
        from lib.editor import replace_text
        return replace_text(self.doc, paragraph=index, text=text)

    def replace_batch_by_index(self, pairs):
        """按索引批量替换。pairs: {43: "文本A", 49: "文本B"}"""
        import json, tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({str(k): v for k, v in pairs.items()}, f, ensure_ascii=False)
            tmp_path = f.name
        try:
            from lib.editor import replace_batch_by_index
            return replace_batch_by_index(self.doc, pairs_file=tmp_path)
        finally:
            os.unlink(tmp_path)

    def insert_paragraph(self, after, text, style='body'):
        from lib.editor import insert_paragraph
        result = insert_paragraph(self.doc, after=after, text=text, style=style)
        self.doc._build_index()
        return result

    def delete_paragraph(self, index):
        from lib.editor import delete_paragraph
        result = delete_paragraph(self.doc, paragraph=index)
        self.doc._build_index()
        return result

    def assign_styles(self, rules=None, preset=None):
        from lib.fixer import assign_styles
        return assign_styles(self.doc, rules=rules, preset=preset)

    def replace_inline(self, paragraph=None, by_text=None, old=None, new=None,
                       bold=None, font=None, font_east=None, size=None, color=None):
        from lib.editor import replace_inline
        if by_text is not None:
            for i, p in enumerate(self.doc.raw_paragraphs):
                if by_text in (p.text or ""):
                    paragraph = i
                    break
            if paragraph is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        return replace_inline(self.doc, paragraph=paragraph, old=old, new=new,
                              bold=bold, font=font, font_east=font_east,
                              size=size, color=color)

    def set_page_setup(self, width=None, height=None,
                       margin_top=None, margin_bottom=None,
                       margin_left=None, margin_right=None):
        from lib.layout import set_page_setup
        return set_page_setup(self.doc, width=width, height=height,
                             margin_top=margin_top, margin_bottom=margin_bottom,
                             margin_left=margin_left, margin_right=margin_right)

    def set_format(self, style, paragraph=None, start=None, end=None, target=None, rules=None):
        from lib.editor import set_format
        return set_format(self.doc, style=style, paragraph=paragraph, start=start,
                         end=end, target=target, rules=rules)

    def insert_image(self, after, image, width=None, caption=None):
        from lib.editor import insert_image
        return insert_image(self.doc, after=after, image=image, width=width, caption=caption)

    def insert_table(self, after, data):
        from lib.editor import insert_table
        return insert_table(self.doc, after=after, data=data)

    def replace_image(self, image, caption=None, paragraph=None, media=None):
        from lib.editor import replace_image
        return replace_image(self.doc, image=image, caption=caption,
                            paragraph=paragraph, media=media)

    # ========== 引用 ==========

    def list_references(self):
        from lib.reference import list_references
        return list_references(self.doc)

    def renumber_references(self, output):
        from lib.reference import renumber_references
        return renumber_references(self.doc, output=output)

    # ========== 保存 ==========

    def save(self, output_path=None):
        path = output_path or self.filepath
        self.doc.save(path)
        return path

    def save_zip(self, output_path=None):
        return self.doc.save_zip(output_path)

    # ========== 属性 ==========

    @property
    def paragraphs(self):
        return self.doc.paragraphs

    @property
    def sections(self):
        return self.doc.sections_tree
