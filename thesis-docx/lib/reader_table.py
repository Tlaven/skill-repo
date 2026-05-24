"""表格读取 — 纯库函数"""
from lib.reader_loc import read_location

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def read_table(doc, index, deep=False):
    if index < 0 or index >= len(doc.tables):
        return {"error": f"表格索引 {index} 超出范围 (0-{len(doc.tables)-1})"}
    tbl = doc.tables[index]
    result = {
        "index": tbl["index"], "shape": f"{tbl['rows']}x{tbl['cols']}",
        "header": tbl["header"], "data": tbl["data"],
        "para_index_approx": tbl["para_index_approx"],
    }
    if deep:
        if index < len(doc.raw_tables):
            raw_tbl = doc.raw_tables[index]
            borders = extract_table_borders(raw_tbl)
            if borders:
                result["format"] = borders
            cell_fonts = extract_table_cell_fonts(raw_tbl)
            if cell_fonts:
                result["cell_styles"] = cell_fonts
        loc = read_location(doc, tbl["para_index_approx"])
        if "error" not in loc:
            result["section"] = loc.get("section_path", "")
        caption = None
        for offset in range(-3, 4):
            idx = tbl["para_index_approx"] + offset
            if 0 <= idx < len(doc.paragraphs):
                p = doc.get_para(idx)
                if p and p["style"] == "Caption":
                    caption = p["text"]
                    break
        result["caption"] = caption or "（未找到 Caption 标题）"
        ctx = []
        for offset in [-1, 0, 1]:
            idx = tbl["para_index_approx"] + offset
            if 0 <= idx < len(doc.paragraphs):
                p = doc.get_para(idx)
                if p and p["text"].strip():
                    ctx.append({"index": idx, "text": p["text"][:150], "style": p["style"]})
        if ctx:
            result["context_paragraphs"] = ctx
        result["_deep"] = True
    return result


def read_tables(doc):
    return {
        "total": len(doc.tables),
        "tables": [{
            "index": t["index"], "rows": t["rows"], "cols": t["cols"],
            "header": t["header"], "para_index_approx": t["para_index_approx"],
        } for t in doc.tables],
    }


def read_table_context(doc, index):
    if index < 0 or index >= len(doc.tables):
        return {"error": f"表格索引 {index} 超出范围 (0-{len(doc.tables)-1})"}

    tbl = doc.tables[index]
    tp = tbl["para_index_approx"]

    loc_result = read_location(doc, tp)
    section_path = loc_result.get("section_path", "") if "error" not in loc_result else ""

    caption_text = None
    for offset in range(-3, 4):
        idx = tp + offset
        if 0 <= idx < len(doc.paragraphs):
            p = doc.get_para(idx)
            if p and p["style"] == "Caption":
                caption_text = p["text"]
                break

    context_paras = []
    for offset in [-1, 0, 1]:
        idx = tp + offset
        if 0 <= idx < len(doc.paragraphs):
            p = doc.get_para(idx)
            if p and p["text"].strip():
                context_paras.append({"index": idx, "text": p["text"][:150], "style": p["style"]})

    return {
        "table_index": index,
        "shape": f"{tbl['rows']}x{tbl['cols']}",
        "header": tbl["header"],
        "data": tbl["data"],
        "section": section_path,
        "caption": caption_text or "（未找到 Caption 标题）",
        "context_paragraphs": context_paras,
        "para_index_approx": tp,
    }


def extract_table_borders(table):
    """提取 Word 表格的边框信息，判断是否为三线表。"""
    W = W_NS
    tblPr = table._tbl.find(f'{{{W}}}tblPr')
    if tblPr is None:
        return {"note": "无 tblPr"}

    tblStyle = tblPr.find(f'{{{W}}}tblStyle')
    style_name = tblStyle.get(f'{{{W}}}val') if tblStyle is not None else None

    borders = tblPr.find(f'{{{W}}}tblBorders')
    if borders is None:
        if style_name:
            return {"style": style_name, "note": "边框由表格样式控制（未在 tblPr 显式定义）"}
        return {"note": "无显式边框设置（默认无边框）"}

    result = {"style": style_name} if style_name else {}
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        elem = borders.find(f'{{{W}}}{side}')
        if elem is not None:
            val = elem.get(f'{{{W}}}val')
            sz = elem.get(f'{{{W}}}sz')
            if val and val != 'none':
                result[side] = {"style": val, "size": int(sz) if sz else 0}
            else:
                result[side] = {"style": "none"}

    has_top = result.get('top', {}).get('style') not in (None, 'none')
    has_bottom = result.get('bottom', {}).get('style') not in (None, 'none')
    has_insideH = result.get('insideH', {}).get('style') not in (None, 'none')
    no_left = result.get('left', {}).get('style') in (None, 'none')
    no_right = result.get('right', {}).get('style') in (None, 'none')
    no_insideV = result.get('insideV', {}).get('style') in (None, 'none')
    result['_is_three_line'] = has_top and has_bottom and has_insideH and no_left and no_right and no_insideV
    return result


def extract_table_cell_fonts(table):
    """提取表格各行的文字样式（字体/字号/加粗），判断内容样式是否统一。"""
    W = W_NS
    rows = table._tbl.findall(f'{{{W}}}tr')
    if not rows:
        return None

    sample_rows = []
    for ri in [0, 1]:
        if ri >= len(rows):
            continue
        row = rows[ri]
        cells = row.findall(f'{{{W}}}tc')
        cell_fonts = []
        for ci, cell in enumerate(cells):
            if ci >= 3:
                break
            paras = cell.findall(f'{{{W}}}p')
            for p in paras:
                runs = p.findall(f'{{{W}}}r')
                for r in runs[:1]:
                    rPr = r.find(f'{{{W}}}rPr')
                    font_info = {"font": None, "font_east": None, "size": None, "bold": None}
                    if rPr is not None:
                        rFonts = rPr.find(f'{{{W}}}rFonts')
                        if rFonts is not None:
                            font_info["font"] = rFonts.get(f'{{{W}}}ascii')
                            font_info["font_east"] = rFonts.get(f'{{{W}}}eastAsia')
                        sz = rPr.find(f'{{{W}}}sz')
                        if sz is not None:
                            val = sz.get(f'{{{W}}}val')
                            if val:
                                font_info["size"] = round(int(val) / 2, 1)
                        b = rPr.find(f'{{{W}}}b')
                        if b is not None:
                            b_val = b.get(f'{{{W}}}val')
                            font_info["bold"] = b_val != '0' if b_val else True
                    cell_fonts.append(font_info)
        sample_rows.append({"row": ri, "cells": cell_fonts})

    all_fonts = set()
    all_sizes = set()
    for row_data in sample_rows:
        for c in row_data["cells"]:
            if c["font"]: all_fonts.add(c["font"])
            if c["font_east"]: all_fonts.add(c["font_east"])
            if c["size"]: all_sizes.add(c["size"])

    uniform = len(all_fonts) <= 1 and len(all_sizes) <= 1
    common_font = list(all_fonts)[0] if len(all_fonts) == 1 else (all_fonts if all_fonts else "（全部继承表格样式）")
    common_size = list(all_sizes)[0] if len(all_sizes) == 1 else (all_sizes if all_sizes else "（全部继承表格样式）")
    return {
        "samples": sample_rows,
        "uniform": uniform,
        "common_font": common_font,
        "common_size": common_size,
        "note": "null = 继承表格样式，非直接设置" if uniform and not all_fonts else None,
    }
