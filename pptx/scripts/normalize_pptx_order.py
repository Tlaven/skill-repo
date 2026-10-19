#!/usr/bin/env python
"""normalize_pptx_order.py - fix known OOXML element-order issues in generated PPTX files.

pptxgenjs (4.0.1) writes `<p:notesMasterIdLst>` AFTER `<p:sldIdLst>` in
`ppt/presentation.xml`. Strict schema validation (scripts/office/validate.py,
the same XSD set used by OOXML-Validator) rejects that order; PowerPoint/WPS
open it anyway. This script moves the element to its schema-correct position
(right after `<p:sldMasterIdLst>`, before `<p:handoutMasterIdLst>`/`<p:sldIdLst>`).

【实测:tests/evidence/normalize_check.log — raw FAILED / normalized PASSED (pptxgenjs 4.0.1)】

Usage:
  python scripts/normalize_pptx_order.py in.pptx out.pptx
  python scripts/normalize_pptx_order.py inplace in.pptx   # rewrite the same file

Exit codes: 0 ok (moved or already correct); 2 input problem.
"""

import re
import shutil
import sys
import zipfile
from pathlib import Path

NOTES_RE = re.compile(rb"<p:notesMasterIdLst(?:\s*/>|>.*?</p:notesMasterIdLst>)", re.S)
MASTER_RE = re.compile(rb"<p:sldMasterIdLst(?:\s*/>|>.*?</p:sldMasterIdLst>)", re.S)
PRESENTATION = "ppt/presentation.xml"


def normalize_bytes(xml: bytes) -> tuple[bytes, str]:
    m = NOTES_RE.search(xml)
    if not m:
        return xml, "no notesMasterIdLst"
    block = m.group(0)
    rest = xml[: m.start()] + xml[m.end():]
    master = MASTER_RE.search(rest)
    if not master:
        return xml, "no sldMasterIdLst (left as-is)"
    if master.end() <= m.start() and m.start() - master.end() < 200 and block not in rest[: master.end()]:
        pass  # fallthrough; the move below is still correct/idempotent
    out = rest[: master.end()] + block + rest[master.end():]
    if out == xml:
        return xml, "already in schema order"
    return out, "moved notesMasterIdLst before sldIdLst"


def normalize_file(src: Path, dst: Path) -> str:
    with zipfile.ZipFile(src, "r") as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    status = "presentation.xml not found"
    fixed = []
    for info, data in items:
        if info.filename == PRESENTATION:
            data, status = normalize_bytes(data)
        fixed.append((info, data))
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in fixed:
            zout.writestr(info, data)
    shutil.move(str(tmp), str(dst))
    return status


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "inplace":
        src = Path(args[1])
        status = normalize_file(src, src)
        print(f"{src}: {status}")
        return 0
    if len(args) != 2:
        print(__doc__)
        return 2
    src, dst = Path(args[0]), Path(args[1])
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 2
    status = normalize_file(src, dst)
    print(f"{src} -> {dst}: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
