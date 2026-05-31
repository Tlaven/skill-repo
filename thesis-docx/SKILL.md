---
name: thesis-docx
description: "Read, edit, and manage Chinese academic theses in .docx format. TRIGGER: .docx, thesis, 论文, section, paragraph, format check, 格式, 章节, 降重, AIGC, caption, formula, reference, style, academic paper, 学位论文"
---

# thesis-docx — 中文学术论文 .docx 操作

## 定位

读写中文学术论文 .docx 文件。核心是 `Locator → Anchor → Mutation` 寻址系统：用内容定位，不用索引。

## 原子词表

| 类别 | 原子 | 说明 |
|------|------|------|
| 动作 | replace, insert, delete, get, find, export, validate, count, list, set, save, move | CRUD + 领域操作 |
| 对象 | paragraph, section, image, table, style, caption, formula, reference, header, footer, chapter, page, metadata, structure, property, revision | 对应文档实体模型 |
| 定位 | text, chapter, title, range, after, before, first, last, all, has_revision, revision_type, revision_author | 对应 Locator.kind |

对象层级：`document > section > paragraph > (text + style)`。

**歧义消解**：`paragraph` 是独立对象，操作粒度为整个段落（删除/移动/插入）；`content` / `text` 是段落属性，操作粒度为段落内的文字（替换内容）。`paragraph-delete` = 删整个段落；`content-replace` = 改段落文字（留段落本身）。

## 组合规则

无固定顺序。从词表选原子，`-` 连接，任何排列都合法。参数不嵌入复合词：

```
paragraph-replace-content anchor="原始文字" new="新文字"
section-get-chapter value="3.2"
formula-insert-after anchor="如式(3.1)" latex="E=mc^2" number="(3.1)"
```

### 映射规则

基本 CRUD 遵循 `compound-word → safe.compound_word()` 映射（`-` 换 `_`）。但领域特定方法（如 `insert_formula_chain`）不在映射规则覆盖范围内——通过下面的示例学习。

映射规则的覆盖范围：
```
content-replace       → safe.replace_text(anchor, new_text)    ✓ 可映射
paragraph-delete      → safe.delete_paragraph(anchor)           ✓ 可映射
paragraph-insert-after → safe.insert_paragraph(after, text)     ✓ 可映射
formula-insert        → safe.insert_formula(after, latex)       ✓ 可映射
```

不在映射规则覆盖内的方法（通过示例学习）：
```
formula-insert-chain  → safe.insert_formula_chain(after, formulas)   ✗ 原子组合不到
replace-batch         → safe.replace_batch(pairs, chapter)           ✗ batch 非原子词
export-markdown       → safe.export_markdown()                       ✗ 单一词
validate              → safe.detect_format_issues()                  ✗ 单一词
```

## 示例

### paragraph-insert-after
- 原子：paragraph, insert, after
- 含义：在锚点段落后插入新段落
- 库调用：`safe.insert_paragraph(after=anchor, text="正文内容", style="Body Text")`
- 自实现思路：`resolve(Locator(kind="text", value="锚点文字"))` → 拿到 Anchor → 调 `insert_paragraph` → 内部自动 `_rebuild()`
- 要点：新段落索引 = `after.paragraph_index + 1`。style 参数用 Word 样式名（`"Body Text"`, `"Heading 2"` 等）。

### paragraph-delete
- 原子：paragraph, delete
- 含义：删除整个段落
- 库调用：`safe.delete_paragraph(anchor)`
- 自实现思路：定位 → 删除 → 自动 rebuild
- 要点：批量删除多个段落时**从后往前删**（索引大的先删），避免索引漂移导致错删。

### content-replace
- 原子：content, replace（等价于 text, replace）
- 含义：替换段落文字内容，保留格式和修订历史
- 库调用：`safe.replace_text(anchor, new_text)`
- 自实现思路：`resolve` 或 `find` 定位 → 替换 → 保留原段落的 run 格式

### formula-insert-chain
- 含义：批量顺序插入多个 LaTeX 公式（自动转 OMML）
- 库调用：`safe.insert_formula_chain(after, [(latex, eq_number), ...])`
- 代码：
```python
anchor = safe.find(Locator(kind="text", value="如式(3.1)所示"))
safe.insert_formula_chain(anchor, [
    (r"v = W_v f_v(i) + b_v", "(3.1)"),
    (r"u = W_t f_t(t) + b_t", "(3.2)"),
])
```
- 要点：不要循环调用 `insert_formula` 插入多个公式——手动追踪索引容易出错，用 `insert_formula_chain`。

