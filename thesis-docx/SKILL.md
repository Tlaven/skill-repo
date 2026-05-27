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

### 1. 永远用内容定位，不用索引

```python
# ✅ 正确（ThesisEditor）
editor.replace_text(by_text="旧段落", text="新内容")
editor.insert_table(after_text="锚定段落", data=[...])
editor.insert_paragraph(after_text="锚定段落", text="新内容")

# ❌ 危险（insert/delete 后索引漂移）
editor.insert_paragraph(after=43, ...)
editor.insert_paragraph(after=43, ...)  # 第二次的 43 已经偏了
```

### 2. 保存必须用 save_zip()

`python-docx` 原生的 `doc.save()` 会**丢失 OMML 公式和插入的图片**。eval 模式和 ThesisEditor 已自动处理。

### 3. 永远不要在目标文档上直接测试

测试脚本应在副本上运行。每次 eval 成功后，用 `git checkout` 或原始备份恢复，再重新操作。

### 3. 不支持 SVG 图片

所有插图必须为 **PNG 或 JPEG**。

### 4. 公式占位符已自动清理

`insert_formula` 会自动清理 `FORMULA_X_X` 占位符。

### 5. 本工具不创建修订标记

所有写操作（`replace_text`、`insert_table`、`rewrite_section` 等）均为**直接写入**，不会在 Word 中生成修订标记（`<w:ins>`/`<w:del>`）。如需带修订标记的修改，替代方案：
- 修改前用 `shutil.copy2()` 备份原文件
- 修改后用 Word「审阅 → 比较」功能对比新旧版本生成修订记录
- 或使用 win32com 脚本（见 `lessons.md` §修订模式替代方案）

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

### 高级方法（优先使用）

| 方法 | 用途 |
|------|------|
| `editor.replace_all(mapping, scope)` | 批量替换。mapping=`{"旧":"新"}`，scope=`"chapter:3"` / `"section:标题"` / None(全文档) |
| `editor.rewrite_section(title, paragraphs)` | 整节重写。paragraphs=`[{"text":"...", "style":"body"}, ...]` |
| `editor.rewrite_paragraphs(mapping)` | 多段按内容定位替换。mapping=`{"锚定文本":"新全文"}` |
| `editor.fix_format(preset="gb-academic")` | 自动修复格式（样式+页面+引用） |
| `editor.assign_styles(preset="gb-academic")` | 样式识别+分配 |

### 原语方法

高级方法不够用时用这些：

| 方法 | 用途 |
|------|------|
| `editor.replace_text(by_text=, text=)` | 替换整段 |
| `editor.replace_inline(by_text=, old=, new=)` | 段内子串替换（保留格式） |
| `editor.format_inline(by_text=, target=, bold=)` | 改格式不改文字 |
| `editor.delete_paragraph(by_text=)` | 删段落 |
| `editor.move_paragraph(by_text=, after_text=)` | 移动段落（原子操作） |
| `editor.insert_table(after_text=, data=, caption=, three_line=False)` | 插表格 |
| `editor.insert_image(after_text=, image=, caption=)` | 插图片 |
| `editor.insert_formula(after_text=, latex=, number=)` | 插公式 |
| `editor.raw_doc` | python-docx Document 对象（escape hatch） |

### 读方法

| 方法 | 用途 |
|------|------|
| `editor.read_full()` | 全文结构 |
| `editor.read_section(title=, deep=False)` | 章节内容（deep=True 展开完整格式/表格/图片） |
| `editor.search(query=)` | 搜索关键词 |
| `editor.find_text("关键词")` | 快捷查找，返回首匹配文本 |
| `editor.read_stats()` | 字数/段落/图表统计 |

## 论文编辑工作流

收到一份论文时的操作顺序：

### 阶段 1：通读，不做任何修改

```bash
# 看结构
python cli.py read-full "论文.docx"
# 逐章读内容（不要 skip 任何一节）
python cli.py read-section --title "节名" --deep "论文.docx"
```

**目的：建立对论文内容本身的认知，之后再判断哪些该改。** 不要跳过这一步直接跑 `--verify`。

### 阶段 2：逐表检查

每张表用 `read-table-context` 看上下文：

```bash
python cli.py read-table-context --index 0 "论文.docx"
python cli.py read-table-context --index 1 "论文.docx"
# ...每张表都要看
```

检查三要素是否齐全：

| 要素 | 怎么检查 | 缺失后果 |
|------|---------|---------|
| 题注在表格上方 | `read-table-context` 输出的 caption 字段 | 读者不知道表格在说什么 |
| 正文引用（"如表X-Y所示"）就在题注前 | 看 context_paragraphs 中题注前的文字 | 表格像硬塞进去的 |
| 表后有分析文字 | 看 context_paragraphs 中表格后的文字 | 读者不知道为什么有这个表 |

