---
name: thesis-docx
description: "Use when the user mentions .docx files that are Chinese theses; also when 论文, 毕业论文, or 学位论文 is mentioned"
type: skill
---

# 论文 DocX 工具

对 .docx 格式的中文学位论文进行读、写、格式检查与修复的完整工具链。

## When to Use

**使用场景：**
- 用户提到 .docx 文件且是中文论文（毕业论文/学位论文）
- 需要查看/修改论文的段落、表格、图片、公式内容
- 需要检查论文格式规范（标题样式、页面设置、引用一致性）
- 需要插入图片/表格/公式到指定位置
- 需要批量替换文字（如术语统一、编号修正）

**不适合：**
- 非 .docx 格式的文档 → 先转换
- 纯文本处理（无格式要求） → 直接文本工具更快
- 初次写作（非修改已有文档） → 用 Word/WPS

## Core Pattern

```
诊断 → 操作 → 验证 → 下一操作
 ↑                    |
 └──── 失败回滚 ──────┘
```

每次修改后都验证结果，失败时回滚重试。

## Quick Reference

| 你想做什么 | 命令/方式 |
|-----------|----------|
| 快速看全文结构 | `read-full "论文.docx"` |
| 展开某节内容 | `read-section --title "节名" --deep` |
| 改整段文字 | `replace-text --by-text "旧" --text "新"` |
| 改段内几个词 | `replace-inline --by-text "锚定段" --old "旧" --new "新"` |
| 改格式不改字 | `format-inline --by-text "锚定段" --target "子串" --bold` |
| 删一段 | `delete-paragraph --by-text "内容"` |
| 插图片 | `insert-image --after-text "锚定" --image fig.png --caption "图3-1 标题"` |
| 插表格 | `insert-table --after-text "锚定" --data '[["列1","列2"],["v1","v2"]]'` |
| 插公式 | `insert-formula --after-text "锚定" --latex "E=mc^2" --number "(3.1)"` |
| 格式检查 | `read-structure --verify "论文.docx"` |
| 页面检查 | `read-page-setup --verify "论文.docx"` |
| 引用检查 | `list-references --verify "论文.docx"` |
| 批量多步操作 | `ThesisEditor` Python API（见下方） |

不确定用哪个命令 → 看 CLI.md 按类别找。

## 操作方式

根据复杂度选择：

| 场景 | 方式 |
|------|------|
| 单步操作（1-2 次修改） | `python cli.py <command> <file> [options]` |
| 多步复杂操作（≥3 次，跨类型） | `from api import ThesisEditor` → 单进程脚本 |
| CLI/API 无法满足 | 在 `scripts/` 下写 python 脚本解决，并保留复用 |

所有输出 JSON。

### 思维模型

| 原语 | 对应命令 |
|------|---------|
| 读内容 | `read-*` / `search` |
| 替换内容 | `replace-*` |
| 增加内容 | `insert-*` |
| 删 | `delete-*` |
| 检查 | 读 checklist.md |

### 多步操作脚本模板

`ThesisEditor`（`api.py`）是 CLI 的编程等价物——提供与 CLI 命令基本对应的 Python 方法。它与 CLI 共用同一套底层逻辑，区别只是不经过 argparse 解析参数。

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

## Common Mistakes

### 段落索引漂移
`insert-paragraph` / `delete-paragraph` 后所有段落索引立即偏移。
**解法：** 优先用 `--by-text "子串"` / `--after-text "子串"` 内容定位代替索引定位。≥3 次修改写单进程脚本。

### FORMULA_X_X 残留
`insert-formula` 不自动清理占位符。
**解法：** 插入公式后手动 `replace-inline --old "FORMULA_3_1" --delete`。

### 保存丢失公式/图片
`python-docx` 原生的 `doc.save()` 会丢失 OMML 公式和图片。
**解法：** 所有保存都用 `save_zip()`（CLI、API 已默认使用，仅当自己写底层代码时注意）。

### 手动插入段落后的样式
通过 XML 直接插入的段落，样式可能不被 Word 正确识别。
**解法：** 保存后运行 `assign-styles`。

更多操作经验见 lessons.md。

## 文档地图

| 你要做什么 | 先看 | 在哪 |
|-----------|------|------|
| 查命令参考 | 完整参考 | CLI.md |
| 避坑 | 索引漂移 / 公式 / 批注 | lessons.md |
| 学术论文规范检查 | checklist 逐项排查 | checklist.md |
| 复杂脚本复用 | 批量修复/缩写检查 | scripts/ 目录 |
