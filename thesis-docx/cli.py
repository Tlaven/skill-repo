"""CLI 命令行入口 — 瘦身版，只做路由 + 共用参数预处理"""
import sys
import os
import glob
import json
import argparse
from lib.utils import normalize_filename


def resolve_file(filepath):
    """文件路径模糊匹配，解决中文文件名特殊字符问题。"""
    if os.path.exists(filepath):
        return filepath
    basename = os.path.basename(filepath)
    directory = os.path.dirname(filepath) or '.'
    candidates = glob.glob(os.path.join(directory, '*.docx'))
    if not candidates:
        return filepath
    for c in candidates:
        if os.path.basename(c) == basename:
            return c
    norm_input = normalize_filename(basename)
    matches = []
    for c in candidates:
        norm_c = normalize_filename(os.path.basename(c))
        if norm_input in norm_c or norm_c in norm_input:
            matches.append(c)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        best = max(matches, key=lambda m: len(normalize_filename(os.path.basename(m))) if norm_input in normalize_filename(os.path.basename(m)) else 0)
        if norm_input in normalize_filename(os.path.basename(best)):
            return best
    return filepath


def preprocess_find_file(argv):
    """预处理 --find-file 参数。"""
    if '--find-file' not in argv:
        return argv
    idx = argv.index('--find-file')
    if idx + 1 >= len(argv):
        return argv
    pattern = argv[idx + 1]
    search_dirs = {'.', os.getcwd(), os.path.dirname(os.path.abspath(__file__))}
    for arg in argv:
        if arg.endswith('.docx') and os.path.isabs(arg):
            search_dirs.add(os.path.dirname(arg))
    candidates = []
    for directory in search_dirs:
        try:
            candidates.extend(glob.glob(os.path.join(directory, '*.docx')))
        except (OSError, PermissionError):
            pass
    norm_pattern = normalize_filename(pattern)
    matches = []
    for c in candidates:
        bn = os.path.basename(c)
        if pattern in bn or norm_pattern in normalize_filename(bn):
            matches.append(c)
    resolved = min(matches, key=len) if len(matches) >= 1 else pattern
    new_argv = argv[:idx] + argv[idx + 2:]
    file_idx = None
    for i in range(1, len(new_argv)):
        if not new_argv[i].startswith('-') and new_argv[i].endswith('.docx'):
            file_idx = i; break
    if file_idx is not None:
        new_argv[file_idx] = resolved
    else:
        new_argv.insert(2, resolved)
    return new_argv


def json_output(data, command, note=None):
    """统一 JSON 输出。"""
    is_error = "error" in data
    r = {"status": "error" if is_error else "success", "command": command}
    if is_error:
        r["error"] = data["error"]
    else:
        r["data"] = data
    if note:
        r["note"] = note
    encoded = json.dumps(r, ensure_ascii=False, indent=2).encode('utf-8')
    sys.stdout.buffer.write(encoded + b"\n")
    sys.stdout.buffer.flush()


def _fix_query_encoding(query):
    if not query: return query
    try:
        fixed = query.encode('latin-1').decode('utf-8')
        cjk_orig = sum(1 for c in query if '\u4e00' <= c <= '\u9fff')
        cjk_fixed = sum(1 for c in fixed if '\u4e00' <= c <= '\u9fff')
        return fixed if cjk_fixed > cjk_orig else query
    except (UnicodeDecodeError, UnicodeEncodeError):
        return query


