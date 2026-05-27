---
name: thesis-docx-lessons
description: Accumulated operational lessons for thesis-docx. Index-shifting traps, content-based matching, comment cleanup, formula pitfalls, revision handling.
type: reference
---

# 操作经验手册

> 关键避坑规则已移入 SKILL.md 的 "Critical Rules" 章节。本文件保留补充细节。

## 段落索引漂移（补充细节）

### 安全场景判定

| 场景 | 安全 | 原因 |
|------|------|------|
| 单次 replace-text / replace-inline | Yes | 不增删段落 |
| 单次 insert-paragraph（用 `--by-text`） | Yes | 内容定位 |
| 多次 CLI 调用的 insert/delete 组合 | **No** | 每次调用间索引漂移 |
| insert-formulas 多个绝对 after | **No** | 内部不调整索引 |

### Batch 公式的正确姿势

```json
// ❌ 批量公式用绝对索引
[{"after": 45, "latex": "..."}, {"after": 52, "latex": "..."}]

// ✅ 连续公式用 "position": "last"
[{"after": 52, "latex": "...", "number": "(2.2)"},
 {"latex": "...", "number": "(2.3)", "position": "last"}]
```

## 手动插入段落后的样式修复

通过 XML 直接插入的段落，样式可能不被 Word 正确识别。

**解法：** 保存后运行 `assign-styles`，自动按文本模式分配 Heading 级别。

## 批注操作

- `read-comments` 的 `selected_text` 可能为 `null`（光标位置批注），用 `paragraph_index` 定位
- `delete-comments` 已自动清理 4 个 XML 文件（`comments.xml` / `commentsExtended.xml` / `commentsIds.xml` / `commentsExtensible.xml`），**不要手工操作**
- 中英文样式名（"标题 1" / "Heading 1"）均已支持

## 图片尺寸约束

`insert-image` 自动约束图片不超出页面：宽度 ≤ 文字区域，高度 ≤ 页面可用高度。
未指定 `--width` 时默认 80%。

## 修订处理顺序

修改带修订标记的段落时，**先接受修订，再改文字**：

```python
# ✅ 正确
editor.accept_revisions(start=35, end=40)
editor.replace_text(index=35, text='新文字')

# ❌ 错误：先 replace_text 再 accept_revisions 会导致文字重复
```

`replace_text` 现在会自动清除段落内的 `<w:ins>` 和 `<w:del>` 元素，但先 `accept-revisions` 再修改仍然是更安全的做法。

## 写操作没有 dry-run 预览模式

替代策略：

1. **先用搜索确认定位**：`search --query "目标内容"`
2. **加 `--backup`**：每次写操作加 `--backup`，不满意时从备份重来
3. **先在副本上试**：在临时 `.docx` 文件上试操作，确认效果后再改目标文件

## 表格必须有的三要素

论文中每一张表都需要：

1. **题注在表格上方**（Caption 样式）：`表X-Y 标题`
2. **引入文字在题注之前**：如"各模型的结果如表4-2所示"
3. **分析文字在表格之后**：解释表中数据的含义

缺少任何一项，读者会感觉表格是"硬塞进去的"。本工具提供题注重排（`renumber_figures`）和三线表样式（`set_table_border`），但不负责内容合理性——你需要自己检查每张表的上下文。

## 不要在目标文档上直接测试

测试会留下残留数据（插入的段落、改写的文字），即使事后清理也容易遗漏。

```python
# ✅ 正确：先备份
editor.save_zip("副本.docx")
# 在副本上测试
# 确认无误后再改目标

# ❌ 危险：直接在目标文档上反复测试
eval "论文.docx"  # 可能留下"测试插入段"等垃圾
```

如果已经污染了目标文档，最安全的做法是 `git checkout` 恢复原始版本再重新操作。

## renumber_figures 只处理 Caption 样式的段落

`renumber_figures` 的正则匹配 `^[表图]\d+[-.]\d+`，但如果正文以"表4-2展示了…"开头也会误匹配。

**修复：** 只处理 `style == "Caption"` 的段落。如果你的题注跑到了正文段落里，先分配样式再重编号。

## _build_index 不会自动重置

`_build_para_index()` 每次调用都会 **追加** 到 `_para_index`，不会清空旧数据。如果你在同一个 eval 会话中多次调用了删除/插入操作（每次触发 `_build_index()`），索引会指数级膨胀。

- 已修复：`_build_para_index` 开头加了 `self._para_index = []`
- `_build_image_index` 和 `_build_table_index` 同理

## SKILL.md 签名必须与 API 一致

SKILL.md 中教用户用的参数签名如果和 `api.py` 不匹配，用户的 eval 脚本会直接崩溃。本次会话修复了以下不匹配：

| SKILL.md 写的 | API 实际的 | 修复 |
|---------------|-----------|------|
| `replace_text(index=, text=)` | `replace_text(by_text=, text=)` | SKILL.md 更新 |
| `insert_table(three_line=True)` | `insert_table(three_line=False)` | SKILL.md 更新 |
| `insert_formula(after=, ...)` | `insert_formula(after_text=, ...)` | API + SKILL.md 更新 |

## 修订模式替代方案

本工具不创建修订标记。如需带修订标记（Track Changes）的修改：

### 方案 A：Word 比较（推荐）

1. `shutil.copy2(src, backup)` 备份原文
2. 用 eval 模式做修改
3. 在 Word 中：审阅 → 比较 → 比较两个版本的文档
4. 接受/拒绝修订

### 方案 B：win32com 脚本

在 Windows 且有 Word 安装的环境下使用。关键模式：

```python
import win32com.client as win32
word = win32.Dispatch("Word.Application")
doc = word.Documents.Open("论文.docx")
doc.TrackRevisions = True
doc.Range(0, 0).Select()
word.Selection.Find.Text = "旧词"
if word.Selection.Find.Execute():
    word.Selection.Delete()
    word.Selection.TypeText("新词")
doc.SaveAs2("输出.docx", FileFormat=16)
```

注意：win32com 不是本工具的依赖，需单独安装 `pywin32`。

## 单段落 TOC 的定位方法

英文目录（TOC）可能存储为单个段落内的多个 run，`search` 命令无法覆盖。
用 `search-xml` 命令搜索底层 XML 文本：

```bash
python cli.py search-xml --query "chapter summary" "论文.docx"
python cli.py search-xml --query "CONTENTS" --context 200 "论文.docx"
```

## PowerShell 下的搜索替代

`search --query "A|B"` 中 `|` 被 PowerShell 拦截。三种解决方式：

1. 分两次搜索
2. 将关键词写入文本文件：`echo A > queries.txt; echo B >> queries.txt` 再 `search --query-file queries.txt`
3. 在 bash/WSL 中运行（如可用）

## 表格插入后索引验证

`insert_table` 和 `replace_table` 依赖固定索引。插入新表后所有后续表索引 +1。
验证当前索引的方法：

```bash
python cli.py read-table-context --index N "论文.docx"
```

先确认题注文本所在段落，用 `after_text` 参数代替索引定位。
