import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(name, *args, cwd):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ScriptTests(unittest.TestCase):
    def test_check_code_refs_red_then_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "a.md",
                "See `src/ok.py` and `src/missing.py`; also `/src/abs-missing.py`.\n"
                "Prose `读/写`, `py/js`, `N0/N1`; alternatives `.sh`, `CLAUDE.md`; "
                "pending `docs/architecture.md`; extensionless `scripts/tool`; "
                "pending dir `docs/scaffolds/`.\n"
                "<!-- `src/comment-missing.py` -->\n\n```\n`src/ignored.py`\n```\n",
            )
            write(root / "src" / "ok.py", "")
            write(root / "scripts" / "tool.sh", "")
            proc = run_script("check-code-refs.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("src/missing.py", proc.stdout)
            self.assertIn("src/abs-missing.py", proc.stdout)
            self.assertIn("[pending-doc]", proc.stdout)
            self.assertIn("docs/scaffolds", proc.stdout)
            self.assertNotIn("src/ignored.py", proc.stdout)
            self.assertNotIn("读/写", proc.stdout)
            self.assertNotIn("py/js", proc.stdout)
            self.assertNotIn("N0/N1", proc.stdout)
            self.assertNotIn("CLAUDE.md", proc.stdout)
            self.assertNotIn("src/comment-missing.py", proc.stdout)

            write(root / "src" / "missing.py", "")
            write(root / "src" / "abs-missing.py", "")
            proc = run_script("check-code-refs.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_cursor_l1_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / ".cursor" / "rules" / "project.mdc", "See `src/missing.py`.\n")
            proc = run_script("check-code-refs.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("src/missing.py", proc.stdout)

    def test_run_n2_acceptance_list_only_and_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "modules" / "a.md",
                "# A\n\nnovelty=N2\n\n- **验收**: python -c \"print(1)\"\n",
            )
            proc = run_script("run-n2-acceptance.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("NOT executed", proc.stdout)
            self.assertIn("未复跑", proc.stdout)

            proc = run_script("run-n2-acceptance.py", "--root", ".", "--json", "report.json", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["executed"])
            self.assertEqual(report["status"], "未复跑")

            write(root / "docs" / "modules" / "b.md", "# B\n\nnovelty=N2\n\nNo acceptance here.\n")
            write(root / "docs" / "modules" / "c.md", "# C\n\n<!-- novelty=N2\nNo acceptance; comment must be ignored. -->\n")
            proc = run_script("run-n2-acceptance.py", "--root", ".", cwd=root)
            self.assertNotIn("c.md", proc.stdout)
            proc = run_script("run-n2-acceptance.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("no **验收** line", proc.stdout)

            manifest = {
                "units": [
                    {"id": "pass", "doc": "docs/modules/a.md",
                     "command": '"{}" -c "print(1)"'.format(sys.executable)},
                    {"id": "fail", "doc": "docs/modules/a.md",
                     "command": '"{}" -c "import sys; sys.exit(3)"'.format(sys.executable)},
                ]
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            proc = run_script(
                "run-n2-acceptance.py", "--root", ".", "--manifest", "manifest.json", "--json", "manifest-report.json",
                cwd=root,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((root / "manifest-report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["executed"])
            self.assertEqual(report["status"], "未复跑")

            proc = run_script(
                "run-n2-acceptance.py", "--root", ".", "--manifest", "manifest.json", "--run",
                cwd=root,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[PASS] pass", proc.stdout)
            self.assertIn("[FAIL] fail", proc.stdout)

    def test_check_consistency_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "a.md", "- **Widget**: first definition\n")
            write(root / "docs" / "b.md", "- **Widget**: second definition\n")
            write(root / "docs" / "c.md", "Config `timeout: 30`.\n")
            write(root / "docs" / "d.md", "Config `timeout: 60`.\n")
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("Widget", proc.stdout)
            self.assertIn("timeout", proc.stdout)

    def test_check_consistency_clean_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "AGENTS.md",
                "- **历史只增不改**: ADR / reviews / git\n"
                "- **未来必须带状态**: planned / doing / done / dropped\n"
                "Prose localhost: 8080 and localhost: 8443 are not config keys.\n",
            )
            write(
                root / "docs" / "glossary.md",
                "| 术语 | 定义 |\n|---|---|\n| Widget | canonical |\n\n"
                "- **定义**: one sentence\n- **例子**: precise fixture\n",
            )
            write(root / "docs" / "a.md", "Prose localhost: 8080 and localhost: 8443.\n")
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("no duplicate definitions", proc.stdout)

    def test_check_consistency_unregistered_definition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "glossary.md", "| 术语 | 定义 |\n|---|---|\n| Widget | canonical |\n")
            write(root / "docs" / "a.md", "- **Gadget**: unregistered definition\n")
            write(root / "docs" / "b.md", "- **Widget**: duplicate definition\n")
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[unregistered-definition] Gadget", proc.stdout)
            self.assertIn("[duplicate-definition] Widget", proc.stdout)

    def test_check_code_refs_skips_records_identifiers_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "decisions" / "adr-001.md",
                "See `src/gone.py` and `adr-<NNN>-use-event-sourcing.markdown`.\n",
            )
            write(
                root / "docs" / "a.md",
                "Identifiers `父.h`, `邻.h`; placeholder `adr-<NNN>-use.markdown`; "
                "pending `docs/architecture.markdown`.\n",
            )
            proc = run_script("check-code-refs.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("src/gone.py", proc.stdout)
            self.assertNotIn("父.h", proc.stdout)
            self.assertNotIn("邻.h", proc.stdout)
            self.assertNotIn("<NNN>", proc.stdout)
            self.assertIn("[pending-doc]", proc.stdout)
            self.assertIn("docs/architecture.markdown", proc.stdout)

    def test_check_consistency_scope_and_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "decisions" / "adr-001.md", "- **Widget**: historical option name\n")
            write(
                root / "docs" / "mod.md",
                "# M\n\n## [为什么]\n\n- **WhyThing**: rationale bullet\n\n"
                "## [是什么]\n\n- **Gadget**: unregistered definition\n",
            )
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("Gadget", proc.stdout)
            self.assertNotIn("Widget", proc.stdout)
            self.assertNotIn("WhyThing", proc.stdout)

    def test_decisions_readme_template_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "decisions" / "README.md",
                (ROOT / "templates" / "decisions-readme.md").read_text(encoding="utf-8"),
            )
            write(
                root / "docs-templates" / "adr-template.md",
                (ROOT / "templates" / "adr-template.md").read_text(encoding="utf-8"),
            )
            write(
                root / "docs-templates" / "evolution-rules.md",
                (ROOT / "references" / "evolution-rules.md").read_text(encoding="utf-8"),
            )
            proc = run_script("check-code-refs.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_core_code_card_labels_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "core-code.md",
                "- **职责**: pick a slot\n"
                "- **前置不变量**: order is pending\n"
                "- **后置不变量**: capacity holds\n"
                "- **谁必须读它**: allocation modules\n",
            )
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_bom_heading_is_recognized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "a.md", "\ufeff## Section\n\nsome text\n")
            proc = run_script("lint-doc-structure.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("no-headings", proc.stdout)

    def test_lint_doc_structure_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paragraph = "\n".join("line {}".format(i) for i in range(25)) + "\n"
            write(root / "docs" / "a.md", paragraph)
            proc = run_script("lint-doc-structure.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("long-paragraph", proc.stdout)

            proc = run_script("lint-doc-structure.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