### section-content-replace（批量）
- 原子：section, content, replace
- 含义：在指定章节范围内批量替换文字
- 库调用：`safe.replace_batch(pairs=[("旧文字", "新文字")], chapter="3")`
- 自实现思路：resolve chapter 范围 → 遍历段落匹配 → 逐个替换

### 失败兜底：lxml 直操
当 `resolve` 找不到目标，或库方法返回 `False` 时：
```python
# 示例：删除两个段落之间的所有内容（含表格）
import lxml.etree as etree
body = safe.model._doc.element.body
p_start = safe.model._doc.paragraphs[start_idx]._element
p_end = safe.model._doc.paragraphs[end_idx]._element
to_remove = []
found = False
for child in list(body):
    if child is p_start:
        found = True; continue
    if child is p_end:
        break
    if found:
        to_remove.append(child)
for elem in to_remove:
    body.remove(elem)
safe._rebuild()
```

## 自实现循环

1. 用 `find(locator)` / `find_all(locator)` 定位目标
2. 库方法覆盖 → 直接调用（映射规则 + 示例）
3. 库方法未覆盖 → 用 python-docx / lxml 直操，通过 `safe.save()` 保存
4. 记录实现，下次复用

`Locator` 的 kind 就是定位原子：`text`, `chapter`, `title`, `after_text`, `before_text`, `image`, `table`, `formula`, `reference`, `has_revision` 等。`find` 是最常用的定位入口。

## 底层库

路径：`core/`。`SafeDocument` = persistence.py + 8 mixins：

| 模块 | 提供 |
|------|------|
| persistence.py | 基础 CRUD + save_zip（`replace_text`, `delete_paragraph`, `insert_paragraph`, `find`, `find_all`） |
| editor.py | 批量替换 + 段落移动（`replace_batch`, `move_paragraph`） |
| table.py | 表格替换/插入（含三线表） |
| image.py | 图片插入/替换 |
| formula_mixin.py | LaTeX→OMML 公式（`insert_formula`, `insert_formula_chain`, `replace_formula`） |
| style.py | 样式分配 + 格式 setter + 自动修复 |
| reference.py | 参考文献增删重编号 |
| layout.py | 页边距/页眉页脚 |
| exporter.py | 验证/统计/Markdown导出/图片提取 |

`create_thesis(output, outline, template)` 在 `creator.py` — 从 Markdown 大纲创建 .docx。
`DocumentModel` 在 model.py — 6 类索引 + resolve/resolve_all。

不确定某个操作怎么映射时，先看上面的示例。示例覆盖了最常见的操作模式。

## 参考文档

| 要做什么 | 先看 |
|---------|------|
| 理解格式角色 body/caption/reference 对应什么 | `references/format-roles.md` |
| 查字号/行距/单位换算 | `references/typography.md` |
| 判断段落是否太长、自主拆分 | `references/paragraph-length.md` |
| 检测和改写套话/废话 | `references/cliches.md` |
| 统一参考文献格式 | `references/reference-format.md` |
| 检查图表编号和交叉引用 | `references/figure-table-numbering.md` |
| 检查摘要和结论是否重复 | `references/abstract-vs-conclusion.md` |
| 检查关键术语是否一致 | `references/terminology.md` |
| 检查占位符/TODO/空段残留 | `references/residual-content.md` |
| 检查中英文标点混用 | `references/punctuation.md` |
| 检查目录/致谢/声明/附录完整性 | `references/document-structure.md` |
| 检查公式编号连续性和交叉引用 | `references/formula-numbering.md` |
| 检查图片尺寸/格式/题注和表格质量 | `references/figure-table-quality.md` |
| 检查引用密度和孤立参考文献 | `references/citation-density.md` |
| 对照中英文摘要和关键词 | `references/abstract-bilingual.md` |
| 检查章节篇幅是否均衡 | `references/section-balance.md` |
| 检查页边距/纸张/页眉页脚 | `references/page-setup.md` |
| 检查中英文关键词对应和格式 | `references/keywords.md` |
| 检查标题编号是否连续无跳号 | `references/section-numbering.md` |

## 边界

- **复合词**：单步 CRUD（content-replace, paragraph-delete, paragraph-insert, formula-insert）
- **单一词**：save, export-markdown, validate, assign-headings, renumber-references, formula-insert-chain
- **脚本**：多步编排（章节重构、批量格式修复等，agent import 库写脚本）

## 安全规则

- **保存用 `safe.save()`**。python-docx 原生 save 丢失公式和图片。
- **定位用内容，不用索引**。insert/delete 后索引漂移。
- **先备份再批量修改**。`safe.save(output_path=...)`。
- **操作失败返回 False**。检查返回值，False 时用 lxml 直操。

## 依赖

```
python-docx
lxml
latex2mathml
```
