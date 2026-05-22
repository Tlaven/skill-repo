---
name: thesis-docx
description: Chinese thesis .docx editing toolkit. Use to read, edit, format, or quality-check .docx files. Supports full-text reading with --deep mode, inline text replacement with format control, style assignment, template format import, reference management, formula insertion (OMML preserved), and comprehensive quality checks. Triggers: user asks to read/modify/check a .docx thesis; mentions 论文/毕业论文/学位论文; needs to insert images/tables/formulas; wants format check or style cleanup.
type: skill
---

# 论文 DocX 工具

`python cli.py <command> <file> [options]`，所有输出 JSON。详见 [CLI.md](CLI.md)。

## 陷阱（违反会丢数据）

1. **段落索引会漂移** — `insert`/`delete` 后索引全变。用 `--by-text "子串"` 代替。
2. **≥3 次 insert/delete 写脚本** — 不要多次调 CLI，在同一个 Python 进程内完成。
3. **FORMULA_X_X 不会自动清理** — 插入公式后手动 `replace-inline --old "FORMULA_3_1" --new ""`。

## 思维模型

**用户需求 → 拆成以下某一种原语 → 用对应命令。不要写脚本。**

| 原语 | 对应命令 |
|------|---------|
| 读内容 | `read-*` / `search` |
| 改文字 | `replace-text` / `replace-inline` |
| 增内容 | `insert-* --after-text` |
| 改格式 | `set-*` / `format-inline` / `assign-styles` |
| 检查 | `check-*` |
| 删 | `delete-paragraph` / `delete-comments` |

## 命令速查

| 我要做什么 | 命令 |
|-----------|------|
| 全文概况 | `read-full` |
| 某节完整内容+格式+图表 | `read-section --title "节名" --deep` |
| 段落在哪+附近元素 | `read-location --paragraph N` |
| 表格+边框+字体 | `read-table --index N --deep` |
| 公式位置+数学内容 | `read-formulas` |
| 搜索关键词 | `search --query "关键词"` |
| 样式定义 | `extract-rules` |
| 替换整段 | `replace-text --by-text "旧段" --text "新段"` |
| 段内改一个词 | `replace-inline --by-text "锚定段" --old "旧词" --new "新词"` |
| 改词+设格式 | `replace-inline --old X --new Y --bold --font 楷体` |
| 只改格式不改字 | `format-inline --target "子串" --bold` |
| 插入一段/多段 | `insert-paragraph` / `write-paragraphs` |
| 删除一段 | `delete-paragraph --by-text "要删的段"` |
| 插入图片/表格/公式 | `insert-image/table/formula --after-text "锚定"` |
| 套模板格式 | `apply-template --template "模板.docx" "论文.docx"` |
| 自动分配全部样式 | `assign-styles` |
| 全面检查 | `check-all` |
| 专项检查 | `check-placeholders` / `check-formula-references` / `check-style` |
| 对照模板检查 | `check-format --template "模板.docx"` |
| 新建论文 | `create "论文.docx" --preset gb-academic` 或 `--from-template` |
