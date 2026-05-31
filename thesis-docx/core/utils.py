"""
core/utils.py — Pure utility functions extracted and cleaned from the original.

These have no side effects and are safe to keep in the elegant core.
"""

from docx.enum.text import WD_ALIGN_PARAGRAPH


W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_W = f'{{{W_NS}}}'


def emu_to_cm(emu):
    if emu is None:
        return None
    return round(emu / 914400 * 2.54, 2)


def cm_to_emu(cm):
    return int(cm * 914400 / 2.54)


def pt_to_emu(pt):
    return int(pt * 12700)


ALIGNMENT_MAP = {
    WD_ALIGN_PARAGRAPH.LEFT: "left",
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.JUSTIFY: "justify",
}
ALIGNMENT_REVERSE = {v: k for v, k in ALIGNMENT_MAP.items()}


def alignment_to_str(alignment):
    if alignment is None:
        return None
    return ALIGNMENT_MAP.get(alignment, str(alignment))


def str_to_alignment(s):
    if s is None:
        return None
    return ALIGNMENT_REVERSE.get(s)


def get_heading_level(style_name: str | None) -> int | None:
    """Extract heading level from style name. Supports English HeadingX and Chinese 标题X."""
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


def get_run_format(run):
    """Extract font properties from a single run. Returns dict or None."""
    rPr = run._element.find(f'{_W}rPr')
    if rPr is None:
        return None
    fmt = {}
    rFonts = rPr.find(f'{_W}rFonts')
    if rFonts is not None:
        fmt["font_name"] = (rFonts.get(f'{_W}ascii') or
                            rFonts.get(f'{_W}hAnsi') or
                            rFonts.get(f'{_W}eastAsia'))
    sz = rPr.find(f'{_W}sz')
    if sz is not None:
        val = sz.get(f'{_W}val')
        if val:
            fmt["font_size"] = round(int(val) / 2, 1)
    b = rPr.find(f'{_W}b')
    if b is not None:
        fmt["bold"] = b.get(f'{_W}val', 'true') != '0'
    i = rPr.find(f'{_W}i')
    if i is not None:
        rPr_i = i.get(f'{_W}val', 'true') != '0'
        fmt["italic"] = rPr_i
    return fmt if fmt else None


def get_representative_run_format(para):
    """
    Find the most representative run in a paragraph and extract its formatting.
    Favors runs with text and richer style properties.
    """
    if not para.runs:
        return {}
    best = None
    best_score = -1
    for run in para.runs:
        score = 0
        if run.text:
            score += 2
        rPr = run._element.find(f'{_W}rPr')
        if rPr is not None:
            score += len(rPr)
        if score > best_score:
            best_score = score
            best = run
    if best is None:
        return {}
    fmt = get_run_format(best) or {}
    return fmt


def get_paragraph_format(para):
    """Extract paragraph-level formatting (alignment, indents, spacing)."""
    fmt = para.paragraph_format
    pf = para._element.find(f'{_W}pPr')

    first_line_indent_cm = None
    if pf is not None:
        ind = pf.find(f'{_W}ind')
        if ind is not None:
            first_line = ind.get(f'{_W}firstLine')
            if first_line:
                first_line_indent_cm = round(int(first_line) / 567.0, 2)

    line_spacing = None
    line_spacing_rule = None
    if pf is not None:
        spacing = pf.find(f'{_W}spacing')
        if spacing is not None:
            line_val = spacing.get(f'{_W}line')
            line_rule = spacing.get(f'{_W}lineRule')
            if line_val:
                val = int(line_val)
                line_spacing_rule = line_rule or "multiple"
                if line_rule in ("exact", "atLeast"):
                    line_spacing = round(val / 20.0, 1)
                else:
                    line_spacing = round(val / 240.0, 2)

    try:
        align_val = fmt.alignment
        align_str = alignment_to_str(align_val)
    except (ValueError, KeyError):
        align_str = None

    space_before = fmt.space_before.pt if fmt.space_before and fmt.space_before.pt else None
    space_after = fmt.space_after.pt if fmt.space_after and fmt.space_after.pt else None

    run_fmt = get_representative_run_format(para)

    return {
        "alignment": align_str,
        "first_line_indent_cm": first_line_indent_cm if first_line_indent_cm is not None
            else (emu_to_cm(fmt.first_line_indent) if fmt.first_line_indent else None),
        "line_spacing": line_spacing,
        "line_spacing_rule": line_spacing_rule,
        "space_before": space_before,
        "space_after": space_after,
        **run_fmt,
    }
