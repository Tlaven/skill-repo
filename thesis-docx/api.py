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

    def __init__(self, filepath, auto_backup=True):
        self.filepath = os.path.abspath(filepath)
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"文件不存在: {self.filepath}")
        self.doc = ThesisDoc(self.filepath)
        self._auto_backup = auto_backup
        self._backup_done = False
        self._op_count = 0

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

    def search(self, query=None, regex=False, chapter=None, section=None, context=0, limit=20, writing_style=False):
        from lib.searcher import search
        return search(self.doc, query=query, regex=regex, chapter=chapter,
                      section=section, context=context, limit=limit, writing_style=writing_style)

    def search_by_style(self, style):
        from lib.searcher import search_by_style
        return search_by_style(self.doc, style=style)

    def search_format(self, target='all'):
        from lib.searcher import search_format
        return search_format(self.doc, target=target)

    def search_xml(self, query, regex=False, context=80, limit=50):
        from lib.searcher import search_xml
        return search_xml(self.doc, query=query, regex=regex, context=context, limit=limit)

    # ==================== 编辑 ====================

    def _resolve_by_text(self, by_text):
        if by_text is None:
            return None
        for i, p in enumerate(self.doc.raw_paragraphs):
            if by_text in (p.text or ""):
                return i
        return None

    def replace_text(self, index=None, text=None, by_text=None):
        self._ensure_backup()
        if index is None and by_text is not None:
            index = self._resolve_by_text(by_text)
            if index is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        if index is None:
            return {"error": "请提供 index 或 by_text"}
        from lib.editor import replace_text
        result = replace_text(self.doc, paragraph=index, text=text)
        self.doc._build_index()
        return self._track_op(result, 'replace-text')

    def replace_inline(self, paragraph=None, by_text=None, old=None, new=None,
                       bold=None, font=None, font_east=None, size=None, color=None):
        self._ensure_backup()
        if paragraph is None and by_text is None:
            return {"error": "请提供 paragraph 或 by_text"}
        from lib.editor import replace_inline
        if paragraph is None and by_text is not None:
            paragraph = self._resolve_by_text(by_text)
            if paragraph is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        result = replace_inline(self.doc, paragraph=paragraph, old=old, new=new or "",
                              bold=bold, font=font, font_east=font_east,
                              size=size, color=color)
        self.doc._build_index()
        return self._track_op(result, 'replace-inline')

    def format_inline(self, paragraph=None, by_text=None, target=None,
                      bold=None, font=None, font_east=None, size=None, color=None):
        self._ensure_backup()
        if paragraph is None and by_text is None:
            return {"error": "请提供 paragraph 或 by_text"}
        from lib.editor import format_inline
        if paragraph is None and by_text is not None:
            paragraph = self._resolve_by_text(by_text)
            if paragraph is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        result = format_inline(self.doc, paragraph=paragraph, target=target,
                             bold=bold, font=font, font_east=font_east,
                             size=size, color=color)
        self.doc._build_index()
        return self._track_op(result, 'format-inline')

    def replace_batch(self, pairs, chapter=None):
        self._ensure_backup()
        from lib.editor import replace_batch
        result = replace_batch(self.doc, pairs=pairs, chapter=chapter)
        self.doc._build_index()
        return self._track_op(result, 'replace-batch')

    def replace_batch_by_index(self, pairs):
        self._ensure_backup()
        import json, tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump({str(k): v for k, v in pairs.items()}, f, ensure_ascii=False)
            tmp_path = f.name
        try:
            from lib.editor import replace_batch_by_index
            result = replace_batch_by_index(self.doc, pairs_file=tmp_path)
            self.doc._build_index()
            return self._track_op(result, 'replace-batch-by-index')
        finally:
            os.unlink(tmp_path)

    def insert_paragraph(self, after=None, text=None, style='body', after_text=None):
        self._ensure_backup()
        if after is None and after_text is not None:
            after = self._resolve_by_text(after_text)
            if after is None:
                return {"error": f"未找到包含 '{after_text}' 的段落"}
        from lib.editor import insert_paragraph
        result = insert_paragraph(self.doc, after=after, text=text, style=style)
        self.doc._build_index()
        return self._track_op(result, 'insert-paragraph')

    def write_paragraphs(self, after=None, data=None, after_text=None):
        self._ensure_backup()
        if after is None and after_text is not None:
            after = self._resolve_by_text(after_text)
            if after is None:
                return {"error": f"未找到包含 '{after_text}' 的段落"}
        from lib.editor import write_paragraphs
        result = write_paragraphs(self.doc, after=after, data=data)
        self.doc._build_index()
        return self._track_op(result, 'write-paragraphs')

    def delete_paragraph(self, index=None, by_text=None):
        self._ensure_backup()
        from lib.editor import delete_paragraph
        if index is None and by_text is not None:
            index = self._resolve_by_text(by_text)
            if index is None:
                return {"error": f"未找到包含 '{by_text}' 的段落"}
        if index is None:
            return {"error": "请提供 index 或 by_text"}
        result = delete_paragraph(self.doc, paragraph=index)
        self.doc._build_index()
        return self._track_op(result, 'delete-paragraph')

    def move_paragraph(self, index=None, by_text=None, after=None, after_text=None):
        """原子移动段落到指定位置。失败时自动回滚，不会丢失数据。"""
        self._ensure_backup()
        from lib.editor import move_paragraph
        if index is None and by_text is not None:
            index = self._resolve_by_text(by_text)
            if index is None:
                return {"error": f"未找到包含 '{by_text}' 的源段落"}
        if index is None:
            return {"error": "请提供 index 或 by_text 指定源段落"}
        if after is None and after_text is not None:
            after = self._resolve_by_text(after_text)
            if after is None:
                return {"error": f"未找到包含 '{after_text}' 的锚定段落"}
        if after is None:
            return {"error": "请提供 after 或 after_text 指定目标位置"}
        if index == after:
            return {"error": "源段落和目标位置相同，无需移动"}
        result = move_paragraph(self.doc, paragraph=index, after=after)
        self.doc._build_index()
        return self._track_op(result, 'move-paragraph')

    def accept_revisions(self, start, end):
        self._ensure_backup()
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
        self.doc._build_index()
        from lib.detector import detect_revisions
        after = detect_revisions(self.doc)
        result = {"accepted": count, "revisions_remaining": after["summary"]["total_revisions"]}
        return self._track_op(result, 'accept-revisions')

    def detect_revisions(self):
        from lib.detector import detect_revisions
        return detect_revisions(self.doc)

    def set_format(self, style, paragraph=None, start=None, end=None, target=None, rules=None):
        self._ensure_backup()
        from lib.editor import set_format
        result = set_format(self.doc, style=style, paragraph=paragraph, start=start,
                         end=end, target=target, rules=rules)
        if "error" not in result:
            self.doc._build_index()
        return self._track_op(result, 'set-format')

    def replace_table(self, index=None, data=None, by_text=None):
        self._ensure_backup()
        from lib.editor import replace_table
        result = replace_table(self.doc, index=index, data=data, by_text=by_text)
        return self._track_op(result, 'replace-table')

    def insert_table(self, after=None, data=None, caption=None, three_line=False, after_text=None):
        self._ensure_backup()
        if after is None and after_text is not None:
            after = self._resolve_by_text(after_text)
            if after is None:
                return {"error": f"未找到包含 '{after_text}' 的段落"}
        from lib.editor import insert_table
        result = insert_table(self.doc, after=after, data=data,
                              caption=caption, three_line=three_line)
        self.doc._build_index()
        return self._track_op(result, 'insert-table')

    def set_table_border(self, index, three_line=False):
        from lib.editor import set_table_border
        result = set_table_border(self.doc, index=index, three_line=three_line)
        return self._track_op(result, 'set-table-border')

    def insert_image(self, after=None, image=None, width=None, caption=None, after_text=None):
        self._ensure_backup()
        if after is None and after_text is not None:
            after = self._resolve_by_text(after_text)
            if after is None:
                return {"error": f"未找到包含 '{after_text}' 的段落"}
        from lib.editor import insert_image
        result = insert_image(self.doc, after=after, image=image, width=width,
                              caption=caption)
        self.doc._build_index()
        return self._track_op(result, 'insert-image')

    def replace_image(self, image, caption=None, paragraph=None, media=None):
        from lib.editor import replace_image
        result = replace_image(self.doc, image=image, caption=caption,
                            paragraph=paragraph, media=media)
        return self._track_op(result, 'replace-image')

    def delete_comments(self):
        from lib.fixer import delete_comments
        result = delete_comments(self.doc)
        return self._track_op(result, 'delete-comments')

    # ==================== 高级方法 ====================

    def replace_all(self, mapping, scope=None):
        """增强版批量替换，支持 dict 格式和章节范围限定。

        Args:
            mapping: {"旧词": "新词", ...} 或 [{"old": "旧", "new": "新"}, ...]
            scope: None(全文档), "chapter:N"(第N章), "section:标题"(按标题)

        Returns:
            {"total_replacements": int, "details": [...], "scope": str}
        """
        self._ensure_backup()
        if isinstance(mapping, dict):
            pairs = [{"old": k, "new": v} for k, v in mapping.items()]
        else:
            pairs = mapping

        chapter = None
        section_title = None
        scope_desc = "全文档"

        if scope:
            if isinstance(scope, str):
                if scope.startswith("chapter:"):
                    chapter = int(scope.split(":")[1])
                    scope_desc = f"第{chapter}章"
                elif scope.startswith("section:"):
                    section_title = scope.split(":", 1)[1]
                    scope_desc = f"节 '{section_title}'"
            elif isinstance(scope, dict):
                chapter = scope.get("chapter")
                section_title = scope.get("section")
                if chapter:
                    scope_desc = f"第{chapter}章"
                elif section_title:
                    scope_desc = f"节 '{section_title}'"

        if section_title and not chapter:
            section_node = self.doc.find_section(title=section_title)
            if section_node is None:
                return {"error": f"未找到节 '{section_title}'"}
            para_range = section_node["para_range"]
        elif chapter:
            # 用标题匹配"第N章"，而非索引（因为索引不含非章节标题）
            section_node = self.doc.find_section(title=f"第{chapter}章")
            if section_node is None:
                return {"error": f"未找到第{chapter}章"}
            para_range = section_node["para_range"]
        else:
            para_range = None

        if para_range is not None or (section_title or chapter):
            # 手动限定范围替换
            total = 0
            details = []
            for pair in pairs:
                old, new = pair.get("old", ""), pair.get("new", "")
                count = 0
                for i in range(para_range[0], para_range[1] + 1):
                    para = self.doc.raw_paragraphs[i]
                    if old in para.text:
                        from lib.editor import _replace_in_paragraph
                        if _replace_in_paragraph(para, old, new):
                            count += 1
                            total += 1
                detail = {"old": old, "new": new, "replacements": count}
                if count == 0:
                    detail["warning"] = "未找到匹配文本"
                details.append(detail)
            self.doc._build_index()
            result = {"total_replacements": total, "details": details, "scope": scope_desc}
        else:
            from lib.editor import replace_batch
            result = replace_batch(self.doc, pairs=pairs, chapter=None)
            result["scope"] = scope_desc

        return self._track_op(result, 'replace-all')

    def rewrite_section(self, title, paragraphs, include_subsections=False):
        """原子性地重写整个章节的正文内容。

        Args:
            title: 章节标题（模糊匹配）
            paragraphs: [{"text": "...", "style": "body"}, ...]
            include_subsections: True=替换含子标题的全部内容; False=只替换正文段落

        Returns:
            {"section_title": str, "old_count": int, "new_count": int}
        """
        self._ensure_backup()
        section_node = self.doc.find_section(title=title)
        if section_node is None:
            return {"error": f"未找到节 '{title}'"}

        start, end = section_node["para_range"]
        # 收集要删除的段落索引（跳过标题行）
        indices_to_delete = []
        for i in range(start + 1, min(end + 1, len(self.doc.paragraphs))):
            p = self.doc.paragraphs[i]
            if not include_subsections and p["level"] is not None:
                continue  # 跳过子标题
            if p["text"].strip():
                indices_to_delete.append(i)

        # 从后往前删除（防偏移）
        for idx in reversed(indices_to_delete):
            from lib.editor import delete_paragraph
            delete_paragraph(self.doc, paragraph=idx)

        self.doc._build_index()

        # 重新定位标题段落（索引可能变化）
        new_title_idx = self.doc.find_paragraph_by_text(section_node["title"])

        # 插入新内容
        if paragraphs and new_title_idx is not None:
            from lib.editor import write_paragraphs
            write_paragraphs(self.doc, after=new_title_idx, data=paragraphs)
            self.doc._build_index()

        result = {
            "section_title": section_node["title"],
            "old_count": len(indices_to_delete),
            "new_count": len(paragraphs),
        }
        return self._track_op(result, 'rewrite-section')

    def rewrite_paragraphs(self, mapping):
        """按内容定位批量替换多个段落。

        Args:
            mapping: {"锚定文本子串": "新段落全文", ...}

        Returns:
            {"total_replaced": int, "details": [...]}
        """
        self._ensure_backup()
        details = []
        total = 0
        for anchor, new_text in mapping.items():
            idx = self._resolve_by_text(anchor)
            if idx is None:
                details.append({"anchor": anchor[:30], "status": "not_found"})
                continue
            from lib.editor import replace_text
            result = replace_text(self.doc, paragraph=idx, text=new_text)
            if "error" not in result:
                total += 1
                details.append({"anchor": anchor[:30], "paragraph": idx, "status": "replaced",
                               "preview": new_text[:80]})
            else:
                details.append({"anchor": anchor[:30], "status": "error", "error": result["error"]})

        self.doc._build_index()
        result = {"total_replaced": total, "details": details}
        return self._track_op(result, 'rewrite-paragraphs')

    # ==================== 格式修复 ====================

    def assign_styles(self, rules=None, preset=None):
        from lib.fixer import assign_styles
        result = assign_styles(self.doc, rules=rules, preset=preset)
        return self._track_op(result, 'assign-styles')

    def fix_format(self, rules=None, preset=None):
        from lib.fixer import fix_format
        result = fix_format(self.doc, rules=rules, preset=preset)
        return self._track_op(result, 'fix-format')

    def fix_page_setup(self, rules=None):
        from lib.fixer import fix_page_setup
        result = fix_page_setup(self.doc, rules=rules)
        return self._track_op(result, 'fix-page-setup')

    def apply_template(self, template_path):
        from lib.fixer import apply_template
        result = apply_template(self.doc, template_path=template_path)
        return self._track_op(result, 'apply-template')

    # ==================== 页面布局 ====================

    def set_page_setup(self, width=None, height=None,
                       margin_top=None, margin_bottom=None,
                       margin_left=None, margin_right=None):
        from lib.layout import set_page_setup
        result = set_page_setup(self.doc, width=width, height=height,
                             margin_top=margin_top, margin_bottom=margin_bottom,
                             margin_left=margin_left, margin_right=margin_right)
        return self._track_op(result, 'set-page-setup')

    def insert_page_break(self, after=None, after_text=None):
        if after is None and after_text is not None:
            after = self._resolve_by_text(after_text)
            if after is None:
                return {"error": f"未找到包含 '{after_text}' 的段落"}
        from lib.layout import insert_page_break
        result = insert_page_break(self.doc, after=after)
        self.doc._build_index()
        return self._track_op(result, 'insert-page-break')

    def set_header(self, text, font='宋体', size='9'):
        from lib.layout import set_header
        result = set_header(self.doc, text=text, font=font, size=size)
        return self._track_op(result, 'set-header')

    def set_footer(self, text=None, page_number=False, align='center', font='宋体', size='9'):
        from lib.layout import set_footer
        result = set_footer(self.doc, text=text, page_number=page_number,
                         align=align, font=font, size=size)
        return self._track_op(result, 'set-footer')

    def renumber_figures(self):
        from lib.layout import renumber_figures
        result = renumber_figures(self.doc)
        return self._track_op(result, 'renumber-figures')

    # ==================== 引用 ====================

    def list_citations(self):
        from lib.reference import list_citations
        return list_citations(self.doc)

    def list_references(self, verify=False):
        from lib.reference import list_references
        return list_references(self.doc, verify=verify)

    def renumber_references(self, output):
        from lib.reference import renumber_references
        result = renumber_references(self.doc, output=output)
        return self._track_op(result, 'renumber-references')

    def add_reference(self, text, position=None):
        from lib.reference import add_reference
        result = add_reference(self.doc, text=text, position=position)
        return self._track_op(result, 'add-reference')

    def remove_reference(self, number):
        from lib.reference import remove_reference
        result = remove_reference(self.doc, number=number)
        return self._track_op(result, 'remove-reference')

    # ==================== 公式 ====================

    def insert_formula(self, after=None, latex=None, number=None, after_text=None):
        self._ensure_backup()
        if after is None and after_text is not None:
            after = self._resolve_by_text(after_text)
            if after is None:
                return {"error": f"未找到包含 '{after_text}' 的段落"}
        if after is None:
            return {"error": "请提供 after 或 after_text"}
        from lib.formula import insert_formula
        result = insert_formula(self.doc, after_index=after, latex_str=latex, eq_number=number)
        self.doc._build_index()
        return self._track_op(result, 'insert-formula')

    def insert_formulas(self, formulas):
        from lib.formula import insert_formulas_batch
        result = insert_formulas_batch(self.doc, formulas=formulas)
        self.doc._build_index()
        return self._track_op(result, 'insert-formulas')

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

    # ==================== _guide ====================

    def _attach_guide(self, result, command):
        """在写操作结果中附加 _guide 提示（按需投递文档）。"""
        if isinstance(result, dict) and "error" in result:
            return result
        from lib.guide import get_guide, WRITE_COMMANDS
        from commands.common import STRUCTURE_CHANGE_COMMANDS
        ctx = {
            "command": command,
            "is_first_write": self._op_count == 0,
            "is_structure_change": command in STRUCTURE_CHANGE_COMMANDS,
        }
        hints = get_guide(ctx)
        if hints:
            result["_guide"] = hints
        return result

    def _track_op(self, result, command):
        """追踪写操作并附加 _guide。每个写方法返回前调用。"""
        if isinstance(result, dict) and "error" not in result:
            self._op_count += 1
            self._attach_guide(result, command)
        return result

    def _enrich_result(self, result):
        """为操作结果添加额外的反馈信息。"""
        if not isinstance(result, dict) or "error" in result:
            return result
        # 批量替换无匹配时附加 warning
        details = result.get("details", [])
        if details and all(d.get("replacements", d.get("status")) in (0, "not_found", "未找到匹配") for d in details):
            result["warning"] = "所有替换词均未找到匹配。请检查文本内容是否正确。"
        return result

    # ==================== 安全 ====================

    def _ensure_backup(self):
        """第一次破坏性操作前自动保存带时间戳的备份。"""
        if not self._auto_backup or self._backup_done:
            return
        import shutil
        from datetime import datetime
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.filepath}.{ts}.bak"
        shutil.copy2(self.filepath, backup_path)
        self._backup_done = True

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

    @property
    def raw_doc(self):
        """直接返回 python-docx Document 对象，用于底层 XML 操作。"""
        return self.doc.doc

    def find_text(self, query):
        """便捷方法：返回第一个匹配段落的文本，找不到返回 None。"""
        r = self.search(query)
        return r['results'][0]['text'] if r['results'] else None
