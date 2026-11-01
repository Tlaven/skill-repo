#!/usr/bin/env python3
"""run-n2-acceptance.py — list or run N2 acceptance commands from a manifest.

Safety: without a manifest, it only discovers and lists N2 acceptance lines;
it never executes commands extracted from docs. With --run, it executes only
commands explicitly listed in the manifest.

Discovery looks for `novelty=N2` in the N2 homes (`docs/architecture.*`,
`docs/modules/*`) and then the first `**验收**:` line between that marker and
the next `novelty=` marker (or end of file). `docs/core-analysis.*` (L4) is a
reading view, not an N2 home, so it is not scanned.

Modes:
  list/discovery : prints units and marks them 未复跑; --strict exits 1 if a
                   discovered N2 unit has no `**验收**` line.
  manifest list  : prints units and marks them 未复跑.
  --run          : executes manifest commands; exits 1 if any command fails.

--json writes the units (list mode) or results (--run) to the given path.

Manifest:
{
  "units": [
    {"id": "N2-1", "doc": "docs/modules/foo.md",
     "command": "pytest -q tests/test_foo.py", "cwd": "."}
  ]
}
"""

import argparse
import json
import os
import subprocess
import sys

from _doc_common import active_mask, iter_docs, read_lines, rel


def is_n2_home(rel_path):
    """N2 five-piece homes: L2 (cross-module) and module L3 (in-module).

    L4 `docs/core-analysis.*` is a reading view, not a home, so it is excluded.
    """
    return rel_path in ("docs/architecture.md", "docs/architecture.markdown") or rel_path.startswith("docs/modules/")


def discover(root):
    units = []
    for path in iter_docs(root):
        rel_path = rel(root, path)
        if not is_n2_home(rel_path):
            continue
        lines = read_lines(path)
        mask = active_mask(lines)
        for i, (line, in_fence) in enumerate(zip(lines, mask), 1):
            if in_fence or "novelty=N2" not in line:
                continue
            # 单元的边界 = 下一个 `novelty=` 标记(没有就扫到文件末)。
            # 不能只搜固定行数:模块模板把 novelty 写在文件头,`**验收**` 在几十行之后。
            end = len(lines)
            for k in range(i + 1, len(lines) + 1):
                if "novelty=" in lines[k - 1]:
                    end = k - 1
                    break
            acceptance = None
            for j in range(i, end + 1):
                if "**验收**" in lines[j - 1]:
                    acceptance = lines[j - 1].strip()
                    break
            units.append(
                {
                    "id": "{}:{}".format(rel(root, path), i),
                    "doc": rel(root, path),
                    "line": i,
                    "acceptance": acceptance,
                }
            )
    return units


def load_manifest(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    units = data.get("units", data) if isinstance(data, dict) else data
    if not isinstance(units, list):
        raise ValueError("manifest must be a list or {'units': [...]}")
    clean = []
    for idx, unit in enumerate(units, 1):
        if not isinstance(unit, dict):
            raise ValueError("unit #{} is not an object".format(idx))
        command = str(unit.get("command", "")).strip()
        if not command:
            raise ValueError("unit #{} has no command".format(idx))
        clean.append(
            {
                "id": str(unit.get("id") or "unit-{}".format(idx)),
                "doc": str(unit.get("doc", "")),
                "command": command,
                "cwd": str(unit.get("cwd", ".")),
            }
        )
    return clean


def run_unit(root, unit, timeout):
    cwd = os.path.join(root, unit["cwd"])
    try:
        proc = subprocess.run(
            unit["command"],
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "id": unit["id"],
            "command": unit["command"],
            "returncode": proc.returncode,
            "ok": proc.returncode == 0,
            "stdout": proc.stdout[-2000:],
            "stderr": proc.stderr[-2000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "id": unit["id"],
            "command": unit["command"],
            "returncode": None,
            "ok": False,
            "stdout": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "",
            "stderr": "TIMEOUT after {}s".format(timeout),
        }


def print_discovered(units):
    for unit in units:
        print(
            "  {id}  {acc}".format(
                **unit, acc=unit["acceptance"] or "(no **验收** line found)"
            )
        )


def print_manifest(units):
    for unit in units:
        print("  {id}  {command}".format(**unit))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="project root (default: .)")
    ap.add_argument("--manifest", help="JSON manifest of N2 units")
    ap.add_argument("--run", action="store_true", help="execute manifest commands")
    ap.add_argument("--timeout", type=int, default=300, help="per-command timeout seconds")
    ap.add_argument("--strict", action="store_true", help="exit 1 if a discovered N2 unit has no acceptance line")
    ap.add_argument("--json", help="write JSON report to this path")
    args = ap.parse_args()

    root = os.path.abspath(args.root)

    if not args.manifest:
        units = discover(root)
        if not units:
            print("[run-n2-acceptance] no N2 units discovered (no manifest, nothing run).")
            if args.json:
                with open(args.json, "w", encoding="utf-8") as f:
                    json.dump({"units": [], "executed": False, "status": "未复跑"}, f, ensure_ascii=False, indent=2)
            return 0
        print("[run-n2-acceptance] discovered {} N2 unit(s); 未复跑 (NOT executed).".format(len(units)))
        print_discovered(units)
        print("[run-n2-acceptance] provide --manifest and --run to execute explicit commands.")
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({"units": units, "executed": False, "status": "未复跑"}, f, ensure_ascii=False, indent=2)
        missing = [u for u in units if not u["acceptance"]]
        if args.strict and missing:
            print("[run-n2-acceptance] strict: {} N2 unit(s) have no **验收** line.".format(len(missing)))
            return 1
        return 0

    if not args.run:
        units = load_manifest(args.manifest)
        print("[run-n2-acceptance] {} unit(s) in manifest; 未复跑 (add --run).".format(len(units)))
        print_manifest(units)
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({"units": units, "executed": False, "status": "未复跑"}, f, ensure_ascii=False, indent=2)
        return 0

    units = load_manifest(args.manifest)
    results = [run_unit(root, unit, args.timeout) for unit in units]
    for result in results:
        print(
            "[{}] {}  {}".format("PASS" if result["ok"] else "FAIL", result["id"], result["command"])
        )
        if not result["ok"]:
            if result["stdout"].strip():
                print("  stdout: " + result["stdout"].strip().replace("\n", "\n          "))
            if result["stderr"].strip():
                print("  stderr: " + result["stderr"].strip().replace("\n", "\n          "))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"results": results, "executed": True}, f, ensure_ascii=False, indent=2)

    failed = sum(1 for result in results if not result["ok"])
    print("[run-n2-acceptance] {} passed, {} failed.".format(len(results) - failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
