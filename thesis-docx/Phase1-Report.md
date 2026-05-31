# Phase 1 能力报告

## 一、可索引的实体类别（6 类）

| 实体 | 类型 | 字段数 | 读 | 定位 | 写 |
|------|------|--------|----|------|----|
| `ParagraphInfo` | 段落 | 14 | ✅ | ✅ | ✅ replace/delete/insert/move |
| `SectionNode` | 章节树 | 8+1方法 | ✅ | ✅ | — |
| `ImageInfo` | 图片 | 8 | ✅ | ✅ | ✅ insert/replace |
| `TableInfo` | 表格 | 6 | ✅ | ✅ | ✅ insert/replace（含三线表） |
| `FormulaInfo` | 公式 | 5 | ✅ | ✅ | ✅ insert/replace（LaTeX→OMML） |
| `ReferenceInfo` | 参考文献 | 5 | ✅ | ✅ | — |

## 二、定位方式（12 种 Locator kind）

| Locator kind | 返回的 Anchor kind | 用途 |
|---|---|---|
| `text` | paragraph | 按文字子串 |
| `after_text` | paragraph | 取匹配段的后一段 |
| `chapter` | section / paragraph | 按章节号（递归搜整棵树） |
| `section_title` | section / paragraph | 模糊匹配 + 同义词组（6 组） |
| `paragraph_range` | paragraph | 按段落范围 |
| `image` | image | 按图题/章节 |
| `table` | table | 按表题/章节 |
| `formula` | formula | 按公式编号/章节 |
| `reference` | reference | 按序号/文字 |
| `has_revision` | paragraph | 找有修订标记的段落 |
| `revision_type` | paragraph | 按修订类型筛选 |
| `revision_author` | paragraph | 按修订作者筛选 |

**两种模式**：`resolve()` 返回首个匹配；`resolve_all()` 返回全部匹配。

## 三、写操作全景（SafeDocument 方法）

| 操作 | 文件 | 修订保护 | 说明 |
|------|------|---------|------|
| `replace_text(anchor, text)` | persistence | ✅ 不破坏 w:ins/w:del | 段落全文替换 |
| `replace_batch(pairs, chapter)` | editor | ✅ | 可选限定章节 |
| `replace_batch_by_index(pairs)` | editor | ✅ | 按段落索引 |
| `delete_paragraph(anchor)` | persistence | ⚠️ 直接删 | — |
| `insert_paragraph(after, text, style)` | persistence | ✅ 新段无修订 | 锚点后插入 |
| `move_paragraph(source, after)` | editor | ✅ deepcopy | 原子操作，失败回滚 |
| `replace_table(anchor_or_index, data)` | table | — | 行列自适应增减 |
| `insert_table(after, data, caption, three_line)` | table | — | 三线表支持 |
| `replace_image(image_path, anchor, media)` | image | — | 替换二进制 blob |
| `insert_image(after, image_path, width, caption)` | image | — | 自动缩放适配页面 |
| `insert_formula(after, latex, eq_number, centered)` | formula_mixin | — | LaTeX → OMML |
| `replace_formula(anchor, latex, eq_number)` | formula_mixin | — | 保留原居中属性 |
| `save(output_path)` | persistence | ✅ zip 重写 | 保护公式/图片，保存后自动重建索引 |

## 四、修订（Track Changes）支持

```
段落检测     → has_revisions, revision_count, revision_types, revision_authors
章节聚合     → SectionNode 自动汇总其范围内所有段落的修订统计
安全替换     → 只改可见文本，不动 w:ins/w:del，复杂结构返回 False
查询         → find_revised_paragraphs(chapter, author, rev_type)
	          → SectionNode.get_revised_paragraphs(all_paragraphs)
```

## 五、覆盖矩阵

```
          读(索引)  定位(单)  定位(多)  写(单)  写(批量)
段落        ✅       ✅       ✅      ✅      ✅
章节树      ✅       ✅       ✅      —       —
图片        ✅       ✅       ✅      ✅      —
表格        ✅       ✅       ✅      ✅      —
公式        ✅       ✅       ✅      ✅      —
参考文献    ✅       ✅       ✅      —       —
修订        ✅       ✅       ✅      ✅(安全)  ✅
```

## 六、架构

**`Locator → Anchor → Mutation`** 三段式：

1. `Locator(kind, value)` — 描述"要找什么"（内容定位，不用索引）
2. `resolve()` / `resolve_all()` — 在文档中查找，返回 `Anchor`（稳定引用）
3. 用 Anchor 调用写操作 — 操作瞬间索引正确即可，不要求长期稳定

```
SafeDocument
  ├── persistence.py    — 核心持久化 + save_zip + 基础 CRUD
  ├── editor.py         — 批量替换 + 段落移动（EditorMixin）
  ├── table.py          — 表格写操作（TableMixin）
  ├── image.py          — 图片写操作（ImageMixin）
  └── formula_mixin.py  — 公式写操作（FormulaMixin）

DocumentModel
  ├── model.py          — 索引构建 + 查询 API
  ├── locator.py        — resolve() / resolve_all()
  ├── types.py          — Locator, Anchor, 6 个 Info 类型
  └── utils.py          — 工具函数

formula.py              — LaTeX → MathML → OMML 转换
api.py                  — 兼容层（ThesisEditor 薄包装）
```
