#!/usr/bin/env python
"""C5 叠层背景解析自测:验证"文字叠在实色色块上"时按色块取背景(不误报)。

- Case A:白字 + 深色矩形(文本中心落在矩形内)→ 期望 0 flag(按矩形底色 ≈13.8:1)
- Case B:同样的白字放在空白处(无衬底)→ 期望 ≥1 flag(按页面白底 1.06:1)

背景:2026-10-19 发现 filled_shapes 过滤把 autoshape 误排除(autoshape 恒有
text frame),导致"文字叠色块"仍按页面底色计算;本自测锁住该修复。

用法(仓库根目录):python tests/c5_selftest.py   → [PASS]/[FAIL],退出码 0/1
【实测:2026-10-19 首跑 PASS——Case A 0 flag / Case B 命中 1 flag】
"""
import json
import subprocess
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "out"


def make_deck(dest: Path, with_band: bool):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    if with_band:
        band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(2), Inches(8), Inches(2))
        band.fill.solid()
        band.fill.fore_color.rgb = RGBColor(0x1E, 0x27, 0x61)
        band.line.fill.background()
    box = s.shapes.add_textbox(Inches(1), Inches(2.4), Inches(6), Inches(1))
    tf = box.text_frame
    tf.text = "Hello band text"
    run = tf.paragraphs[0].runs[0]
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    run.font.name = "Microsoft YaHei"
    prs.save(str(dest))


def run_qa(pptx: Path, tag: str):
    rep = OUT / f"c5_selftest_{tag}.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "qa_check.py"), str(pptx), "--json", str(rep)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    data = json.loads(rep.read_text(encoding="utf-8"))
    items = data["checks"].get("C5-contrast", [])
    flags = [it for it in items if it["severity"] in ("error", "flag")]
    info = next((it["detail"] for it in items if it["severity"] == "info"), "")
    return flags, info


def main():
    OUT.mkdir(exist_ok=True)
    band = OUT / "c5_selftest_band.pptx"
    noband = OUT / "c5_selftest_noband.pptx"
    make_deck(band, True)
    make_deck(noband, False)

    f1, d1 = run_qa(band, "band")
    f2, d2 = run_qa(noband, "noband")
    print(f"Case A (白字叠深色带): flags={len(f1)}  [{d1}]")
    print(f"Case B (白字无衬底):   flags={len(f2)}  [{d2}]")
    ok = len(f1) == 0 and len(f2) >= 1
    print("[PASS] C5 叠层背景解析正确(有衬底不误报;无衬底照常报)" if ok
          else "[FAIL] C5 叠层背景解析异常")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
