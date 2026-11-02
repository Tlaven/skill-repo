#!/usr/bin/env python3
"""run-n2-acceptance.py — 发现 N2 单元，或执行 manifest 里的验收命令。

合同: docs 的 novelty=N2 + manifest -> 单元列表 / 执行结果；缺验收 / 空 N2 家 / 覆盖不足 1，执行失败 1。
边界: 只跑 manifest 显式命令；覆盖不足会报，但验收语义仍归复核。
"""

import argparse
import json
import os
import subprocess
import sys
from collections import Counter

from _doc_common import N2_L2_DOCS, active_mask, iter_docs, read_lines, rel


def is_n2_home(rel_path, text=""):
    """N2 家：L2，或承载五件套的模块 L3（以「危险实现清单」为标记）。

    模块里的 novelty=N2 是模块档位，不是规格位置；L4 是阅读视图，不算家。
    """
    if rel_path in N2_L2_DOCS:
        return True
    if rel_path.startswith("docs/modules/"):
        return "危险实现清单" in text
    return False


def _active_text(lines):
    mask = active_mask(lines)
    return "\n".join(line for line, inactive in zip(lines, mask) if not inactive)


def _has_n2_intent(rel_path, text):
    if rel_path.startswith("docs/modules/"):
        return "危险实现清单" in text
    if rel_path in N2_L2_DOCS:
        return "### N2:" in text or "危险实现清单" in text
    return False


def discover(root):
    units = []
    empty_homes = []
    for path in iter_docs(root):
        rel_path = rel(root, path)
        lines = read_lines(path)
        text = _active_text(lines)
        if not is_n2_home(rel_path, text):
            continue
        mask = active_mask(lines)
        found = False
        for i, (line, inactive) in enumerate(zip(lines, mask), 1):
            if inactive or "novelty=N2" not in line:
                continue
            found = True
            # 单元边界 = 下一个活动行里的 `novelty=`；跳过注释 / fenced code。
            end = len(lines)
            for k in range(i + 1, len(lines) + 1):
                if mask[k - 1]:
                    continue
                if "novelty=" in lines[k - 1]:
                    end = k - 1
                    break
            acceptance = None
            for j in range(i, end + 1):
                if mask[j - 1]:
                    continue
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
        if not found and _has_n2_intent(rel_path, text):
            empty_homes.append(rel_path)
    return units, empty_homes


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


def coverage_gaps(discovered, manifest_units):
    """按 doc 比较“文档里发现的单元数”与“manifest 列出的单元数”。"""
    need = Counter(unit["doc"] for unit in discovered)
    have = Counter(unit["doc"] for unit in manifest_units)
    gaps = []
    for doc, count in sorted(need.items()):
        if have.get(doc, 0) < count:
            gaps.append({"doc": doc, "discovered": count, "manifest": have.get(doc, 0)})
    return gaps


def print_coverage(gaps, empty_homes):
    for home in empty_homes:
        print("[n2-home-without-marker] {}: N2 家但没找到 novelty=N2".format(home))
    for gap in gaps:
        print(
            "[coverage] {}: 文档 N2 单元 {} 个，manifest 仅 {} 个".format(
                gap["doc"], gap["discovered"], gap["manifest"]
            )
        )


def run_unit(root, unit, timeout):
    cwd = os.path.abspath(os.path.join(root, unit["cwd"]))
    root_n = os.path.normcase(root)
    cwd_n = os.path.normcase(cwd)
    if cwd_n != root_n and not cwd_n.startswith(root_n + os.sep):
        return {
            "id": unit["id"],
            "command": unit["command"],
            "returncode": None,
            "ok": False,
            "stdout": "",
            "stderr": "cwd 越出项目根: {}".format(unit["cwd"]),
        }
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
    ap.add_argument(
        "--strict", action="store_true",
        help="exit 1 if a discovered N2 unit has no acceptance line, or manifest coverage is incomplete",
    )
    ap.add_argument("--json", help="write JSON report to this path")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    manifest_path = args.manifest
    if manifest_path and not os.path.isabs(manifest_path):
        manifest_path = os.path.join(root, manifest_path)

    if not args.manifest:
        units, empty_homes = discover(root)
        print_coverage([], empty_homes)
        if not units:
            print("[run-n2-acceptance] no N2 units discovered (no manifest, nothing run).")
            if args.json:
                with open(args.json, "w", encoding="utf-8") as f:
                    json.dump(
                        {"units": [], "empty_homes": empty_homes, "executed": False, "status": "未复跑"},
                        f, ensure_ascii=False, indent=2,
                    )
            if args.strict and empty_homes:
                print("[run-n2-acceptance] strict: N2 home(s) without novelty=N2.")
                return 1
            return 0
        print("[run-n2-acceptance] discovered {} N2 unit(s); 未复跑 (NOT executed).".format(len(units)))
        print_discovered(units)
        print("[run-n2-acceptance] provide --manifest and --run to execute explicit commands.")
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(
                    {"units": units, "empty_homes": empty_homes, "executed": False, "status": "未复跑"},
                    f, ensure_ascii=False, indent=2,
                )
        missing = [u for u in units if not u["acceptance"]]
        if args.strict and (missing or empty_homes):
            if missing:
                print("[run-n2-acceptance] strict: {} N2 unit(s) have no **验收** line.".format(len(missing)))
            return 1
        return 0

    discovered, empty_homes = discover(root)
    units = load_manifest(manifest_path)
    gaps = coverage_gaps(discovered, units)
    print_coverage(gaps, empty_homes)

    if not args.run:
        print("[run-n2-acceptance] {} unit(s) in manifest; 未复跑 (add --run).".format(len(units)))
        print_manifest(units)
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(
                    {"units": units, "coverage_gaps": gaps, "empty_homes": empty_homes,
                     "executed": False, "status": "未复跑"},
                    f, ensure_ascii=False, indent=2,
                )
        if args.strict and (gaps or empty_homes):
            return 1
        return 0

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
            json.dump(
                {"results": results, "coverage_gaps": gaps, "empty_homes": empty_homes, "executed": True},
                f, ensure_ascii=False, indent=2,
            )

    failed = sum(1 for result in results if not result["ok"])
    print("[run-n2-acceptance] {} passed, {} failed.".format(len(results) - failed, failed))
    return 1 if (failed or (args.strict and (gaps or empty_homes))) else 0


if __name__ == "__main__":
    sys.exit(main())
