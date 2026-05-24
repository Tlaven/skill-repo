# thesis-docx — AGENTS.md

## 入口

- **CLI**: `python cli.py <command> <file> [options]`，输出 JSON
- **Python API**: `from api import ThesisEditor`（context manager，但 `__exit__` 是 no-op—**必须调 `save()`**）
- **脚本**: `scripts/` — `sys.path.insert(0, '..')` 导入 `api.py`
- **参考**: `lessons.md`（操作经验）、`QUICK.md`（场景→命令）、`CLI.md`（全部命令）

## 架构

`lib/`（纯函数）→ `commands/`（argparse 注册 52 个命令）→ `cli.py`（路由）

`lib/core.py` → `ThesisDoc`：加载 `.docx`、构建索引（段落/章节树/图片/表格）、保存。reader 子模块（`reader_loc.py`/`reader_table.py`/`reader_media.py`/`reader_full.py`）全部通过 `reader.py` re-export。

## 保存：永远用 `save_zip()`

`save_zip()` 用 lxml 序列化 `document.xml` 回写 zip + 追加内存中图片 blob。`ThesisDoc.save()`（python-docx 原生）会丢失 OMML 公式和 insert_image 添加的图片。CLI、API、lib 里所有 save 都已用 `save_zip()`——不要手动调 `doc.save()`。

## 索引陷阱

- **漂移命令**（8 个）：`insert-paragraph`, `delete-paragraph`, `write-paragraphs`, `insert-formula[s]`, `insert-table`, `insert-image`, `insert-page-break`。执行后所有段落索引失效。
- **防漂移**：用 `--by-text "子串"` / `--after-text "子串"` 代替 `--paragraph N` / `--after N`。API 版用 `by_text=` / `after_text=`。
- **≥3 次修改写脚本**：在单进程内用 `ThesisEditor` API 完成，不要多次调 CLI。
- **`write-paragraphs` 从后往前插入** 防止漂移。
- **`FORMULA_X_X` 不自动清理**：插入公式后手动 `replace-inline --old "FORMULA_3_1" --delete`。
- **索引重建**：API 的 `insert_*`/`delete_paragraph`/`write_paragraphs` 自动调 `_build_index()`。CLI 每次重新打开文件。
- **`batch_fix.py` 展示表删除模式**：`body.remove(tbl_element)` 直接操作 XML，之后必须调 `_build_index()`。

## 样式系统

`lib/styles.py`：`STYLE_DEFS` 定义 h1-h3/body/caption/reference/header/footer。`classify_paragraph()` 按正则匹配（`^第[1-9]章`、`^摘\s*要$` 等）识别角色。`--preset gb-academic` 切换 GB/T 7713.2-2022 字号。

`check-*` 命令已移除，验证功能在 `read-* --verify` / `list-references --verify`。

## 测试 & CI

无测试文件（`__pycache__` 有残留 `.pyc`，源文件已删除）。无 CI/CD、无 linter、无 type checker。非 pip 包（无 `pyproject.toml`/`setup.py`）。`test-case/` 含 `thesis.docx` 作为脚本测试夹具。

## 环境细节

- **PowerShell 中文乱码**：`_fix_all_string_args` 自动 `latin-1→utf-8` 修复。`--data-file` 绕过双引号被吞。
- **`--find-file`**：CLI 自动用 `normalize_filename` 模糊匹配 `.docx` 文件。
- **`batch_fix.py` 含硬编码绝对路径**：`SRC = r"C:\Users\TL\.claude\skills\thesis-docx\test-case\thesis.docx"`——其他机器需修改。
- 所有 `.docx` 在 `.gitignore` 中。