def run_command(args):
    """路由到 lib/ 对应函数执行命令。"""
    import lib.reader as lib_read
    import lib.editor as lib_edit
    import lib.checker as lib_check
    import lib.fixer as lib_fixer
    import lib.reference as lib_ref
    import lib.formula as lib_formula
    import lib.layout as lib_layout
    import lib.searcher as lib_search
    import lib.exporter as lib_export
    import lib.extractor as lib_extract
    from lib.core import ThesisDoc

    if args.command == 'create':
        template = getattr(args, 'from_template', None)
        if template:
            from lib.creator import create_from_template
            return create_from_template(template, output=args.output or args.file)
        output_path = getattr(args, 'output', None) or args.file
        doc = ThesisDoc(output_path, create=True)
        from lib.creator import create_thesis
        return create_thesis(doc, output=args.output, preset=getattr(args, 'preset', None))

    args.file = resolve_file(args.file)
    if hasattr(args, 'file_new') and args.file_new:
        args.file_new = resolve_file(args.file_new)

    doc = ThesisDoc(args.file)

    _out = getattr(args, 'output', None)
    _bak = getattr(args, 'backup', False)

    cmd_map = {
        'read-structure': lambda: lib_read.read_structure(doc, format=getattr(args, 'format', 'tree')),
        'read-paragraph': lambda: lib_read.read_paragraph(doc, args.index, with_format=getattr(args, 'with_format', False), deep=getattr(args, 'deep', False)),
        'read-paragraphs': lambda: lib_read.read_paragraphs(doc, args.start, args.end, with_format=getattr(args, 'with_format', False)),
        'read-section': lambda: lib_read.read_section(doc, title=getattr(args, 'title', None), level=getattr(args, 'level', None), index=getattr(args, 'index', None), deep=getattr(args, 'deep', False)),
        'read-image': lambda: lib_read.read_image(doc, args.id, extract=getattr(args, 'extract', False), output_dir=getattr(args, 'output_dir', None), deep=getattr(args, 'deep', False)),
        'read-images': lambda: lib_read.read_images(doc),
        'read-table': lambda: lib_read.read_table(doc, args.index, deep=getattr(args, 'deep', False)),
        'read-tables': lambda: lib_read.read_tables(doc),
        'read-page-setup': lambda: lib_read.read_page_setup(doc),
        'read-stats': lambda: lib_read.read_stats(doc),
        'read-comments': lambda: lib_read.read_comments(doc),
        'read-formulas': lambda: lib_read.read_formulas(doc),
        'read-location': lambda: lib_read.read_location(doc, getattr(args, 'paragraph', 0)),
        'read-table-context': lambda: lib_read.read_table_context(doc, getattr(args, 'index', 0)),
        'read-full': lambda: lib_read.read_full(doc,
            section=getattr(args, 'section', None),
            paragraphs=getattr(args, 'range', None)),
        'search': lambda: lib_search.search(doc, query=getattr(args, 'query', None), query_file=getattr(args, 'query_file', None), regex=getattr(args, 'regex', False), chapter=getattr(args, 'chapter', None), section=getattr(args, 'section', None), context=getattr(args, 'context', 0), limit=getattr(args, 'limit', 20)),
        'search-by-style': lambda: lib_search.search_by_style(doc, args.style),
        'search-format': lambda: lib_search.search_format(doc, target=getattr(args, 'target', 'all')),
        'replace-text': lambda: lib_edit.replace_text(doc, args.paragraph, args.text, output=_out, backup=_bak),
        'replace-inline': lambda: lib_edit.replace_inline(doc, args.paragraph, args.old, args.new,
            output=_out, backup=_bak, bold=getattr(args, 'bold', None),
            font=getattr(args, 'font', None), font_east=getattr(args, 'font_east', None),
            size=getattr(args, 'size', None), color=getattr(args, 'color', None)),
        'format-inline': lambda: lib_edit.format_inline(doc, args.paragraph, args.target,
            output=_out, backup=_bak, bold=getattr(args, 'bold', None),
            font=getattr(args, 'font', None), font_east=getattr(args, 'font_east', None),
            size=getattr(args, 'size', None), color=getattr(args, 'color', None)),
        'replace-batch': lambda: lib_edit.replace_batch(doc, json.loads(args.pairs), chapter=getattr(args, 'chapter', None), output=_out, backup=_bak),
        'replace-batch-by-index': lambda: lib_edit.replace_batch_by_index(doc, args.pairs_file, output=_out, backup=_bak),
        'insert-paragraph': lambda: lib_edit.insert_paragraph(doc, args.after, args.text, style=getattr(args, 'style', 'body'), rules=getattr(args, 'rules', None), output=_out, backup=_bak),
        'write-paragraphs': lambda: lib_edit.write_paragraphs(doc, args.after, json.loads(args.data), output=_out, backup=_bak),
        'delete-paragraph': lambda: lib_edit.delete_paragraph(doc, args.paragraph, output=_out, backup=_bak),
        'set-format': lambda: lib_edit.set_format(doc, args.style, paragraph=getattr(args, 'paragraph', None), start=getattr(args, 'start', None), end=getattr(args, 'end', None), target=getattr(args, 'target', None), rules=getattr(args, 'rules', None), output=_out, backup=_bak),
        'replace-table': lambda: lib_edit.replace_table(doc, args.index, json.loads(args.data), output=_out, backup=_bak),
        'insert-table': lambda: lib_edit.insert_table(doc, args.after, json.loads(args.data), output=_out, backup=_bak),
        'insert-image': lambda: lib_edit.insert_image(doc, args.after, args.image, width=getattr(args, 'width', None), caption=getattr(args, 'caption', None), output=_out, backup=_bak),
        'replace-image': lambda: lib_edit.replace_image(doc, args.image, caption=getattr(args, 'caption', None), paragraph=getattr(args, 'paragraph', None), media=getattr(args, 'media', None), output=_out, backup=_bak),
        'delete-comments': lambda: lib_edit.delete_comments(doc, output=_out, backup=_bak),
        'list-citations': lambda: lib_ref.list_citations(doc),
        'list-references': lambda: lib_ref.list_references(doc),
        'check-references': lambda: lib_check.check_references(doc),
        'renumber-references': lambda: lib_ref.renumber_references(doc, args.output),
        'add-reference': lambda: lib_ref.add_reference(doc, args.text, position=getattr(args, 'position', None), output=_out, backup=_bak),
        'remove-reference': lambda: lib_ref.remove_reference(doc, args.number, output=_out, backup=_bak),
        'check-format': lambda: _check_format_with_template(doc, args, lib_check),
        'check-headings': lambda: lib_check.check_headings(doc, getattr(args, 'rules', None)),
        'check-body': lambda: lib_check.check_body(doc, getattr(args, 'rules', None)),
        'check-captions': lambda: lib_check.check_captions(doc, getattr(args, 'rules', None)),
        'check-page-setup': lambda: lib_check.check_page_setup(doc, getattr(args, 'rules', None)),
        'check-style': lambda: lib_check.check_style(doc),
        'check-paragraphs': lambda: lib_check.check_paragraphs(doc, threshold=getattr(args, 'threshold', 200), start=getattr(args, 'start', None), end=getattr(args, 'end', None)),
        'check-placeholders': lambda: lib_check.check_placeholders(doc),
        'check-figure-references': lambda: lib_check.check_figure_references(doc),
        'check-formula-references': lambda: lib_check.check_formula_references(doc),
        'check-all': lambda: lib_check.check_all(doc, rules=getattr(args, 'rules', None), threshold=getattr(args, 'threshold', 200)),
        'export-markdown': lambda: lib_export.export_markdown(doc, output=getattr(args, 'output', None)),
        'export-section': lambda: lib_export.export_section(doc, args.title, output=getattr(args, 'output', None)),
        'export-images': lambda: lib_export.export_images(doc, args.output_dir),
        'export-diff': lambda: lib_export.export_diff(doc, args.file_new, output=getattr(args, 'output', None)),
        'extract-text': lambda: lib_extract.extract_text(doc, start=getattr(args, 'start', None), end=getattr(args, 'end', None), section=getattr(args, 'section', None), output=getattr(args, 'output', None)),
        'extract-rules': lambda: lib_extract.extract_rules(doc, output=getattr(args, 'output', None)),
        'insert-formula': lambda: _cmd_insert_formula(doc, args),
        'insert-formulas': lambda: _cmd_insert_formulas(doc, args),
        'list-formulas': lambda: lib_formula.list_formulas(doc),
        'assign-styles': lambda: lib_fixer.assign_styles(doc, rules=getattr(args, 'rules', None), preset=getattr(args, 'preset', None), output=_out, backup=_bak),
        'fix-format': lambda: lib_fixer.fix_format(doc, rules=getattr(args, 'rules', None), preset=getattr(args, 'preset', None), output=_out, backup=_bak),
        'fix-page-setup': lambda: lib_fixer.fix_page_setup(doc, rules=getattr(args, 'rules', None), output=_out, backup=_bak),
        'set-page-setup': lambda: lib_layout.set_page_setup(doc, width=getattr(args, 'width', None), height=getattr(args, 'height', None), margin_top=getattr(args, 'margin_top', None), margin_bottom=getattr(args, 'margin_bottom', None), margin_left=getattr(args, 'margin_left', None), margin_right=getattr(args, 'margin_right', None), output=_out, backup=_bak),
        'insert-page-break': lambda: lib_layout.insert_page_break(doc, args.after, output=_out, backup=_bak),
        'set-header': lambda: lib_layout.set_header(doc, args.text, font=getattr(args, 'font', '宋体'), size=getattr(args, 'size', '9'), output=_out, backup=_bak),
        'set-footer': lambda: lib_layout.set_footer(doc, text=getattr(args, 'text', None), page_number=getattr(args, 'page_number', False), align=getattr(args, 'align', 'center'), font=getattr(args, 'font', '宋体'), size=getattr(args, 'size', '9'), output=_out, backup=_bak),
        'renumber-figures': lambda: lib_layout.renumber_figures(doc, output=_out, backup=_bak),
        'apply-template': lambda: lib_fixer.apply_template(doc, args.template, output=_out, backup=_bak),
    }

    if args.command not in cmd_map:
        return {"error": f"未知命令: {args.command}"}

    return cmd_map[args.command]()


