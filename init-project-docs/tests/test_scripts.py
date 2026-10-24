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


    def test_adr_index_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "README.md", "# ADR\n\n<!-- adr-index:begin -->\n<!-- adr-index:end -->\n")
            write(d / "adr-001-a.md", "---\nstatus: accepted\n---\n\n# ADR-001: Use A\n\nbody\n")
            write(d / "adr-002-b.md", "---\nstatus: proposed\n---\n\n# ADR-002: Maybe B\n")
            write(d / "adr-003-c.md",
                  "---\nstatus: superseded\nsuperseded_by: ADR-001\n---\n\n# ADR-003: Old C\n")

            proc = run_script("adr-index.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("[adr-index-drift]", proc.stdout)

            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

            proc = run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("regenerated", proc.stdout)

            index = (d / "README.md").read_text(encoding="utf-8")
            self.assertIn("- ADR-001 · accepted · Use A", index)
            self.assertIn("- ADR-002 · proposed · Maybe B", index)
            self.assertNotIn("ADR-003", index)          # superseded never listed
            self.assertNotIn("<!-- adr-index:begin -->", index)   # banner normalized

            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("[adr-archive]", proc.stdout)  # warning only, not a failure

    def test_adr_index_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "adr-001-a.md", "---\nstatus: accepted\n---\n\n# ADR-001: A\n")
            write(d / "adr-001-b.md", "---\nstatus: accepted\n---\n\n# ADR-001: B\n")
            write(d / "adr-002-c.md", "---\nstatus: approved\n---\n\n# ADR-002: C\n")
            write(d / "adr-003-d.md", "---\nstatus: superseded\n---\n\n# ADR-003: D\n")
            write(d / "adr-004-e.md", "---\nstatus: accepted\nsuperseded_by: ADR-099\n---\n\n# ADR-004: E\n")
            write(d / "adr-005-f.md", "---\nstatus: accepted\n---\n\n# ADR-006: F\n")
            write(d / "adr-007-g.md", "# ADR-007: G\n\nno status\n")
            write(d / "README.md", "# ADR\n\n<!-- adr-index:begin -->\n<!-- adr-index:end -->\n")

            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[adr-id-duplicate] ADR-001", proc.stdout)
            self.assertIn("[adr-bad-status] docs/decisions/adr-002-c.md", proc.stdout)
            self.assertIn("[adr-superseded-no-target] docs/decisions/adr-003-d.md", proc.stdout)
            self.assertIn("[adr-relation-missing] docs/decisions/adr-004-e.md", proc.stdout)
            self.assertIn("[adr-name-mismatch] docs/decisions/adr-005-f.md", proc.stdout)
            self.assertIn("[adr-bad-status] docs/decisions/adr-007-g.md", proc.stdout)

    def test_adr_index_legacy_prose_status_and_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "adr-001-a.md", "# ADR-001: A\n\n## 状态\n\naccepted(修订)\n\n## 背景\n\nlegacy\n")
            write(d / "adr-002-b.md", "# ADR-002: B\n\n## 状态\n\nsuperseded by ADR-001\n")

            proc = run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("created", proc.stdout)
            index = (d / "README.md").read_text(encoding="utf-8")
            self.assertIn("- ADR-001 · accepted(修订) · A", index)
            self.assertNotIn("ADR-002", index)

            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


    def test_adr_citations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "README.md", "# ADR\n\n<!-- adr-index:begin -->\n<!-- adr-index:end -->\n")
            write(d / "adr-001-a.md", "---\nstatus: accepted\n---\n\n# ADR-001: A\n")
            write(d / "adr-002-b.md",
                  "---\nstatus: superseded\nsuperseded_by: ADR-001\n---\n\n# ADR-002: B\n")
            write(root / "AGENTS.md", "See ADR-001, ADR-002 and ADR-099.\n\n```\nADR-404\n```\n")

            run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[adr-cite-missing] AGENTS.md:1: ADR-099", proc.stdout)
            self.assertIn("[adr-cite-retired] AGENTS.md:1: ADR-002", proc.stdout)
            self.assertNotIn("ADR-404", proc.stdout)      # fenced block is not a citation

            write(root / "AGENTS.md", "See ADR-001.\n")
            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            write(root / "AGENTS.md", "See ADR-099.\n")
            proc = run_script("adr-index.py", "--root", ".", "--strict", "--no-citations", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_adr_legacy_format_tolerance(self):
        """Real projects: prose statuses, fullwidth colon, README.markdown, template ids."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "README.markdown", "# ADR\n\n<!-- adr-index:begin -->\n<!-- adr-index:end -->\n")
            write(d / "adr-000-template.md", "# ADR-000: template\n\n## 状态\n\nproposed\n")
            write(d / "adr-001-a.md",
                  "# ADR-001：全角冒号\n\n## 状态\n\naccepted(2026-10-15)\n")
            write(d / "adr-002-b.md",
                  "# ADR-002: B\n\n## 状态\n\n⚠️ accepted(已落地：`x.html` 照它改了)\n")
            write(d / "adr-003-c.md",
                  "# ADR-003: C\n\n## 状态\n\nsuperseded(被 adr-002 取代)\n")
            write(root / "AGENTS.md", "模板见 ADR-000。\n")

            run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for tag in ("adr-bad-status", "adr-heading-mismatch", "adr-superseded-no-target",
                        "adr-index-missing", "adr-cite-missing"):
                self.assertNotIn(tag, proc.stdout)
            self.assertIn("[adr-archive]", proc.stdout)     # superseded, still in the main dir

            write(d / "adr-004-d.md", "# ADR-004: D\n\n## 状态\n\n已定\n")
            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[adr-bad-status] docs/decisions/adr-004-d.md", proc.stdout)
            self.assertIn("'已定'", proc.stdout)

    def test_adr_long_warnings_collapse(self):
        body = "\n\n".join("段落 {}".format(i) for i in range(300))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "README.md", "# ADR\n\n<!-- adr-index:begin -->\n<!-- adr-index:end -->\n")
            for i in range(1, 6):
                write(d / "adr-00{}-x.md".format(i),
                      "---\nstatus: accepted\n---\n\n# ADR-00{}: X\n\n{}\n".format(i, body))
            run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual(proc.stdout.count("[adr-long]"), 1, proc.stdout)
            self.assertIn("5 of 5 records exceed 800 words", proc.stdout)

            proc = run_script("adr-index.py", "--root", ".", "--strict", "--max-words", "5000", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("[adr-long]", proc.stdout)

    def test_adr_ignore_warning(self):
        """archive/ is invisible to rg only when docs/decisions/.ignore says so."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "README.md", "# ADR\n\n<!-- adr-index:begin -->\n<!-- adr-index:end -->\n")
            write(d / "adr-001-a.md", "---\nstatus: accepted\n---\n\n# ADR-001: A\n")
            write(d / "archive" / "adr-000-old.md",
                  "---\nstatus: superseded\nsuperseded_by: ADR-001\n---\n\n# ADR-000: old\n")

            run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("[adr-no-ignore]", proc.stdout)

            write(d / ".ignore", "# rg: keep history out of keyword search\narchive/\n")
            proc = run_script("adr-index.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("[adr-no-ignore]", proc.stdout)

    def test_adr_immutable_append_only(self):
        def git(*args):
            return subprocess.run(
                ["git", "-C", str(root)] + list(args),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "docs" / "decisions"
            write(d / "README.md", "# ADR\n\n<!-- adr-index:begin -->\n<!-- adr-index:end -->\n")
            write(d / "adr-001-a.md",
                  "---\nstatus: accepted\n---\n\n# ADR-001: A\n\n## 选择\n\nUse A.\n")
            run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            git("init", "-q")
            git("add", "-A")
            git("-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init")

            proc = run_script("adr-index.py", "--root", ".", "--strict", "--immutable", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            write(d / "adr-001-a.md",
                  "---\nstatus: accepted\n---\n\n# ADR-001: A\n\n## 选择\n\nUse B.\n")
            proc = run_script("adr-index.py", "--root", ".", "--strict", "--immutable", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[adr-immutable] docs/decisions/adr-001-a.md", proc.stdout)

            write(d / "adr-001-a.md",
                  "---\nstatus: accepted\n---\n\n# ADR-001: A\n\n## 选择\n\nUse A.\n\n## 补充 1\n\nmore\n")
            proc = run_script("adr-index.py", "--root", ".", "--strict", "--immutable", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            write(d / "archive" / "adr-001-a.md",
                  "---\nstatus: superseded\nsuperseded_by: ADR-002\n---\n\n# ADR-001: A\n\n"
                  "> Superseded by ADR-002 on 2026-10-24 - replaced.\n\n"
                  "## 选择\n\nUse A.\n\n## 补充 1\n\nmore\n")
            (d / "adr-001-a.md").unlink()
            write(d / "adr-002-c.md", "---\nstatus: accepted\n---\n\n# ADR-002: C\n")
            run_script("adr-index.py", "--root", ".", "--write", cwd=root)
            proc = run_script("adr-index.py", "--root", ".", "--strict", "--immutable", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            (d / "archive" / "adr-001-a.md").unlink()
            proc = run_script("adr-index.py", "--root", ".", "--strict", "--immutable", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[adr-deleted] docs/decisions/adr-001-a.md", proc.stdout)


if __name__ == "__main__":
    unittest.main()