同时用 `checklist.md` 的 1.1-1.6 逐项过。**不要只看 `--verify` 的输出**——它只查编号跳号。

### 阶段 3：逐项修复

根据阶段 2 发现的问题清单，写 eval 脚本逐一修复。

**规则：**
- 先在副本上试：`editor.save_zip("副本.docx")` → 确认效果 → 再改目标
- 一次只修一类问题（不要结构修改和内容修改混在一起）
- 每次 eval 前先 `git checkout` 恢复原始状态

### 阶段 4：验证

```bash
# 结构验证（只查编号跳号，不查内容）
python cli.py read-structure --verify "论文.docx"
# 人工重新通读改过的章节
python cli.py read-section --title "改过的节" --deep "论文.docx"
```

**`--verify` 通过 ≠ 文档没问题。** 真正验证改得好不好，必须重新读一遍改过的章节。

## 任务流程

### 类型 A：单一操作

→ 写一个 eval 脚本，一行即可。

### 类型 B：质量审查或改良

→ **先读 `checklist.md`**，按清单逐项排查，列出问题清单后再用 eval 修改。

→ **表格上下文检查**：每张表必须有题注（在上方）、引入文字（题注前）、分析文字（表格后）。缺少任何一项就是"硬塞的"。
  - `python cli.py read-table-context --index N 论文.docx` 查看表格上下文
  - `read-structure --verify` 只查编号跳号，**不查内容合理性**

### 类型 C：格式修复

→ **先读 `lessons.md`** 了解避坑点，再 `editor.fix_format()` 或 `editor.assign_styles()`。

### 类型 D：内容填充

→ `editor.read_full()` 了解结构，再 `editor.rewrite_section()` 批量写入。

## 读操作 (CLI)

eval 模式外需要快速查看时用 CLI：

| 你想做什么 | 命令 |
|-----------|------|
| 看全文结构 | `python cli.py read-full "论文.docx"` |
| 读某节内容 | `python cli.py read-section --title "节名" --deep "论文.docx"` |
| 搜索关键词 | `python cli.py search --query "关键词" "论文.docx"` |
| 格式检查 | `python cli.py read-structure --verify "论文.docx"` |
| 页面检查 | `python cli.py read-page-setup --verify "论文.docx"` |
| 引用检查 | `python cli.py list-references --verify "论文.docx"` |

## _guide 提示

操作输出中可能包含 `_guide` 字段，提供上下文相关的使用建议。这些提示在关键节点自动触发（第一次写操作、结构性变更后），帮助正确使用本工具。

## 数据格式

### 表格 data

二维 JSON 数组，第一行为表头：`[["列1","列2"],["v1","v2"]]`。加 `three_line=True` 用三线表。

### 段落 paragraphs

`[{"text": "正文", "style": "body"}]`。style 可选：`body`, `h1`, `h2`, `h3`, `caption`, `reference`。

### 公式 latex

标准 LaTeX：`NDVI = \\frac{NIR - R}{NIR + R}`，编号用 `number="(2.1)"`。

## 文件存放

| 文件类型 | 存放到 | 生命周期 |
|---------|-------|---------|
| eval 临时脚本 | 任意位置 | 会话结束前删除 |
| 图表导出图 | 论文项目目录下 `diagrams/` | 永久 |

## 文档地图

| 你要做什么 | 先看 | 在哪 |
|-----------|------|------|
| 避坑 | 操作经验 | `lessons.md` |
| 质量检查 | 逐项排查 | `checklist.md` |
| 查底层命令 | CLI 参考 | `CLI.md` |

## 已知限制

### 1. 不创建修订标记

所有写操作为直接写入，不产生 Word 修订标记。详见 Critical Rules §5。

### 2. 修订标记影响读准确性

文档含 `<w:ins>`/`<w:del>` 时，`paragraph.text` 可能不准确（丢失插入文本或残留删除文本）。
始终以 Word 中「审阅 → 所有标记」视图为最终依据。
使用 `detect-revisions` 确认修订内容，而非依赖 `read-paragraphs` 的文本输出。

### 3. TOC 字段文本在搜索盲区

自动目录（TOC 字段）中的文字可能以单段落多 run 形式存在，`search` 命令无法覆盖。
使用 `search-xml` 命令（见 CLI.md）直接搜索底层 XML。

### 4. Windows PowerShell 中 `|` 需转义

`search --query "A|B"` 中的 `|` 被 PowerShell 解释为管道。替代方案：
- 多次搜索 `--query "A"` + `--query "B"`
- 或使用 `--query-file queries.txt`（每行一个关键词）