def _cmd_insert_formula(doc, args):
    import zipfile
    from lxml import etree
    from lib.formula import insert_formula, M_NS
    from lib.utils import get_output_path
    output_path = get_output_path(doc, output=args.output, backup=args.backup)
    result = insert_formula(doc, args.after, args.latex, getattr(args, 'number', None))
    doc.save_zip(output_path)
    with zipfile.ZipFile(output_path, 'r') as z:
        content = z.read('word/document.xml')
        tree = etree.fromstring(content)
        saved_count = len(tree.findall(f'.//{{{M_NS}}}oMath'))
    result["output"] = output_path
    result["saved_formula_count"] = saved_count
    if saved_count == 0:
        result["warning"] = "保存后未检测到公式元素"
    return result


def _cmd_insert_formulas(doc, args):
    import zipfile
    import json
    from lxml import etree
    from lib.formula import insert_formulas_batch, M_NS
    from lib.utils import get_output_path
    with open(args.file_json, 'r', encoding='utf-8') as f:
        formulas = json.load(f)
    result = insert_formulas_batch(doc, formulas)
    output_path = get_output_path(doc, output=args.output, backup=args.backup)
    doc.save_zip(output_path)
    with zipfile.ZipFile(output_path, 'r') as z:
        content = z.read('word/document.xml')
        tree = etree.fromstring(content)
        saved_count = len(tree.findall(f'.//{{{M_NS}}}oMath'))
    result["output"] = output_path
    result["saved_formula_count"] = saved_count
    expected = result.get("total_inserted", 0)
    if saved_count < expected:
        result["warning"] = f"期望 {expected} 个公式，保存后检测到 {saved_count} 个"
    return result


