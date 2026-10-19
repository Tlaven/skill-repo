#!/usr/bin/env python
"""qa_check.py - Executable QA assertions for PPTX delivery.

Runs a set of deterministic, source-tagged checks against a .pptx file and
prints a human-readable report (and optional JSON) usable as an acceptance gate.

Checks:
  C1 structure      slide count / media count / picture count; --expect-slides
  C2 placeholder    leftover placeholder text patterns (lorem, xxxx, click to edit...)
  C3 min-font-size  runs with explicit size below --min-font-pt (default 10)
  C4 color-hygiene  malformed hex colors in XML ('#' prefix or 8-digit srgbClr)
  C5 contrast       WCAG contrast of explicitly colored runs (4.5:1 / 3:1 large text)
  C6 image-aspect   displayed aspect vs native image aspect (deviation > --aspect-tol)
  C7 pdf-bounds     words crossing the page edge (requires --pdf; poppler pdftotext)
  C8 render-text    every paragraph survives into the rendered PDF text layer
                    (requires --pdf; catches content clipped away by overflow)
  C9 editable       slides likely non-editable (single full-page image, no text)
  I1 font-inventory font faces used (informational, for cross-platform delivery)

Usage:
  python qa_check.py deck.pptx [--json report.json] [--strict] [--pdf render/deck.pdf]
                      [--min-font-pt 10] [--aspect-tol 0.02] [--expect-slides N] [--min-coverage 0.8]

Exit codes: 0 ok (or issues without --strict); 1 issues with --strict; 2 runtime error.

Evidence tags used across this skill:
  【实测:path】  measured in this repo's test fixtures / logs
  【引用:url】   external standard or documentation
  【假设待测】   assumed, not yet verified
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import defusedxml.minidom
from pptx import Presentation
from pptx.enum.dml import MSO_FILL
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

# C2: placeholder / leftover text patterns. 【实测:tests/expected.json c1_placeholder / clean】
PLACEHOLDER_RE = re.compile(
    r"(lorem|ipsum|x{4,}|click to edit|单击此处|点击此处|待填|待补充|请输入|TBD|TODO)",
    re.IGNORECASE,
)

# C5: WCAG 2.1 SC 1.4.3 【引用:https://www.w3.org/TR/WCAG21/#contrast-minimum】
CONTRAST_NORMAL = 4.5
CONTRAST_LARGE = 3.0
LARGE_TEXT_PT = 18.0        # >= 18pt (~24px)
LARGE_TEXT_BOLD_PT = 14.0   # >= 14pt (~18.66px) and bold

MAX_ITEMS = 25  # cap per-check item lists in output


def _rgb_tuple(color_format):
    """Best-effort (r,g,b) extraction from a python-pptx ColorFormat."""
    if color_format is None:
        return None
    try:
        rgb = color_format.rgb
    except Exception:
        return None
    if rgb is None:
        return None
    try:
        t = tuple(rgb)
    except Exception:
        t = None
    if t is not None and len(t) == 3 and all(isinstance(v, int) for v in t):
        return (t[0] & 0xFF, t[1] & 0xFF, t[2] & 0xFF)
    s = str(rgb).strip()
    m = re.fullmatch(r"([0-9A-Fa-f]{6})", s)
    if m:
        v = m.group(1)
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    return None


def _fill_rgb(fill):
    """Solid-fill rgb, or None. Also returns reason when not a solid rgb fill."""
    try:
        ftype = fill.type
    except Exception:
        return None, "fill-type-unknown"
    if ftype is None:
        return None, "no-fill"
    if ftype == MSO_FILL.SOLID:
        rgb = _rgb_tuple(fill.fore_color)
        if rgb is None:
            return None, "solid-fill-non-rgb"
        return rgb, "solid-fill"
    return None, "non-solid-fill"


def _lum(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _contrast(rgb1, rgb2):
    l1, l2 = _lum(rgb1), _lum(rgb2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _slide_bg(prs, slide):
    """Slide background rgb with fallback to master; returns (rgb, reason)."""
    try:
        rgb, reason = _fill_rgb(slide.background.fill)
        if rgb is not None:
            return rgb, "slide-bg"
    except Exception:
        pass
    try:
        master = slide.slide_layout.slide_master
        rgb, reason = _fill_rgb(master.background.fill)
        if rgb is not None:
            return rgb, "master-bg"
    except Exception:
        pass
    return (255, 255, 255), "default-white-assumed"


def _under_text_bg(shape, filled_shapes):
    """Solid fill of the topmost filled shape whose bbox contains the text shape's center.

    Lets C5 resolve "text over a solid band" when the text frame itself has no fill.
    【实测:冷启动测试(2026-10-19)——白字叠浅色带被按页面底色误报 1.06:1】
    """
    try:
        cx = shape.left + shape.width / 2
        cy = shape.top + shape.height / 2
    except Exception:
        return None
    for left, top, width, height, rgb in reversed(filled_shapes):
        if left <= cx <= left + width and top <= cy <= top + height:
            return rgb
    return None


def iter_shapes(shapes):
    for shape in shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for sub in iter_shapes(shape.shapes):
                yield sub


def iter_text_runs(shape):
    """Yield (source_name, paragraph_text, run, cell_bg) for text frames and tables.

    cell_bg: solid rgb of the owning table cell (or None) so contrast checks can
    resolve the effective background of table text. 【实测:tests/out/reports/clean.json】
    """
    src = getattr(shape, "name", "?")
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                yield src, para.text, run, None
    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            for cell in row.cells:
                cell_bg = None
                try:
                    cell_bg, _ = _fill_rgb(cell.fill)
                except Exception:
                    cell_bg = None
                for para in cell.text_frame.paragraphs:
                    for run in para.runs:
                        yield src + "!table", para.text, run, cell_bg


def _short(text, n=40):
    text = (text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "\u2026"


def _norm_text(s):
    return re.sub(r"\s+", "", s or "")


class Report:
    def __init__(self):
        self.checks = {}
        self.unresolved = []  # contrast: runs we could not evaluate

    def add(self, check, severity, slide, detail):
        self.checks.setdefault(check, []).append(
            {"severity": severity, "slide": slide, "detail": detail}
        )

    def info(self, check, text):
        self.checks.setdefault(check, []).append(
            {"severity": "info", "slide": None, "detail": text}
        )

    def counts(self):
        err = flag = info = 0
        for items in self.checks.values():
            for it in items:
                if it["severity"] == "error":
                    err += 1
                elif it["severity"] == "flag":
                    flag += 1
                else:
                    info += 1
        return err, flag, info


def check_structure(prs, path, report, expect_slides):
    n = len(prs.slides)
    with zipfile.ZipFile(path) as zf:
        media = len([x for x in zf.namelist() if x.startswith("ppt/media/") and not x.endswith("/")])
    pics = 0
    for slide in prs.slides:
        for shape in iter_shapes(slide.shapes):
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                pics += 1
    report.info("C1-structure", f"slides={n}, media={media}, pictures={pics}")
    if expect_slides is not None and n != expect_slides:
        report.add("C1-structure", "flag", None, f"expected {expect_slides} slides, found {n}")


def check_placeholder(prs, report):
    hits = 0
    for idx, slide in enumerate(prs.slides, 1):
        for shape in iter_shapes(slide.shapes):
            if not (shape.has_text_frame or getattr(shape, "has_table", False)):
                continue
            text = shape.text_frame.text if shape.has_text_frame else ""
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    for cell in row.cells:
                        text += "\n" + cell.text_frame.text
            for m in PLACEHOLDER_RE.finditer(text):
                hits += 1
                if hits <= MAX_ITEMS:
                    report.add(
                        "C2-placeholder",
                        "flag",
                        idx,
                        f"matched {m.group(0)!r} in shape {shape.name!r}: {_short(text)!r}",
                    )
    if hits == 0:
        report.info("C2-placeholder", "no placeholder pattern found")


def check_min_font(prs, report, min_pt):
    hits = 0
    inherited = 0
    for idx, slide in enumerate(prs.slides, 1):
        for shape in iter_shapes(slide.shapes):
            for src, ptext, run, _cell_bg in iter_text_runs(shape):
                if not (run.text or "").strip():
                    continue
                size = run.font.size
                if size is None:
                    inherited += 1
                    continue
                pt = size.pt
                if pt < min_pt:
                    hits += 1
                    if hits <= MAX_ITEMS:
                        report.add(
                            "C3-min-font",
                            "flag",
                            idx,
                            f"{pt:.1f}pt (min {min_pt}pt) in {src!r}: {_short(run.text)!r}",
                        )
    report.info(
        "C3-min-font",
        f"below-min={hits}, inherited-size(not checked)={inherited}",
    )


def check_color_hygiene(path, report):
    bad = 0
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not re.match(r"^ppt/(slides|slideLayouts|slideMasters)/.*\.xml$", name):
                continue
            xml = zf.read(name).decode("utf-8", errors="replace")
            for m in re.finditer(r'<a:srgbClr val="([^"]*)"', xml):
                val = m.group(1)
                if "#" in val or not re.fullmatch(r"[0-9A-Fa-f]{6}", val):
                    bad += 1
                    if bad <= MAX_ITEMS:
                        report.add("C4-color-hygiene", "error", None, f"{name}: srgbClr val={val!r}")
            for m in re.finditer(r'<a:outerShdw[^>]*\bdist="(-\d+)"', xml):
                bad += 1
                if bad <= MAX_ITEMS:
                    report.add("C4-color-hygiene", "error", None, f"{name}: negative shadow dist={m.group(1)}")
    if bad == 0:
        report.info("C4-color-hygiene", "hex colors well-formed")


def check_contrast(prs, report):
    flagged = 0
    checked = 0
    for idx, slide in enumerate(prs.slides, 1):
        slide_bg, _ = _slide_bg(prs, slide)
        filled_shapes = []
        for shp in iter_shapes(slide.shapes):
            if shp.has_text_frame or getattr(shp, "has_table", False):
                continue
            try:
                frgb, _ = _fill_rgb(shp.fill)
            except Exception:
                frgb = None
            if frgb is None:
                continue
            try:
                filled_shapes.append((shp.left, shp.top, shp.width, shp.height, frgb))
            except Exception:
                pass
        for shape in iter_shapes(slide.shapes):
            shape_bg, bg_reason = None, "none"
            has_text = shape.has_text_frame or getattr(shape, "has_table", False)
            if has_text:
                try:
                    shape_bg, bg_reason = _fill_rgb(shape.fill)
                except Exception:
                    shape_bg, bg_reason = None, "fill-unreadable"
            for src, ptext, run, cell_bg in iter_text_runs(shape):
                if not (run.text or "").strip():
                    continue
                color = _rgb_tuple(run.font.color)
                if color is None:
                    continue  # inherited/theme color: not evaluable here
                if cell_bg is not None:
                    bg = cell_bg
                elif shape_bg is not None:
                    bg = shape_bg
                else:
                    bg = _under_text_bg(shape, filled_shapes)
                    if bg is None:
                        bg = slide_bg
                if bg is None:
                    if len(report.unresolved) < 200:
                        report.unresolved.append(
                            {"slide": idx, "shape": src, "reason": bg_reason}
                        )
                    continue
                checked += 1
                size = run.font.size
                pt = size.pt if size is not None else 0.0
                large = pt >= LARGE_TEXT_PT or (pt >= LARGE_TEXT_BOLD_PT and bool(run.font.bold))
                need = CONTRAST_LARGE if large else CONTRAST_NORMAL
                ratio = _contrast(color, bg)
                if ratio + 1e-9 < need:
                    flagged += 1
                    if flagged <= MAX_ITEMS:
                        report.add(
                            "C5-contrast",
                            "flag",
                            idx,
                            f"ratio {ratio:.2f} < {need} ({'large' if large else 'normal'} text) "
                            f"in {src!r}: {_short(run.text)!r} "
                            f"color=#{color[0]:02X}{color[1]:02X}{color[2]:02X} bg=#{bg[0]:02X}{bg[1]:02X}{bg[2]:02X}",
                        )
    report.info(
        "C5-contrast",
        f"checked={checked}, below-threshold={flagged}, unresolved(needs visual)={len(report.unresolved)}",
    )


def check_image_aspect(prs, report, tol):
    flagged = 0
    for idx, slide in enumerate(prs.slides, 1):
        for shape in iter_shapes(slide.shapes):
            if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                continue
            try:
                px_w, px_h = shape.image.size
                if px_w == 0 or px_h == 0:
                    continue
                cl = getattr(shape, "crop_left", 0.0) or 0.0
                cr = getattr(shape, "crop_right", 0.0) or 0.0
                ct = getattr(shape, "crop_top", 0.0) or 0.0
                cb = getattr(shape, "crop_bottom", 0.0) or 0.0
                eff_w = px_w * max(1e-6, 1.0 - cl - cr)
                eff_h = px_h * max(1e-6, 1.0 - ct - cb)
                native = eff_w / eff_h
                disp = Emu(shape.width).inches / Emu(shape.height).inches
                dev = abs(native - disp) / native
            except Exception as e:
                report.add("C6-image-aspect", "flag", idx, f"could not evaluate {shape.name!r}: {e}")
                continue
            if dev > tol:
                flagged += 1
                if flagged <= MAX_ITEMS:
                    report.add(
                        "C6-image-aspect",
                        "flag",
                        idx,
                        f"{shape.name!r}: displayed aspect {disp:.3f} vs native {native:.3f} "
                        f"(deviation {dev*100:.1f}% > {tol*100:.1f}%)",
                    )
    if flagged == 0:
        report.info("C6-image-aspect", "all pictures within aspect tolerance")


def check_pdf_overflow(pdf_path, report, tol_pt=1.0):
    exe = shutil.which("pdftotext")
    if not exe:
        report.add("C7-pdf-bounds", "flag", None, "pdftotext (poppler) not found on PATH")
        return
    proc = subprocess.run(
        [exe, "-bbox", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        report.add("C7-pdf-bounds", "flag", None, f"pdftotext failed: {proc.stderr.strip()[:200]}")
        return
    dom = defusedxml.minidom.parseString(proc.stdout)
    flagged = 0
    pages = dom.getElementsByTagName("page")
    for page_no, page in enumerate(pages, 1):
        try:
            w = float(page.getAttribute("width"))
            h = float(page.getAttribute("height"))
        except ValueError:
            continue
        for word in page.getElementsByTagName("word"):
            try:
                x0 = float(word.getAttribute("xMin"))
                y0 = float(word.getAttribute("yMin"))
                x1 = float(word.getAttribute("xMax"))
                y1 = float(word.getAttribute("yMax"))
            except ValueError:
                continue
            text = "".join(n.data for n in word.childNodes if n.nodeType == n.TEXT_NODE)
            if x0 < -tol_pt or y0 < -tol_pt or x1 > w + tol_pt or y1 > h + tol_pt:
                flagged += 1
                if flagged <= MAX_ITEMS:
                    report.add(
                        "C7-pdf-bounds",
                        "flag",
                        page_no,
                        f"word {text!r} outside page ({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f}) "
                        f"page {w:.1f}x{h:.1f}",
                    )
    if flagged == 0:
        report.info("C7-pdf-bounds", f"no words outside slide bounds across {len(pages)} page(s)")


def check_render_text(prs, pdf_path, report):
    """C8: every deck paragraph must survive into the rendered PDF text layer.

    Catches content clipped away by overflow: some exporters drop lines beyond the
    slide edge entirely, so a bounds check on the PDF sees nothing.
    【实测:tests/out/reports/c3_overflow.json — missing tail "导出时就丢内容"】
    """
    exe = shutil.which("pdftotext")
    if not exe:
        report.add("C8-render-text", "flag", None, "pdftotext (poppler) not found on PATH")
        return
    proc = subprocess.run(
        [exe, str(pdf_path), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        report.add("C8-render-text", "flag", None, f"pdftotext failed: {proc.stderr.strip()[:200]}")
        return
    pages = [_norm_text(p) for p in proc.stdout.split("\f")]
    if pages and pages[-1] == "":
        pages.pop()  # pdftotext emits a trailing form feed
    missing = 0
    seen = set()
    for idx, slide in enumerate(prs.slides, 1):
        page_text = pages[idx - 1] if idx - 1 < len(pages) else ""
        for shape in iter_shapes(slide.shapes):
            for src, ptext, _run, _bg in iter_text_runs(shape):
                t = _norm_text(ptext)
                if len(t) < 2 or (idx, t) in seen:
                    continue
                seen.add((idx, t))
                if t in page_text:
                    continue
                k = 0
                for kk in range(len(t), -1, -1):
                    if t[:kk] in page_text:
                        k = kk
                        break
                tail = t[k:]
                missing += 1
                if missing <= MAX_ITEMS:
                    if k == 0:
                        report.add(
                            "C8-render-text",
                            "flag",
                            idx,
                            f"paragraph entirely missing from PDF: {_short(t, 60)!r} (shape {src!r})",
                        )
                    else:
                        report.add(
                            "C8-render-text",
                            "flag",
                            idx,
                            f"missing last {len(tail)} char(s) {_short(tail, 30)!r} "
                            f"of paragraph in {src!r}",
                        )
    if missing == 0:
        report.info("C8-render-text", f"all paragraphs present in PDF text layer ({len(pages)} page(s))")


def check_editable(prs, report, min_coverage=0.8):
    """C9: flag slides that are likely non-editable (single full-page image, no text).

    AI pipelines sometimes export pre-rendered slide images; such decks look right but
    cannot be re-edited (they fail the "editable PPTX" delivery goal).
    【引用:https://github.com/orgs/marp-team/discussions/82】【引用:https://github.com/kdnsna/pptlint】
    覆盖率阈值 80%【假设待测】(可调:--min-coverage)。
    """
    flagged = 0
    slide_area = prs.slide_width * prs.slide_height
    for idx, slide in enumerate(prs.slides, 1):
        texts = []
        area_ratio = 0.0
        has_pic = False
        for shape in iter_shapes(slide.shapes):
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                has_pic = True
                try:
                    ratio = (shape.width * shape.height) / slide_area
                    area_ratio = max(area_ratio, ratio)
                except Exception:
                    pass
            if shape.has_text_frame:
                texts.append(shape.text_frame.text)
            if getattr(shape, "has_table", False):
                for row in shape.table.rows:
                    for cell in row.cells:
                        texts.append(cell.text_frame.text)
        if has_pic and area_ratio >= min_coverage and not any(t.strip() for t in texts):
            flagged += 1
            report.add(
                "C9-editable",
                "flag",
                idx,
                f"slide looks non-editable: a picture covers {area_ratio*100:.0f}% of the slide "
                f"and no text was found",
            )
    if flagged == 0:
        report.info("C9-editable", "no full-page-image-only slides")


def check_font_inventory(prs, report):
    faces = {}
    for slide in prs.slides:
        for shape in iter_shapes(slide.shapes):
            for src, ptext, run, _cell_bg in iter_text_runs(shape):
                name = run.font.name
                if name:
                    faces[name] = faces.get(name, 0) + 1
    if faces:
        summary = "; ".join(f"{k} x{v}" for k, v in sorted(faces.items(), key=lambda kv: -kv[1]))
        report.info("I1-font-inventory", summary)
    else:
        report.info("I1-font-inventory", "no explicit font faces (all inherited)")


def main():
    ap = argparse.ArgumentParser(description="Executable QA assertions for PPTX delivery")
    ap.add_argument("pptx", help="path to .pptx file")
    ap.add_argument("--json", dest="json_path", help="write machine-readable report")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any error/flag found")
    ap.add_argument("--pdf", help="rendered PDF of the same deck (enables C7/C8)")
    ap.add_argument("--min-font-pt", type=float, default=10.0)
    ap.add_argument("--aspect-tol", type=float, default=0.02)
    ap.add_argument("--expect-slides", type=int, default=None)
    ap.add_argument("--min-coverage", type=float, default=0.8,
                    help="C9: full-page-image coverage ratio that flags a slide (default 0.8)")
    args = ap.parse_args()

    path = Path(args.pptx)
    if not path.exists():
        print(f"error: {path} not found", file=sys.stderr)
        return 2

    prs = Presentation(str(path))
    report = Report()

    check_structure(prs, path, report, args.expect_slides)
    check_placeholder(prs, report)
    check_min_font(prs, report, args.min_font_pt)
    check_color_hygiene(path, report)
    check_contrast(prs, report)
    check_image_aspect(prs, report, args.aspect_tol)
    check_editable(prs, report, args.min_coverage)
    if args.pdf:
        check_pdf_overflow(args.pdf, report)
        check_render_text(prs, args.pdf, report)
    else:
        report.info("C7-pdf-bounds", "skipped (no --pdf given)")
        report.info("C8-render-text", "skipped (no --pdf given)")
    check_font_inventory(prs, report)

    err, flag, info = report.counts()
    print(f"== qa_check: {path.name} ==")
    for check in sorted(report.checks):
        items = report.checks[check]
        sev = {}
        for it in items:
            sev[it["severity"]] = sev.get(it["severity"], 0) + 1
        head = ", ".join(f"{k}={v}" for k, v in sorted(sev.items()))
        print(f"[{check}] {head}")
        for it in items:
            if it["severity"] == "info":
                print(f"    info: {it['detail']}")
        for it in items:
            if it["severity"] in ("error", "flag"):
                where = f"slide {it['slide']}: " if it["slide"] else ""
                print(f"    {it['severity'].upper()}: {where}{it['detail']}")
    print(f"summary: errors={err}, flags={flag}, info={info}")
    if report.unresolved:
        print(f"note: {len(report.unresolved)} run(s) skipped in C5 (needs visual): "
              + ", ".join(sorted({u['reason'] for u in report.unresolved})))

    if args.json_path:
        out = {
            "file": str(path),
            "summary": {"errors": err, "flags": flag, "info": info},
            "unresolved": report.unresolved,
            "checks": report.checks,
        }
        Path(args.json_path).write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"json: {args.json_path}")

    if args.strict and (err + flag) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
