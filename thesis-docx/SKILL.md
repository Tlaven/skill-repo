---
name: thesis-docx
description: Chinese thesis .docx editing toolkit. Use to read, edit, format, or verify .docx files through CLI commands. Supports full-text reading with --deep mode, inline text replacement with format control, style assignment, template format import, reference management, formula insertion (OMML preserved), and reading with --verify for anomaly detection. Triggers: user asks to read/modify/verify a .docx thesis; mentions 论文/毕业论文/学位论文; needs to insert images/tables/formulas; wants format check or style cleanup.
type: skill
---

# 论文 DocX 工具

`python cli.py <command> <file> [options]`，所有输出 JSON。

## 思维模型

**用户需求 → 拆成原语 → 选命令 → 执行 → 验证**

| 原语 | 对应命令 |
|------|---------|
| 读内容 | `read-*` / `search` |
| 改文字 | `replace-text` / `replace-inline` / `replace-batch` |
| 改表格 | `replace-table` |
| 增内容 | `insert-* --after-text` |
| 改格式 | `set-format` / `format-inline` / `assign-styles` / `set-page-setup` |
| 检查 | `check-*` |
| 删 | `delete-paragraph --by-text` / `delete-comments` |

## 黄金流程

每步操作后立即验证，形成闭环：

```
诊断 → 操作 → 验证 → 下一操作
 ↑                    |
 └──── 失败回滚 ──────┘
```

| 操作类型 | 操作命令 | 验证命令 |
|---------|---------|---------|
| 改文字 | replace-text / replace-inline | read-paragraphs / search |
| 改表格 | replace-table | read-table --index N --deep |
| 插图片 | insert-image | read-images / read-section --deep |
| 插表格 | insert-table | read-tables / list-references |
| 插公式 | insert-formula | read-formulas |
| 删段落 | delete-paragraph | read-full / read-section |
| 改页设置 | set-page-setup | read-page-setup --verify |
| 改整体格式 | assign-styles / fix-format | read-structure --verify |

## 陷阱

1. **段落索引漂移** → 始终用 `--by-text` / `--after-text`。展开: lessons.md §1
2. **≥3 次 insert/delete 写单脚本** → 多步操作同进程。展开: lessons.md §1
3. **FORMULA_X_X 残留** → 插公式后手动 `replace-inline --old "FORMULA_3_1" --delete`。展开: lessons.md §5

## 验证（–verify）

原 check-* 命令已移除，验证功能附加到 read-*/list-* 的 `--verify` 参数上：

| 验证点 | 对应命令 |
|--------|---------|
| 页宽/高/边距是否符合标准 | `read-page-setup --verify` |
| 正文样式异常（字号/行距/缩进） | `read-section --verify` |
| 标题样式未分配 | `read-structure --verify` |
| 引用编号对应（未引用/未定义/顺序） | `list-references --verify` |

## 文档地图

动手前先读对应文档，选好命令再执行：

| 你要做什么 | 先看 | 在哪 |
|-----------|------|------|
| 找命令 | "我要做 X → 用 Y" | QUICK.md |
| 确认命令参数 | 完整参考 + 示例 | CLI.md |
| 避坑 | 索引漂移 / 公式 / 批注 | lessons.md |
