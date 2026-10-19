#!/usr/bin/env python
"""Build c7_badcolor.pptx: clean.pptx with one hex color corrupted (val="#222222").

Deterministic injection so qa_check C4 (color hygiene) has its own negative control.
Run by tests/run_tests.py after make_controls.js.
"""
import re
import sys
import zipfile
from pathlib import Path

TESTS = Path(__file__).parent
SRC = TESTS / "out" / "clean.pptx"
DST = TESTS / "out" / "c7_badcolor.pptx"


def main() -> int:
    with zipfile.ZipFile(SRC) as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    hit = False
    out_items = []
    for info, data in items:
        if info.filename.startswith("ppt/slides/") and info.filename.endswith(".xml") and not hit:
            text = data.decode("utf-8")
            text, n = re.subn(
                r'(<a:srgbClr val=")([0-9A-Fa-f]{6})(")', r"\g<1>#\g<2>\g<3>", text, count=1
            )
            hit = bool(n)
            data = text.encode("utf-8")
        out_items.append((info, data))
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in out_items:
            zout.writestr(info, data)
    print(f"c7_badcolor.pptx written (corrupted={hit})")
    return 0 if hit else 1


if __name__ == "__main__":
    sys.exit(main())
