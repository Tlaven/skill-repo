import json
import os
import shutil
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

    def test_step2a_minimal_project_is_clean(self):
        """Step 2A 落盘即首跑必须是绿的:L1 模板 + methodology + task_plan + 空 .live."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "AGENTS.md", (ROOT / "templates" / "l1-memory.md").read_text(encoding="utf-8"))
            write(
                root / "docs-templates" / "methodology.md",
                (ROOT / "templates" / "methodology.md").read_text(encoding="utf-8"),
            )
            write(root / "task_plan.md", "# plan\n")
            write(root / "docs" / ".live", "")
            proc = run_script("check-code-refs.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("[missing-ref]", proc.stdout)

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
            write(
                root / "docs" / "architecture.md",
                "# L2\n\nnovelty=N2\n\nN2: §2 分配算法\n",
            )
            proc = run_script("run-n2-acceptance.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("NOT executed", proc.stdout)
            self.assertIn("未复跑", proc.stdout)
            self.assertIn("architecture.md", proc.stdout)  # L2 现在是 N2 家
            self.assertNotIn("core-code.md", proc.stdout)  # L4 是阅读视图,不扫

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
                "- **历史内容只增不改**: ADR / reviews / git\n"
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
            self.assertIn("no consistency warnings found", proc.stdout)

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

    def test_check_consistency_no_default_budget(self):
        """行数预算没有内置默认值:不传 --max-lines 就只警告不报超预算。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "AGENTS.md", "\n".join("line" for _ in range(260)) + "\n")
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("[over-budget]", proc.stdout)

            proc = run_script(
                "check-consistency.py", "--root", ".", "--strict", "--max-lines", "100",
                cwd=root,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[over-budget] AGENTS.md", proc.stdout)

    def test_check_consistency_no_budget_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "AGENTS.md", "\n".join("line" for _ in range(260)) + "\n")
            proc = run_script(
                "check-consistency.py", "--root", ".", "--strict", "--no-budget", cwd=root
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("[over-budget]", proc.stdout)

    def test_check_consistency_live_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "a.md", "clean\n")
            write(root / "docs" / "b.md", "\n".join("line" for _ in range(20)) + "\n")
            write(root / "docs" / ".live", "a.md\n")
            proc = run_script(
                "check-consistency.py", "--root", ".", "--strict", "--max-lines", "5",
                cwd=root,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("docs/b.md", proc.stdout)

            proc = run_script(
                "check-consistency.py", "--root", ".", "--strict", "--max-lines", "5",
                "--all-docs", cwd=root,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[over-budget] docs/b.md", proc.stdout)

    def test_check_consistency_live_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / ".live", "missing.md\n")
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[live-missing]", proc.stdout)
            self.assertIn("missing.md", proc.stdout)

    def test_check_consistency_duplicate_literal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "a.md", "Config `timeout: 30`.\n")
            write(root / "docs" / "b.md", "Again `timeout: 30`.\n")
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[duplicate-literal] timeout=30", proc.stdout)

    def test_check_consistency_duplicate_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "glossary.md",
                "| 术语 | 定义 |\n|---|---|\n| 剖面 | 参数 `profCoast` |\n",
            )
            write(root / "docs" / "a.md", "profCoast=.6\n")
            write(root / "docs" / "b.md", "profCoast=.35\n")
            proc = run_script("check-consistency.py", "--root", ".", "--strict", cwd=root)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[duplicate-alias] profCoast", proc.stdout)

    def test_check_consistency_ignore_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "glossary.md",
                "| 术语 | 定义 |\n|---|---|\n| 剖面 | 参数 `profCoast` |\n",
            )
            write(root / "docs" / "a.md", "profCoast=.6\n")
            write(root / "docs" / "b.md", "profCoast=.35\n")
            proc = run_script(
                "check-consistency.py", "--root", ".", "--strict",
                "--ignore-alias", "profCoast", cwd=root,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("[duplicate-alias]", proc.stdout)

    def test_check_consistency_term_demote(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "glossary.md", "| 术语 | 定义 |\n|---|---|\n| 槽 | container |\n")
            write(root / "docs" / "modules" / "theme.md", "槽 槽 槽 槽\n")
            proc = run_script(
                "check-consistency.py", "--root", ".", "--strict",
                "--glossary-locality", cwd=root,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("[term-demote] 槽", proc.stdout)

    def test_check_consistency_term_in_l2_is_not_demoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "glossary.md", "| 术语 | 定义 |\n|---|---|\n| 槽 | container |\n")
            write(root / "docs" / "modules" / "theme.md", "槽 槽 槽 槽\n")
            write(root / "docs" / "architecture.md", "槽 槽 槽 是架构级容器\n")
            proc = run_script(
                "check-consistency.py", "--root", ".", "--strict",
                "--glossary-locality", cwd=root,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("[term-demote] 槽", proc.stdout)

    def test_check_doc_refs_failure_semantics_only_n2(self):
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if not ps:
            self.skipTest("PowerShell not available")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "AGENTS.md", "# L1\n")
            write(
                root / "docs" / "modules" / "n1.md",
                "# N1\n\nnovelty=N1\n\n## [不变量]\n\n- x\n",
            )
            write(
                root / "docs" / "modules" / "n2.md",
                "# N2\n\nnovelty=N2\n\n### 危险实现清单\n\n"
                "| # | 最可能被写成的样子 | 为什么错 | 由谁挡住 |\n"
                "|---|---|---|---|\n| 1 | x | y | z |\n",
            )
            proc = subprocess.run(
                [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(SCRIPTS / "check-doc-refs.ps1")],
                cwd=str(root), capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            self.assertNotIn("n1.md", proc.stdout)
            self.assertIn("n2.md", proc.stdout)
            self.assertIn("module-missing-failure-semantics", proc.stdout)

    def test_check_doc_refs_n2_home_only(self):
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if not ps:
            self.skipTest("PowerShell not available")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "AGENTS.md", "# L1\n")
            # 高层只放定位 / 契约，不要求五件套与验收
            write(
                root / "docs" / "architecture.md",
                "# L2\n\nnovelty=N2\n\nN2: §2 分配算法\n",
            )
            write(root / "docs" / "design-contract.md", "# Contract\n\nN2: §3 重试语义\n")
            write(root / "docs" / "modules" / "fenced.md", "# Fenced\n\n```\nnovelty=N2\n```\n")
            # N2 五件套的家：缺验收应报(L2)
            write(
                root / "docs" / "architecture.md",
                "# Arch\n\nnovelty=N2\n\n"
                "### 危险实现清单\n\n"
                "| # | 最可能被写成的样子 | 为什么错 | 由谁挡住 |\n"
                "|---|---|---|---|\n| 1 | x | y | z |\n",
            )
            # 狗窝: L4 不再是家,写了也不该被扫
            write(root / "docs" / "core-code.md", "# Core\n\nnovelty=N2\n\nNo acceptance.\n")
            proc = subprocess.run(
                [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(SCRIPTS / "check-doc-refs.ps1")],
                cwd=str(root), capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            self.assertNotIn("design-contract.md", proc.stdout)
            self.assertNotIn("fenced.md", proc.stdout)
            self.assertNotIn("core-code.md", proc.stdout)
            self.assertIn("architecture.md", proc.stdout)
            self.assertIn("n2-missing-verification", proc.stdout)

    def test_check_doc_refs_provenance_line_is_flagged_ps1(self):
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if not ps:
            self.skipTest("PowerShell not available")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "AGENTS.md", "# L1\n")
            write(
                root / "docs" / "decisions" / "adr-001-x.md",
                "---\nstatus: accepted\n---\n\n# ADR-001: X\n",
            )
            write(
                root / "docs" / "modules" / "m.md",
                "> 出处：被拒方案见 docs/decisions/ADR-001\n"
                "因为 docs/decisions/ADR-001 规定，所以这样做。\n",
            )
            proc = subprocess.run(
                [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(SCRIPTS / "check-doc-refs.ps1")],
                cwd=str(root), capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            # `> 出处：…` 行已退役:它和普通引用一样是"现状文档引记录"
            self.assertIn("m.md:1", proc.stdout)
            self.assertIn("m.md:2", proc.stdout)

    def test_check_doc_refs_l1_entry_ref_ps1(self):
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if not ps:
            self.skipTest("PowerShell not available")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "architecture.md", "# L2\n")
            write(
                root / "AGENTS.md",
                "| 为什么这么定 / 被拒方案 | `docs/decisions/`(决策记录,按需) |\n"
                "加载顺序固定为 内核 → 主题 → UI(ADR-037)。\n"
                "模板见 `docs/decisions/adr-000-template.md`。\n",
            )
            proc = subprocess.run(
                [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(SCRIPTS / "check-doc-refs.ps1")],
                cwd=str(root), capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            # L1 活文档索引里的目录级行(含 docs/decisions/)允许;具体条目编号不允许;adr-000 是模板,放行
            self.assertNotIn("AGENTS.md:1", proc.stdout)
            self.assertIn("AGENTS.md:2", proc.stdout)
            self.assertIn("l1-entry-ref", proc.stdout)
            self.assertNotIn("AGENTS.md:3", proc.stdout)

    def test_l1_template_is_project_memory_only(self):
        text = (ROOT / "templates" / "l1-memory.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 70)
        self.assertNotIn("## 文档方法论", text)
        self.assertNotIn("### 铁律", text)
        self.assertIn("methodology.md", text)

        methodology = (ROOT / "templates" / "methodology.md").read_text(encoding="utf-8")
        self.assertIn("三段式", methodology)
        self.assertIn("三时间轴", methodology)
        self.assertIn("铁律", methodology)

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

    def test_templates_do_not_teach_reverse_adr_links(self):
        for name in ("adr-template.md", "decisions-readme.md"):
            text = (ROOT / "templates" / name).read_text(encoding="utf-8")
            self.assertNotIn("superseded_by", text, name)
            self.assertNotIn("> Superseded by", text, name)

    def test_glossary_template_has_no_record_reference(self):
        text = (ROOT / "templates" / "glossary.md").read_text(encoding="utf-8")
        self.assertNotIn("docs/decisions/", text)

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


    def test_check_consistency_dangling_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "contract.md",
                "| # | rule |\n|---|---|\n| **D-14** | first look |\n",
            )
            write(
                root / "docs" / "plan.md",
                "依据 D-14 与 D-17；记录见 ADR-031。\n",
            )
            proc = run_script("check-consistency.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("dangling-code", proc.stdout)
            self.assertIn("D-17", proc.stdout)
            self.assertNotIn("D-14:", proc.stdout)
            self.assertNotIn("ADR-031", proc.stdout)

    def test_check_consistency_code_defined_by_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(
                root / "docs" / "rules.md",
                "## E-1: 陈述退役\n\n## E-2: 方向型\n",
            )
            write(root / "docs" / "plan.md", "按 E-1 与 E-2 执行。\n")
            proc = run_script("check-consistency.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("dangling-code", proc.stdout)

    def test_check_consistency_no_downward_reference_check(self):
        # 索引（上层列下层）与"句子放太高"从文本上不可区分 → 不设机器判据。
        # 这条测试守的是"别把它加回来"：任何指向更深文档的行都不该产生 finding。
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "architecture.md", "细节 → `docs/modules/car.md`。\n")
            write(root / "docs" / "modules" / "car.md", "# 车\n")
            proc = run_script("check-consistency.py", "--root", ".", cwd=root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("no consistency warnings found", proc.stdout)

    def test_check_doc_refs_sh_n2_home_behavior(self):
        # 优先 Git for Windows 的 bash:Windows 上的 `bash` 常常是 WSL 的,
        # 它拿 Windows 路径会直接失败(空输出),那样的"绿"是假绿。
        git_bash = r"C:\Program Files\Git\bin\bash.exe"
        bash = git_bash if os.path.exists(git_bash) else shutil.which("bash")
        if not bash:
            self.skipTest("bash not available")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "docs" / "architecture.md", "novelty=N2\n\n这一段没有可跑验收。\n")
            write(root / "docs" / "core-code.md", "novelty=N2\n\nL4 是阅读视图,不该被扫。\n")
            write(root / "docs" / "modules" / "fenced.md", "# F\n\n```\nnovelty=N2\n```\n")
            proc = subprocess.run(
                [bash, str(SCRIPTS / "check-doc-refs.sh").replace("\\", "/")],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertIn("n2-missing-verification", proc.stdout)
            self.assertIn("docs/architecture.md", proc.stdout)
            self.assertNotIn("core-code.md", proc.stdout)
            self.assertNotIn("fenced.md", proc.stdout)




class SingleHomeTests(unittest.TestCase):
    """协议本体自己的规矩：E-1–E-7 只在 references/evolution-rules.md 写一次。

    2026-10-31 实测：'一处正文'这条被写成 6 遍，其中两处互相打脸
    （methodology 说"别处只导航"，evolution-rules 说"别处连指针都不写"）。
    下面这几个说法是 E-1–E-7 独有的；出现在 methodology 里 = 开始复述。
    """

    E_ONLY = ("三条出路", "记录寿命", "单一事实来源", "只在一个地方写", "唯一正文归属处")

    def test_e_rules_are_not_restated_in_methodology(self):
        text = (ROOT / "templates" / "methodology.md").read_text(encoding="utf-8")
        hits = [m for m in self.E_ONLY if m in text]
        self.assertEqual(hits, [], "methodology.md 复述了演进规则：{}".format(hits))

    def test_e_only_markers_still_have_a_home(self):
        text = (ROOT / "references" / "evolution-rules.md").read_text(encoding="utf-8")
        for marker in ("三条出路", "记录寿命", "单一事实来源"):
            self.assertIn(marker, text, "演进规则丢了自己的正文：{}".format(marker))


if __name__ == "__main__":
    unittest.main()