def _check_format_with_template(doc, args, lib_check):
    """处理 check-format --template：提取模板规则后检查。"""
    tmpl_path = getattr(args, 'template', None)
    if tmpl_path:
        from lib.core import ThesisDoc as _TD
        from lib.extractor import extract_rules as _extract
        tmpl_doc = _TD(tmpl_path)
        tmpl_rules = _extract(tmpl_doc)
        # 转换为 check 用的 rules 格式
        rules = {
            "page": tmpl_rules.get("page", {}),
            "headings": {},
            "body": {},
            "caption": {},
            "reference": {},
        }
        for sname, sinfo in tmpl_rules.get("styles", {}).items():
            sname_lower = sname.lower()
            if "heading 1" in sname_lower:
                rules["headings"]["h1"] = sinfo
            elif "heading 2" in sname_lower:
                rules["headings"]["h2"] = sinfo
            elif "heading 3" in sname_lower:
                rules["headings"]["h3"] = sinfo
            elif "body text" in sname_lower or "normal" in sname_lower:
                rules["body"] = sinfo
            elif "caption" in sname_lower:
                rules["caption"] = sinfo
        return lib_check.check_format(doc, rules)
    return lib_check.check_format(doc, getattr(args, 'rules', None))


def main():
    import io
    if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    for i in range(1, len(sys.argv)):
        if '\\' in sys.argv[i] and not sys.argv[i].startswith('-'):
            sys.argv[i] = sys.argv[i].replace('\\', '/')

    sys.argv = preprocess_find_file(sys.argv)

    parser = argparse.ArgumentParser(description='Thesis Toolkit — 中文论文 .docx 工具集', prog='cli.py', allow_abbrev=False)
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    from commands import register_all
    register_all(subparsers)

    args = parser.parse_args()
    if not args.command:
        parser.print_help(); sys.exit(1)

    from commands.common import STRUCTURE_CHANGE_COMMANDS

    # --query-file
    if getattr(args, 'query_file', None):
        with open(args.query_file, 'r', encoding='utf-8') as f:
            args.query = f.read().strip()
        if not args.query:
            json_output({"error": "--query-file 文件内容为空"}, args.command); sys.exit(1)

    # --text-file
    text_file = getattr(args, 'text_file', None)
    if text_file:
        with open(text_file, 'r', encoding='utf-8') as f:
            args.text = f.read()
        if not args.text.strip():
            json_output({"error": "--text-file 文件内容为空"}, args.command); sys.exit(1)

    if args.command in ('replace-text', 'insert-paragraph') and not getattr(args, 'text', None):
        json_output({"error": "请提供 --text 或 --text-file"}, args.command); sys.exit(1)

    # --after-text
    if getattr(args, 'after_text', None) and args.command in ('insert-paragraph', 'insert-image', 'insert-table', 'insert-page-break'):
        from lib.core import ThesisDoc
        doc_for_lookup = ThesisDoc(args.file)
        idx = doc_for_lookup.find_paragraph_by_text(args.after_text)
        if idx is None:
            json_output({"error": f"未找到包含 \"{args.after_text}\" 的段落"}, args.command); sys.exit(1)
        args.after = idx

    if args.command in ('insert-paragraph', 'insert-image', 'insert-table', 'insert-page-break'):
        if not hasattr(args, 'after') or args.after is None:
            json_output({"error": "请提供 --after <索引> 或 --after-text <文本子串>"}, args.command); sys.exit(1)

    # --by-text（内容定位，替代 --paragraph）
    BY_TEXT_COMMANDS = ('replace-text', 'replace-inline', 'delete-paragraph', 'set-format')
    if getattr(args, 'by_text', None) and args.command in BY_TEXT_COMMANDS:
        from lib.core import ThesisDoc as _TD
        _tmp = _TD(args.file)
        idx = _tmp.find_paragraph_by_text(args.by_text)
        if idx is None:
            json_output({"error": f"未找到包含 \"{args.by_text}\" 的段落"}, args.command); sys.exit(1)
        args.paragraph = idx
    if args.command in BY_TEXT_COMMANDS:
        if not hasattr(args, 'paragraph') or args.paragraph is None:
            json_output({"error": "请提供 --paragraph <索引> 或 --by-text <文本子串>"}, args.command); sys.exit(1)

    if getattr(args, 'query', None):
        args.query = _fix_query_encoding(args.query)

    if getattr(args, 'command', None) == 'search' and not getattr(args, 'query', None):
        parser.parse_args(['search', '--help']); sys.exit(1)

    try:
        result = run_command(args)
        note = None
        if args.command in STRUCTURE_CHANGE_COMMANDS and "error" not in result:
            note = "段落索引已偏移，后续操作前请先对输出文件执行 read-structure 获取新索引"
        json_output(result, args.command, note=note)
    except FileNotFoundError as e:
        json_output({"error": str(e)}, args.command); sys.exit(1)
    except Exception as e:
        json_output({"error": f"{type(e).__name__}: {str(e)}"}, args.command); sys.exit(1)


if __name__ == '__main__':
    main()
