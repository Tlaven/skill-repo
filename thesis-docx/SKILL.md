---
name: thesis-docx
description: Chinese thesis .docx editing toolkit. Use to read, edit, format, or verify .docx files through CLI commands. Supports full-text reading with --deep mode, inline text replacement with format control, style assignment, template format import, reference management, formula insertion (OMML preserved), and reading with --verify for anomaly detection. Triggers: user asks to read/modify/verify a .docx thesis; mentions 论文/毕业论文/学位论文; needs to insert images/tables/formulas; wants format check or style cleanup.
type: skill
---

# 论文 DocX 工具

有两种操作方式，根据复杂度选择：

| 场景 | 方式 |
|------|------|
| 单步操作（1-2 次修改） | `python cli.py <command> <file> [options]` |
| 多步复杂操作（≥3 次，跨类型） | `from api import ThesisEditor` → 单进程脚本 |
| DocX工具无法满足要求 | 在 thesis-docx/scripts/ 下写python脚本解决，并保留 |

所有输出 JSON。

## 思维模型

| 原语 | 对应命令 |
|------|---------|
| 读内容 | `read-*` / `search` |
| 替换内容 | `replace-*` |
| 增加内容 | `insert-*` |
| 删 | `delete-*` |
| 检查 | 读 checklist.md |

## 黄金流程

```
诊断 → 操作 → 验证 → 下一操作
 ↑                    |
 └──── 失败回滚 ──────┘
```

| 操作类型 | 操作命令 | 验证命令 |
|---------|---------|---------|
| 改文字 | replace-text / replace-inline | search |
| 改表格 | replace-table | read-table --index N --deep |
| 插图片 | insert-image | read-images / read-section --deep |
| 插表格 | insert-table | read-table --index N --deep |
| 插公式 | insert-formula | read-formulas |
| 删段落 | delete-paragraph | search / read-section |
| 改页设置 | set-page-setup | read-page-setup --verify |
| 改样式 | assign-styles / fix-format | read-structure --verify |

## 多步操作脚本模板

`ThesisEditor`（`api.py`）是 CLI 的编程等价物——提供与 CLI 命令基本对应的 Python 方法（`replace_inline`、`set_page_setup`、`delete_paragraph`、`replace_text`、`format_inline`、`insert_formula` 等，完整列表见 `api.py`）。它与 CLI 共用同一套底层逻辑，区别只是不经过 argparse 解析参数。

≥3 次修改或跨操作类型时用 `ThesisEditor` 写单进程脚本，避免多次 CLI 调用的打开/保存开销和索引漂移：

```python
from api import ThesisEditor
with ThesisEditor("论文.docx") as editor:
    editor.set_page_setup(width=21, height=29.7, margin_top=2.5)
    editor.replace_inline(by_text="图6-1", old="图6-1", new="图3-1")
    editor.replace_inline(by_text="式(4.1)", old="式(4.1)", new="式(2.1)")
    editor.delete_paragraph(by_text="要删除的段落")
    editor.save()
```

## 文档地图

| 你要做什么 | 先看 | 在哪 |
|-----------|------|------|
| 找命令 | "我要做 X → 用 Y" | QUICK.md |
| 确认命令参数 | 完整参考 + 示例 | CLI.md |
| 避坑 | 索引漂移 / 公式 / 批注 | lessons.md |
| 学术论文规范检查 | checklist 逐项排查 | checklist.md |
| 复杂脚本复用 | 批量修复/缩写检查 | scripts/ 目录 |


对于无法用 CLI 自动化验证的项，用 `read-table-context` / `read-section --deep` 获取上下文后自行判断。
