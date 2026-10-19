#!/usr/bin/env python
"""C7 检测逻辑自测:人造一份"文字跨页缘"的 PDF,验证 C7 能红。

背景:本机渲染器(WPS)对越界文本一律裁切,deck 级夹具不可得
(见 acceptance-checklist.md §5);本自测不经过渲染器,直接构造跨缘 PDF,
单独验证 C7 的检测逻辑本身能命中。C8 同时不出声(空白 deck,无段落可评)。

构造注意:poppler 会丢弃"起点越出页缘"的字形(整字不可见),只保留跨缘字形的
真实包围盒——因此用宽字形(W,24pt≈22.7pt 宽)从 x≈588 起制造跨缘。
【实测:2026-10-19 首跑 PASS——'W' 命中,xMax=610.7 > 页宽 595(容差 1pt)】

用法(仓库根目录):python tests/c7_selftest.py   → [PASS]/[FAIL],退出码 0/1
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "out"


def make_oob_pdf(dest: Path):
    """最小未压缩 PDF:一处在页内的字 + 一处 x 明显超过页宽(595pt)的字。"""
    content = (
        b"BT /F1 24 Tf 72 700 Td (InsideOK) Tj ET\n"
        b"BT /F1 24 Tf 588 300 Td (WWWWWWWW) Tj ET\n"
    )
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1,
        xref_pos,
    )
    dest.write_bytes(bytes(out))


def main():
    OUT.mkdir(exist_ok=True)

    pdf = OUT / "c7_selftest.pdf"
    make_oob_pdf(pdf)

    from pptx import Presentation

    blank = OUT / "c7_selftest_blank.pptx"
    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6])
    prs.save(str(blank))

    report = OUT / "c7_selftest_report.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "qa_check.py"),
            str(blank),
            "--pdf", str(pdf),
            "--json", str(report),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    data = json.loads(report.read_text(encoding="utf-8"))
    hits = [it for it in data["checks"].get("C7-pdf-bounds", []) if it["severity"] in ("error", "flag")]
    print(f"qa_check exit={proc.returncode}, C7 hits={len(hits)}")
    for it in hits[:3]:
        print("  -", it["detail"])
    if hits:
        print("[PASS] C7 检测逻辑可红(人造越界 PDF 命中)")
        return 0
    print("[FAIL] C7 未命中——检测逻辑或环境异常,请人工检查")
    print(proc.stdout)
    return 1


if __name__ == "__main__":
    sys.exit(main())
