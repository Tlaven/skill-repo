"""共享工具函数"""
from docx.enum.text import WD_ALIGN_PARAGRAPH


def emu_to_cm(emu):
    if emu is None:
        return None
    return round(emu / 914400 * 2.54, 2)


def cm_to_emu(cm):
    return int(cm * 914400 / 2.54)


def pt_to_half_pt(pt):
    if pt is None:
        return None
    return int(pt * 2)


ALIGNMENT_MAP = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
}
ALIGNMENT_REVERSE = {v: k for k, v in ALIGNMENT_MAP.items()}


def alignment_to_str(alignment):
    if alignment is None:
        return None
    return ALIGNMENT_MAP.get(alignment, str(alignment))


def str_to_alignment(s):
    if s is None:
        return None
    return ALIGNMENT_REVERSE.get(s)


def get_font_name(run, east_asian=False):
    if east_asian:
        rPr = run._element.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
        if rPr is not None:
            rFonts = rPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
            if rFonts is not None:
                return (rFonts.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia')
                        or rFonts.get('{http://schemas.openxmlformats.org/drawingml/2006/main}eastAsia'))
    return run.font.name


def get_run_font_info(run):
    font = run.font
    return {
        "font_name": font.name,
        "font_name_east": get_font_name(run, east_asian=True),
        "font_size": round(font.size.pt, 1) if font.size and font.size.pt else None,
        "bold": font.bold,
        "italic": font.italic,
        "color": str(font.color.rgb) if font.color and font.color.rgb else None,
        "underline": font.underline is True,
    }


def get_paragraph_format(para):
    fmt = para.paragraph_format
    pf = para._element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr')
    first_line_indent_cm = None
    if pf is not None:
        ind = pf.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ind')
        if ind is not None:
            first_line = ind.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}firstLine')
            if first_line:
                first_line_indent_cm = round(int(first_line) / 567.0, 2)
    line_spacing = None
    if pf is not None:
        spacing = pf.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing')
        if spacing is not None:
            line_val = spacing.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line')
            line_rule = spacing.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lineRule')
            if line_val:
                val = int(line_val)
                if line_rule == "exact" or line_rule == "atLeast":
                    line_spacing = round(val / 20.0, 1)
                else:
                    line_spacing = round(val / 240.0, 2)
    try:
        align_val = fmt.alignment
        align_str = alignment_to_str(align_val)
    except (ValueError, KeyError):
        align_str = None
    return {
        "alignment": align_str,
        "line_spacing": line_spacing if line_spacing is not None else (fmt.line_spacing if fmt.line_spacing else None),
        "first_line_indent_cm": first_line_indent_cm if first_line_indent_cm is not None else (emu_to_cm(fmt.first_line_indent) if fmt.first_line_indent else None),
        "space_before": fmt.space_before.pt if fmt.space_before and fmt.space_before.pt else None,
        "space_after": fmt.space_after.pt if fmt.space_after and fmt.space_after.pt else None,
    }


def get_heading_level(style_name):
    if not style_name:
        return None
    if style_name.startswith("Heading"):
        try:
            return int(style_name.replace("Heading", "").strip())
        except ValueError:
            return None
    if "标题" in style_name:
        try:
            return int(style_name.replace("标题", "").strip())
        except ValueError:
            return None
    CN_LEVEL_MAP = {"一级": 1, "二级": 2, "三级": 3, "四级": 4}
    if style_name in CN_LEVEL_MAP:
        return CN_LEVEL_MAP[style_name]
    return None


def is_heading(style_name):
    return get_heading_level(style_name) is not None


NSMAP = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def get_output_path(doc, output=None, backup=False):
    if output:
        return output
    if backup:
        import datetime
        import shutil
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = doc.filepath.replace('.docx', f'_backup_{timestamp}.docx')
        shutil.copy2(doc.filepath, backup_path)
    return doc.filepath


def normalize_filename(name):
    return ''.join(ch for ch in name.lower() if ch.isalnum() or '\u4e00' <= ch <= '\u9fff')


def find_toc_range(doc):
    from lib.styles import classify_paragraph
    toc_start = None
    toc_end = None
    for p in doc.paragraphs:
        text = p["text"].strip()
        if text in ("目录", "目　录") and toc_start is None:
            toc_start = p["index"]
        if toc_start is not None and toc_end is None:
            if p["level"] == 1 and p["index"] > toc_start + 3:
                toc_end = p["index"]
                break
            if p["index"] > toc_start + 3:
                role = classify_paragraph(text)
                if role == "chapter_title":
                    toc_end = p["index"]
                    break
    return toc_start, toc_end
