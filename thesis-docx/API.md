---
name: thesis-docx-api
description: "ThesisEditor API reference for thesis-docx eval mode. Method signatures, data formats, and operational tips."
type: reference
---

# ThesisEditor API 参考

`python cli.py eval "论文.docx" --script-file ops.py`

`editor`（ThesisEditor 实例）自动注入，无需 import、无需 save。

## 高级方法（优先使用）

| 方法 | 用途 |
|------|------|
| `editor.replace_all(mapping, scope)` | 批量替换。mapping=`{"旧":"新"}`，scope=`"chapter:3"` / `"section:标题"` / None(全文档) |
| `editor.rewrite_section(title, paragraphs, include_subsections=False)` | 整节重写。paragraphs 见下方数据格式 |
| `editor.rewrite_paragraphs(mapping)` | 多段按内容定位替换。mapping=`{"锚定文本":"新全文"}` |
| `editor.fix_format(preset="gb-academic")` | 自动修复格式（样式+页面+引用） |
| `editor.assign_styles(preset="gb-academic")` | 样式识别+分配 |

## 原语方法

高级方法不够用时用这些：

| 方法 | 用途 |
|------|------|
| `editor.replace_text(by_text=, text=)` | 替换整段 |
| `editor.replace_inline(by_text=, old=, new=, bold=, font=, size=, color=)` | 段内子串替换，可同时改格式 |
| `editor.format_inline(by_text=, target=, bold=, font=, size=, color=)` | 改格式不改文字 |
| `editor.delete_paragraph(by_text=)` | 删段落 |
| `editor.move_paragraph(by_text=, after_text=)` | 移动段落（原子操作） |
| `editor.insert_table(after_text=, data=, caption=, three_line=False)` | 插表格 |
| `editor.insert_image(after_text=, image=, caption=, width=)` | 插图片。width 为英寸值，默认 80% 页宽 |
| `editor.insert_formula(after_text=, latex=, number=)` | 插公式 |
| `editor.raw_doc` | python-docx Document 对象（escape hatch） |

## 读方法

| 方法 | 用途 |
|------|------|
| `editor.read_full()` | 全文结构 |
| `editor.read_section(title=, deep=False)` | 章节内容（deep=True 展开完整格式/表格/图片） |
| `editor.search(query=)` | 搜索关键词 |
| `editor.find_text("关键词")` | 快捷查找，返回首匹配文本 |
| `editor.read_stats()` | 字数/段落/图表统计 |

## 数据格式

### 表格 data

二维 JSON 数组，第一行为表头：`[["列1","列2"],["v1","v2"]]`。加 `three_line=True` 用三线表。

### 段落 paragraphs

`[{"text": "正文", "style": "body"}]`。style 可选：`body`, `h1`, `h2`, `h3`, `caption`, `reference`。

### 公式 latex

标准 LaTeX：`NDVI = \\frac{NIR - R}{NIR + R}`，编号用 `number="(2.1)"`。

## 操作提示

### 连续公式

连续插入多个公式时用 `insert_formulas`（batch），列表中第二项起加 `"position": "last"` 避免索引漂移：

```python
editor.insert_formulas([
    {"after_text": "锚定", "latex": "...", "number": "(2.2)"},
    {"latex": "...", "number": "(2.3)", "position": "last"},
])
```

### 图片尺寸

自动约束 ≤ 文字区域宽度，未指定时默认 80%。高度不超过页面可用高度。

### 修订文档

带修订标记的段落，先 `accept_revisions` 再改文字。`replace_text` 会自动清除段落内的 `<w:ins>`/`<w:del>`，但先接受再修改更安全。

### 批注

`delete-comments` 自动清理 4 个 XML 文件（comments / commentsExtended / commentsIds / commentsExtensible），不要手工操作。

### 编号重排

`renumber_figures` 只处理 Caption 样式的段落。题注跑到正文样式的段落中时，先 `assign_styles` 再重编号。

### dry-run 替代

无 dry-run 模式。替代：先 `search` 确认定位 → 加 `--backup` → 在副本上试 → 确认后再改目标。

### 修订标记替代方案

本工具不创建修订标记。替代方案：`shutil.copy2()` 备份 → eval 修改 → Word「审阅 → 比较」对比新旧版本。Windows 环境下可用 win32com 脚本操作 TrackRevisions，需单独安装 `pywin32`。
