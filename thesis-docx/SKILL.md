---
name: thesis-docx
description: "Use when the user mentions .docx files that are Chinese theses; also when 论文, 毕业论文, or 学位论文 is mentioned. NOT for workflows requiring Track Changes creation (revision marks). All write operations are direct (no w:ins/w:del)."
type: skill
---

# 论文 DocX 工具

对 .docx 格式的中文学位论文进行读、写、格式检查与修复的完整工具链。

## When to Use

- 用户提到 .docx 文件且是中文论文（毕业论文/学位论文）
- 需要查看/修改论文的段落、表格、图片、公式内容
- 需要检查论文格式规范（标题样式、页面设置、引用一致性）
- 需要插入图片/表格/公式到指定位置
- 需要批量替换文字（如术语统一、编号修正）
- 需要往空模板中填充论文内容

## 定位

本工具是**论文文档的结构/格式领域专家**。擅长：
- 文档结构操作（章节、段落、表格、图片、公式的增删改移）
- 格式检查与修复（样式、页面设置、引用一致性）
- 基于规则的多步操作（编号修正、批量替换、整节重写）

**不负责内容判断**。段落写得好不好、论点是否充分——这是你（Agent）的智能，不是本工具的职责。

## 运行环境

- **工作目录**：CLI 命令必须在 skill 根目录（`thesis-docx/`）下运行
- **Python 依赖**：`python-docx`, `lxml`, `latex2mathml`（pip install）
- **Windows 限制**：不要用 `python -c "..."` 执行代码，写成 `.py` 脚本文件再 `python script.py`
- **所有输出为 JSON**，用 `json.loads()` 解析

## Critical Rules

违反以下规则会导致数据丢失或损坏：

1. **永远用内容定位，不用索引。** `by_text="旧段落"` 而非 `after=43`——insert/delete 后索引漂移。
2. **保存必须用 save_zip()。** `python-docx` 原生的 `doc.save()` 会丢失 OMML 公式和插入的图片。eval 模式已自动处理。
3. **不在目标文档上直接测试。** 先备份或用副本，确认效果后再改目标。
4. **不支持 SVG 图片。** 所有插图必须为 PNG 或 JPEG。
5. **不创建修订标记。** 所有写操作为直接写入（无 `<w:ins>`/`<w:del>`）。替代方案见 API.md。

## 操作方式

**读用 CLI，写用 eval。**

| 场景 | 方式 |
|------|------|
| 读文档 | `python cli.py read-* / search`（见下方读操作表） |
| 改文档（任何修改） | `python cli.py eval "论文.docx" --script-file ops.py` |

不要用 CLI 做写操作。eval 模式解决所有写场景，不存在"太简单不需要 eval"的情况。

## eval 模式

```bash
python cli.py eval "论文.docx" --script-file ops.py
```

`editor`（ThesisEditor 实例）自动注入，无需 import、无需 save：

```python
# ops.py
editor.replace_all({"图6-": "图3-"}, scope="chapter:3")
editor.rewrite_section("3.2 数据处理", paragraphs=[
    {"text": "新的第一段内容", "style": "body"},
    {"text": "新的第二段内容", "style": "body"},
])
editor.delete_paragraph(by_text="要删除的段落")
```

方法签名和操作提示见 **API.md**。

## 任务流程

### 类型 A：单一操作

→ 写一个 eval 脚本，一行即可。

### 类型 B：质量审查或改良

→ **先读 `checklist.md`**，按清单逐项排查，列出问题清单后再用 eval 修改。

### 类型 C：格式修复

→ **先读 API.md 操作提示**了解避坑点，再 `editor.fix_format()` 或 `editor.assign_styles()`。

### 类型 D：内容填充

→ `editor.read_full()` 了解结构，再 `editor.rewrite_section()` 批量写入。

## 读操作 (CLI)

| 你想做什么 | 命令 |
|-----------|------|
| 看全文结构 | `python cli.py read-full "论文.docx"` |
| 读某节内容 | `python cli.py read-section --title "节名" --deep "论文.docx"` |
| 搜索关键词 | `python cli.py search --query "关键词" "论文.docx"` |
| 格式检查 | `python cli.py read-structure --verify "论文.docx"` |
| 页面检查 | `python cli.py read-page-setup --verify "论文.docx"` |
| 引用检查 | `python cli.py list-references --verify "论文.docx"` |

完整命令列表见 **CLI.md**。

## 文档地图

| 你要做什么 | 先看 | 在哪 |
|-----------|------|------|
| 写 eval 脚本 | 方法签名 + 操作提示 | `API.md` |
| 质量检查 | 逐项排查 | `checklist.md` |
| 查 CLI 命令 | 读操作参考 | `CLI.md` |

## 已知限制

### 1. 修订标记影响读准确性

文档含 `<w:ins>`/`<w:del>` 时，`paragraph.text` 可能不准确。始终以 Word「审阅 → 所有标记」视图为最终依据。使用 `detect-revisions` 确认修订内容。

### 2. TOC 字段文本在搜索盲区

自动目录（TOC 字段）中的文字可能以单段落多 run 形式存在，`search` 命令无法覆盖。用 `search-xml` 直接搜索底层 XML。

### 3. Windows PowerShell 中 `|` 需转义

`search --query "A|B"` 中的 `|` 被 PowerShell 解释为管道。替代方案：多次搜索，或用 `--query-file queries.txt`（每行一个关键词）。
