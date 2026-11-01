#!/usr/bin/env python
"""Run the pptx QA fixture suite: negative controls + end-to-end deck.

Steps per deck: build (node) -> render to PNG/PDF (WPS/PowerPoint COM on Windows)
-> qa_check.py -> compare against tests/expected.json.

Usage:
  python tests/run_tests.py [--which all|controls|e2e] [--no-build] [--no-render]

Prereqs: Node with global pptxgenjs + sharp; Python deps (requirements.txt);
a renderer (Windows: PowerPoint/WPS COM via scripts/render_slides.ps1);
poppler on PATH (pdftotext).

Outputs:
  tests/out/       build + render + JSON reports (gitignored)
  tests/evidence/  transcript + report copies (committed records)

Exit code 1 if any control misses its expected detection.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
OUT = TESTS / "out"
EVID = TESTS / "evidence"
QA = REPO / "scripts" / "qa_check.py"
RENDER = REPO / "scripts" / "render_slides.ps1"

CONTROL_DECKS = ["clean", "c1_placeholder", "c2_lowcontrast", "c3_overflow", "c4_stretched", "c5_tinyfont", "c6_flatslide", "c7_badcolor", "c8_bgshape"]
E2E_DECK = "e2e_deck"

TRANSCRIPT = []


def log(line=""):
    print(line)
    TRANSCRIPT.append(line)


def run(cmd, cwd=None, env=None, quiet=False):
    log("$ " + " ".join(str(c) for c in cmd))
    proc = subprocess.run(
        [str(c) for c in cmd], cwd=str(cwd) if cwd else None, env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.stdout and not quiet:
        log(proc.stdout.rstrip())
    if proc.stderr and proc.stderr.strip():
        log("[stderr] " + proc.stderr.strip())
    return proc


def node_env():
    env = os.environ.copy()
    root = subprocess.run(
        "npm root -g", shell=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()
    if root:
        env["NODE_PATH"] = root
    return env


def build(script):
    return run(["node", TESTS / script], cwd=TESTS, env=node_env())


def render(deck_path, out_dir):
    if sys.platform == "win32":
        return run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", RENDER, "-Pptx", deck_path, "-OutDir", out_dir, "-Pdf",
        ], quiet=True)
    # Non-Windows fallback: LibreOffice chain (not exercised by this repo's evidence).
    soffice = REPO / "scripts" / "office" / "soffice.py"
    pdf_dir = Path(out_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    p = run([sys.executable, soffice, "--headless", "--convert-to", "pdf", "--outdir", pdf_dir, deck_path], quiet=True)
    pdf = pdf_dir / (Path(deck_path).stem + ".pdf")
    p2 = run(["pdftoppm", "-jpeg", "-r", "150", pdf, str(pdf_dir / "slide")], quiet=True)
    return p2


def qa(deck_path, pdf_path, json_path, expect_slides=None):
    cmd = [sys.executable, QA, deck_path, "--pdf", pdf_path, "--json", json_path]
    if expect_slides:
        cmd += ["--expect-slides", str(expect_slides)]
    proc = run(cmd)
    data = json.loads(Path(json_path).read_text(encoding="utf-8")) if Path(json_path).exists() else {}
    return proc.returncode, data


def check_expectation(name, report, spec):
    """Return (ok, notes) for one deck against its expected.json spec."""
    notes = []
    checks = report.get("checks", {})
    summary = report.get("summary", {})
    fired = {
        cid for cid, items in checks.items()
        if any(it["severity"] in ("error", "flag") for it in items)
    }
    ok = True
    for cid in spec.get("must_include", []):
        if cid not in fired:
            ok = False
            notes.append(f"expected {cid} to fire, but it did not")
    if "max_flags" in spec and summary.get("flags", 0) > spec["max_flags"]:
        ok = False
        notes.append(f"flags={summary.get('flags')} > max_flags={spec['max_flags']} (false positives)")
    if "max_errors" in spec and summary.get("errors", 0) > spec["max_errors"]:
        ok = False
        notes.append(f"errors={summary.get('errors')} > max_errors={spec['max_errors']}")
    if not notes:
        notes.append(f"fired: {', '.join(sorted(fired)) or '(none)'} | flags={summary.get('flags')}, errors={summary.get('errors')}")
    return ok, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["all", "controls", "e2e"], default="all")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-evidence", action="store_true",
                    help="do not write tests/evidence/ (CI / eval runners that must leave the tree clean)")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    if not args.no_evidence:
        EVID.mkdir(parents=True, exist_ok=True)
        (EVID / "reports").mkdir(parents=True, exist_ok=True)

    expected = json.loads((TESTS / "expected.json").read_text(encoding="utf-8"))
    results = {}

    decks = []
    if args.which in ("all", "controls"):
        decks += CONTROL_DECKS
    if args.which in ("all", "e2e"):
        decks += [E2E_DECK]

    if not args.no_build:
        log("== build fixtures ==")
        if args.which in ("all", "controls"):
            build("make_controls.js")
            run([sys.executable, TESTS / "make_badcolor.py"])
            run([sys.executable, TESTS / "make_bgshape.py"])
        if args.which in ("all", "e2e"):
            build("make_e2e_deck.js")

    for deck in decks:
        deck_path = OUT / f"{deck}.pptx"
        render_dir = OUT / "render" / deck
        if not deck_path.exists():
            results[deck] = (False, [f"missing {deck_path}"])
            continue
        if not args.no_render:
            log(f"== render {deck} ==")
            render(deck_path, render_dir)
        pdf = render_dir / f"{deck}.pdf"
        json_path = OUT / "reports" / f"{deck}.json"
        log(f"== qa {deck} ==")
        qa(deck_path, pdf, json_path)
        report = json.loads(json_path.read_text(encoding="utf-8"))
        # copy report into evidence
        if not args.no_evidence:
            (EVID / "reports" / f"{deck}.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        spec = expected["decks"].get(deck)
        if spec is not None:
            results[deck] = check_expectation(deck, report, spec)
        else:
            summary = report.get("summary", {})
            ok = summary.get("errors", 0) == 0
            results[deck] = (ok, [f"flags={summary.get('flags')}, errors={summary.get('errors')}"])

    log("")
    log("== summary ==")
    all_ok = True
    for deck in decks:
        ok, notes = results.get(deck, (False, ["not run"]))
        all_ok = all_ok and ok
        log(f"[{'PASS' if ok else 'FAIL'}] {deck}: " + "; ".join(notes))

    if not args.no_evidence:
        (EVID / "run.log").write_text("\n".join(TRANSCRIPT) + "\n", encoding="utf-8")
        log(f"evidence: {EVID / 'run.log'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
