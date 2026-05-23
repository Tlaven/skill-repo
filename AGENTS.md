# thesis-docx — AGENTS.md

## 项目性质

单项目仓库，仅含 `thesis-docx/`。中文论文 .docx 编辑工具集，同时是 OpenCode skill（定义见 `~/.claude/skills/thesis-docx/SKILL.md`）。

## 入口与架构

- **CLI 入口**：`python cli.py <command> <file> [options]`，所有输出 JSON
- **Python API**：`from api import ThesisEditor`，支持 context manager
- **分层**：`lib/`（纯函数，无 argparse）→ `commands/`（argparse 粘合）→ `cli.py`（路由）
- **依赖**：`pip install -r requirements.txt`（python-docx, latex2mathml）
- **Python**：本地 3.12.4，兼容 3.9+

## 关键陷阱（违反会丢数据）

1. **段落索引漂移** — `insert`/`delete` 后索引全变。始终用 `--by-text "子串"` / `--after-text "子串"` 代替 `--paragraph N`
2. **≥3 次 insert/delete 写脚本** — 不要多次调 CLI，在同一个 Python 进程内完成（或用 `api.py`）
3. **FORMULA_X_X 不会自动清理** — 插入公式后手动 `replace-inline --old "FORMULA_3_1" --delete`（PowerShell 下推荐用 `--delete` 替代 `--new ""`）
4. **批注删除清 4 个 XML** — `delete-comments` 已封装；手动需清理 `comments.xml` / `commentsExtended.xml` / `commentsIds.xml` / `commentsExtensible.xml`

## 通用选项

- `--backup` 修改前创建带时间戳备份
- `--by-text "子串"` 替代 `--paragraph N`（内容定位，防索引漂移）
- `--after-text "子串"` 替代 `--after N`（同上）
- `--data-file` 在 PowerShell 下替代 `--data '[...]'`（绕开双引号被吞问题）

## 测试

```bash
python -m pytest tests/
```

夹具在 `tests/conftest.py`：`create_test_doc()` 创建标准论文，`create_doc_with_headings()` 创建含多层标题的文档。

## 架构参考

```
lib/          — 纯函数（reader, editor, checker, fixer, styles, formula, reference, layout, creator, exporter, extractor, searcher, rules, core, utils）
commands/     — argparse 定义（read_cmds, edit_cmds, format_cmds, check_cmds, create_cmds, ref_cmds, export_cmds, extract_cmds）
scripts/      — 可复用独立脚本
test-case/    — 测试用 .docx + 图片
api.py        — ThesisEditor 编程接口
cli.py        — 命令行入口（路由 + 参数预处理）
```

## 预设

- `--preset gb-academic` 切换到 GB/T 7713.2-2022 标准字号（正文 10.5pt）
- 可用于 `create` / `assign-styles` / `fix-format`

## 文档

- `CLI.md` — 完整命令参考
- `lessons.md` — 操作经验手册（索引漂移、公式、格式等实战教训）
- `SKILL.md` — OpenCode skill 定义（思维模型 + 陷阱 + 命令速查）
