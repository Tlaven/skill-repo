---
name: thesis-docx
description: Chinese thesis .docx editing toolkit. Use to read, edit, format, or quality-check .docx files. Supports full-text reading with --deep mode, inline text replacement with format control, style assignment, template format import, reference management, formula insertion (OMML preserved), and comprehensive quality checks. Triggers: user asks to read/modify/check a .docx thesis; mentions 论文/毕业论文/学位论文; needs to insert images/tables/formulas; wants format check or style cleanup.
type: skill
---

# 论文 DocX 工具

`python cli.py <command> <file> [options]`。所有输出为 JSON。

详细参考：[CLI.md](CLI.md) | [lessons.md](lessons.md) | [api.py](api.py)

## 必须先知道的陷阱

1. **段落索引会漂移** — `insert`/`delete` 后所有旧索引失效。解决办法：用 `--by-text "子串"` 或 `--after-text "子串"` 代替索引。
2. **复杂修改写脚本** — 涉及 ≥3 次 `insert`/`delete` 时，用 Python 脚本在同一个进程内操作，不要多次调 CLI。
3. **FORMULA_X_X 不会自动清理** — 插入公式后需手动 `replace-inline --old "FORMULA_3_1" --new ""`。

## 思维模型：需求 → 原语 → 命令

用户需求拆成以下 6 种原语之一，映射到对应命令：

| 原语 | 对应命令 | 适用场景举例 |
|------|---------|------------|
| 读内容 | `read-*` / `search` | 查结构、读段落、搜关键词、看图片/公式/表格 |
| 改文字 | `replace-text` / `replace-inline` | 改句子、补说明、替换关键词 |
| 增内容 | `insert-* --after-text` | 加段落、插图片/表格/公式/分页 |
| 改格式 | `set-*` / `format-inline` / `assign-styles` | 改样式、调字体、套模板 |
| 检查 | `check-*` | 质量检查、引用检查、格式对比 |
| 删 | `delete-paragraph` / `delete-comments` | 删段落、删批注 |

**判断准则**：任务属于上述某一种 → CLI 已能处理。只有当需要**组合 3+ 次 insert/delete** 或**遍历文档做条件修改**时，才需要写脚本放到 `scripts/` 下。

## 能力速查

### 看（READ）

| 我要做什么 | 命令 |
|-----------|------|
| 全文概况 | `read-full`（~3k tokens 地图） |
| 展开某节全文+格式+图表 | `read-section --title "节名" --deep`（≤3000字自动限） |
| 某段落在哪+附近元素 | `read-location --paragraph N` |
| 某段完整格式（runs） | `read-paragraph --index N --deep` |
| 表格全部数据+边框+字体 | `read-table --index N --deep` |
| 所有公式位置+数学内容 | `read-formulas` |
| 所有图片列表+标题 | `read-images` |
| 样式定义 | `extract-rules` |
| 页面设置/批注/统计 | `read-page-setup` / `read-comments` / `read-stats` |
| 章节树 | `read-structure` |
| 搜索关键词 | `search --query "关键词"` |

### 改（WRITE + FORMAT）

| 我要做什么 | 命令 |
|-----------|------|
| 替换整段 | `replace-text --by-text "旧段" --text "新段"` |
| 改段内一个词（保留格式） | `replace-inline --by-text "锚定段" --old "旧词" --new "新词"` |
| 改词+同时设格式 | `replace-inline --old X --new Y --bold --font 楷体` |
| 只改格式不改文字 | `format-inline --target "子串" --bold --color FF0000` |
| 插入一段 | `insert-paragraph --after-text "锚定" --text "内容" --style body` |
| 批量插入多段 | `write-paragraphs --after N --data '[{...}]'` |
| 删除一段 | `delete-paragraph --by-text "要删的段"` |
| 插入图片/表格/公式 | `insert-image/table/formula --after-text "锚定"` |
| 替换图片 | `replace-image --caption "图3-1" --image "new.png"` |
| 设置段落样式 | `set-format --by-text "标题" --style h1` |
| 自动分配全部样式 | `assign-styles` |
| 套用学校模板格式 | `apply-template --template "模板.docx" "论文.docx"` |
| 修改页面/页眉/页脚 | `set-page-setup` / `set-header` / `set-footer` |
| 参考文献管理 | `list-references` / `add-reference` / `renumber-references` |

### 查（CHECK）

| 我要做什么 | 命令 |
|-----------|------|
| 全面检查 | `check-all` |
| 占位符残留 | `check-placeholders`（TODO/FORMULA_/IMAGE_/TABLE_） |
| 公式引用检查 | `check-formula-references`（前后有无"如式"引用和"其中"解释） |
| 图片引用检查 | `check-figure-references` |
| 写作风格问题 | `check-style`（AI 痕迹检测） |
| 对照模板检查格式 | `check-format --template "模板.docx"` |

### 建（CREATE）

| 我要做什么 | 命令 |
|-----------|------|
| 从零创建 | `create "论文.docx" --preset gb-academic` |
| 从学校模板创建 | `create "论文.docx" --from-template "学校模板.docx"` |

## 我不确定用什么命令

按这个顺序思考：

1. **先读** — `read-full` 看全貌，`read-location` 定位，`read-section --deep` 看细节
2. **后改** — 文字用 `replace-inline`，格式用 `format-inline`，段落用 `insert/delete --by-text`
3. **再查** — `check-all` 兜底，具体问题用专项 check

## 内容定位参数（代替索引）

| 参数 | 适用命令 | 作用 |
|------|---------|------|
| `--by-text "子串"` | replace-text / replace-inline / delete-paragraph / set-format / format-inline | 找到含此文字的段落 |
| `--after-text "子串"` | insert-paragraph / insert-image / insert-table / insert-page-break | 在此段落后插入 |
| `--old / --new` | replace-inline | 段内查找替换 |
| `--target "子串"` | format-inline | 定位要改格式的文字 |

## 反模式（不要这样做）

- ❌ 用了 `--paragraph N` 后又做 insert/delete → 索引漂移，优先用 `--by-text`
- ❌ 自己写 python-docx 遍历读内容 → 用 `read-section --deep` 或 `read-paragraph --deep`
- ❌ 多次 CLI 调用来做多步 insert → 写脚本
- ❌ 用 `replace-text` 做全文关键词替换 → 用 `replace-batch`

## 公式

- 批量：`insert-formulas --json formulas.json`，连续公式用 `"position": "last"`
- 验证：返回值 `saved_formula_count` 确认写入成功
- 清理：插入后 `FORMULA_X_X` 不会自动消失，用 `replace-inline` 手动清除

## Windows

- 中文文件名 → `--find-file "子串"`
- 不要用 `python -c "多行代码"` → 写成 `.py` 文件
- subprocess 读输出 → `encoding='utf-8'`

## 通用选项

`--backup` / `--find-file` / `--output` / `--query-file`
