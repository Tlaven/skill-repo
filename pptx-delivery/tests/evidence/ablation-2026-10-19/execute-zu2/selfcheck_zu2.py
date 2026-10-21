#!/usr/bin/env python
"""selfcheck_zu2.py — 组2.md 第 3 节「交付前我会跑的 3 个检查」的可执行版。

检查 1  字号下限(自证 C3):所有 run ≥ 14pt;正文框 ≥ 18pt;表格 ≥ 16pt。
检查 2  安全区与越界(自证 C7):所有元素在 0.5in 安全区内;非 bg- 元素两两不重叠。
检查 3  色板与对比度(自证 C4/C5):全 deck 用色 ≤ 6;文字对比度 ≥ 4.5,大字 ≥ 3.0。

复用了 pptx-delivery 的 qa_check.py(C5-C8 同一套判定),不另写一套口径。

用法: python selfcheck_zu2.py deck.pptx [-v]
退出码: 0 全过 / 1 有失败
"""
import sys
import zipfile
import re
from pathlib import Path

SKILL = Path(r"C:\Users\TL\skills-repo\pptx-delivery\scripts")
sys.path.insert(0, str(SKILL))
import qa_check as Q  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

SAFE = 0.5          # in
MIN_RUN_PT = 14.0
MIN_BODY_PT = 18.0
MIN_TABLE_PT = 16.0
PALETTE_MAX = 6
EPS = 1e-6

PASS, FAIL = "PASS", "FAIL"


def inch(v):
    return Emu(v).inches


def check_fonts(prs):
    bad = []
    counts = {"run": 0, "body": 0, "table": 0}
    for idx, slide in enumerate(prs.slides, 1):
        for shp in Q.iter_shapes(slide.shapes):
            name = getattr(shp, "name", "") or ""
            is_table = getattr(shp, "has_table", False)
            if is_table:
                floor, kind = MIN_TABLE_PT, "table"
            elif name.startswith(("ftr-", "lbl-")):
                floor, kind = MIN_RUN_PT, "note"
            else:
                floor, kind = MIN_BODY_PT, "body"
            counts[kind if kind != "note" else "run"] = counts.get(kind if kind != "note" else "run", 0) + 1
            for src, ptext, run, _bg in Q.iter_text_runs(shp):
                if not (run.text or "").strip():
                    continue
                size = run.font.size
                if size is None:
                    bad.append((idx, src, "inherited size (not judged)", ""))
                    continue
                if size.pt + EPS < floor:
                    bad.append((idx, src, f"{size.pt:.1f}pt < {floor:.0f}pt", run.text[:20]))
    return bad


def check_bounds(prs):
    W = inch(prs.slide_width)
    H = inch(prs.slide_height)
    out_of_bounds, overlaps = [], []
    for idx, slide in enumerate(prs.slides, 1):
        items = []
        for shp in Q.iter_shapes(slide.shapes):
            try:
                x, y = inch(shp.left), inch(shp.top)
                w, h = inch(shp.width), inch(shp.height)
            except Exception:
                continue
            name = getattr(shp, "name", "") or ""
            if x < SAFE - EPS or y < SAFE - EPS or x + w > W - SAFE + EPS or y + h > H - SAFE + EPS:
                out_of_bounds.append((idx, name, round(x, 3), round(y, 3), round(x + w, 3), round(y + h, 3)))
            if not name.startswith("bg-"):
                items.append((name, x, y, w, h))
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                n1, x1, y1, w1, h1 = items[i]
                n2, x2, y2, w2, h2 = items[j]
                ox = min(x1 + w1, x2 + w2) - max(x1, x2)
                oy = min(y1 + h1, y2 + h2) - max(y1, y2)
                if ox > 1e-3 and oy > 1e-3:
                    overlaps.append((idx, n1, n2, round(ox * oy, 4)))
    return out_of_bounds, overlaps


def check_palette(path):
    used = set()
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not re.match(r"^ppt/slides/slide\d+\.xml$", name):
                continue
            xml = zf.read(name).decode("utf-8", "replace")
            used.update(v.upper() for v in re.findall(r'<a:srgbClr val="([0-9A-Fa-f]{6})"', xml))
    return sorted(used)


def check_contrast(prs):
    fails, checked = [], 0
    for idx, slide in enumerate(prs.slides, 1):
        slide_bg, _ = Q._slide_bg(prs, slide)
        filled = []
        for shp in Q.iter_shapes(slide.shapes):
            if getattr(shp, "has_table", False):
                continue
            try:
                frgb, _ = Q._fill_rgb(shp.fill)
            except Exception:
                frgb = None
            if frgb is not None:
                try:
                    filled.append((shp.left, shp.top, shp.width, shp.height, frgb))
                except Exception:
                    pass
        for shape in Q.iter_shapes(slide.shapes):
            shape_bg = None
            if shape.has_text_frame or getattr(shape, "has_table", False):
                try:
                    shape_bg, _ = Q._fill_rgb(shape.fill)
                except Exception:
                    shape_bg = None
            for src, ptext, run, cell_bg in Q.iter_text_runs(shape):
                if not (run.text or "").strip():
                    continue
                color = Q._rgb_tuple(run.font.color)
                if color is None:
                    continue
                bg = cell_bg or shape_bg or Q._under_text_bg(shape, filled) or slide_bg
                size = run.font.size.pt if run.font.size else 0.0
                large = size >= Q.LARGE_TEXT_PT or (size >= Q.LARGE_TEXT_BOLD_PT and bool(run.font.bold))
                need = Q.CONTRAST_LARGE if large else Q.CONTRAST_NORMAL
                ratio = Q._contrast(color, bg)
                checked += 1
                if ratio + 1e-9 < need:
                    fails.append((idx, src, round(ratio, 2), need, run.text[:16]))
    return checked, fails


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "deck.pptx")
    verbose = "-v" in sys.argv
    prs = Presentation(str(path))
    ok = True

    print(f"== selfcheck (组2 §3): {path.name} ==")

    bad_fonts = check_fonts(prs)
    print(f"[检查 1 字号下限] {PASS if not bad_fonts else FAIL}: 违规 {len(bad_fonts)}")
    for b in bad_fonts[:20]:
        print(f"    slide {b[0]} {b[1]}: {b[2]} {b[3]!r}")
    ok &= not bad_fonts

    oob, ov = check_bounds(prs)
    print(f"[检查 2 安全区/越界] {PASS if not (oob or ov) else FAIL}: 越界 {len(oob)}, 重叠对 {len(ov)}")
    for o in oob[:20]:
        print(f"    slide {o[0]} {o[1]} bbox=({o[2]},{o[3]})-({o[4]},{o[5]})")
    for o in ov[:20]:
        print(f"    slide {o[0]} overlap {o[1]} x {o[2]} = {o[3]} in²")
    ok &= not (oob or ov)

    palette = check_palette(path)
    checked, cfails = check_contrast(prs)
    print(f"[检查 3 色板/对比度] {PASS if (len(palette) <= PALETTE_MAX and not cfails) else FAIL}: "
          f"色板 {len(palette)} 色 {palette}, 对比度检查 {checked} run, 不达标 {len(cfails)}")
    for c in cfails[:20]:
        print(f"    slide {c[0]} {c[1]}: {c[2]} < {c[3]} {c[4]!r}")
    ok &= len(palette) <= PALETTE_MAX and not cfails

    print("== 结论:", "三条全过,可导出并签字 ==" if ok else "未通过,退回修改 ==")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
