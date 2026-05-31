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
| 动作 | replace, insert, delete, get, find, resolve, export, validate, count, list, set, save, move | CRUD + 领域操作 |
| 对象 | paragraph, section, image, table, style, caption, formula, reference, header, footer, chapter, page, metadata, structure, property, revision | 对应文档实体模型 |
| 定位 | text, chapter, title, range, after, before, first, last, all, has_revision, revision_type, revision_author | 对应 Locator.kind |

对象层级：`document > section > paragraph > (text + style)`。

## 组合规则

无固定顺序。从词表选原子，`-` 连接，任何排列都合法。参数不嵌入复合词：

```
paragraph-replace-text anchor="原始文字" content="新文字"
section-get-chapter value="3.2"
```

### 复合词 → 库调用

复合词映射到 `SafeDocument` 方法：`-` 换 `_`，动作在前、对象在后。

```
list-citations          → safe.list_citations()
detect-format-issues    → safe.detect_format_issues()
count-words             → safe.count_words()
writing-style-check     → safe.check_writing_style()
```

带 `_guide` 返回的命令加 `with_guide=True`：`safe.list_citations(with_guide=True)`。

底层库方法名与复合词命名一致，agent 不需要查映射表——拼出来就是方法名。

## 自实现循环

1. 用 `resolve()` / `resolve_all()` 定位目标
2. 调用 `SafeDocument` 方法
3. 定位失败 → 用 python-docx / lxml 直操，通过 `safe.save()` 保存
4. 记录实现，下次复用

## 底层库

路径：`core/`。`SafeDocument` = persistence.py + 7 mixins：

| 模块 | 提供 |
|------|------|
| persistence.py | 基础 CRUD + save_zip |
| editor.py | 批量替换 + 段落移动 |
| table.py | 表格替换/插入（含三线表） |
| image.py | 图片插入/替换 |
| formula_mixin.py | LaTeX→OMML 公式 |
| style.py | 样式分配 + 格式 setter + 自动修复 |
| reference.py | 参考文献增删重编号 |
| layout.py | 页边距/页眉页脚 |
| exporter.py | 验证/统计/Markdown导出/图片提取 |

`create_thesis(output, outline, template)` 在 `creator.py` — 从 Markdown 大纲创建 .docx，无模板用默认样式。

`DocumentModel` 在 model.py，提供 6 类索引 + resolve/resolve_all。

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

## 边界

- **复合词**：单步 CRUD（paragraph-replace, style-set, reference-add）
- **单一词**：save, export-markdown, validate, assign-headings, renumber-references
- **脚本**：多步编排（agent import 库写脚本）

## 安全规则

- **保存用 `safe.save()`**。python-docx 原生 save 丢失公式和图片。
- **定位用内容，不用索引**。insert/delete 后索引漂移。
- **先备份再批量修改**。`safe.save(output_path=...)`。
- **操作失败返回 False**。检查 anchor 有效性，改用直操 XML。

## 依赖

```
python-docx
lxml
latex2mathml
```
