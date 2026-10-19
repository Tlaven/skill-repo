#!/usr/bin/env python
"""Build c8_bgshape.pptx: text over a filled shape that carries its own text frame.

Regression control for C5 background resolution. python-pptx (and PowerPoint)
rectangles always have a text frame, so a resolver that skips `has_text_frame`
shapes falls back to the slide background and misses the low contrast.
Run by tests/run_tests.py after make_badcolor.py.
"""
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

TESTS = Path(__file__).parent
DST = TESTS / "out" / "c8_bgshape.pptx"


def main() -> int:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    band = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    band.fill.solid()
    band.fill.fore_color.rgb = RGBColor(0x99, 0x99, 0x99)
    band.line.fill.background()

    title = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(9), Inches(0.9))
    trun = title.text_frame.paragraphs[0].add_run()
    trun.text = "背景解析回归负控"
    trun.font.size = Pt(20)
    trun.font.color.rgb = RGBColor(0x20, 0x20, 0x20)

    ghost = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(9), Inches(1.2))
    grun = ghost.text_frame.paragraphs[0].add_run()
    grun.text = "灰底灰字：应当被 C5 抓出（约 1.39:1）"
    grun.font.size = Pt(28)
    grun.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    prs.save(str(DST))
    print("c8_bgshape.pptx written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
