---
name: thesis-docx-lessons
description: Accumulated operational lessons for thesis-docx docx editing. Index-shifting traps, content-based matching, comment cleanup, formula pitfalls.
type: reference
---

# 操作经验手册

## 环境：PowerShell 下 Python stdout 陷阱

**不要用 `python -c "..."` 执行含 Python 代码的命令。** 一律写成 `.py` 脚本文件后用 `python path/to/file.py` 执行。

原因：Python 3.12+ 在 Windows 上检测到 stdout 是管道时启用块缓冲。用 `-c` 模式运行时，进程退出时序可能导致缓冲区在 pipe reader 关闭前没刷出去。`-u`、`PYTHONUNBUFFERED=1`、`PYTHONUTF8=1` 都无效。只有 `print('hello', flush=True)` 和 `.py` 脚本文件可靠。

症状：`python -c "print('hello')"` 输出为空，但 `python script.py` 正常。

## 段落索引漂移

每次 `insert-paragraph` / `delete-paragraph` 都会增删段落，**后续所有索引立即偏移**。

### 安全规则

| 场景 | 安全 | 原因 |
|------|------|------|
| 单次 replace-text / replace-inline | Yes | 不增删段落 |
| 单次 insert-paragraph（用 `--after-text`） | Yes | 内容定位，不用索引 |
| 多次 insert-paragraph（多个 CLI 调用） | **No** | 每次调用间索引漂移 |
| insert-formulas 多个绝对 after | **No** | 内部不调整索引 |
| 任意多次 insert/delete 组合 | **No** | 跨调用索引失效 |

### 正确做法

**优先用内容定位，不用索引：**
- `replace-text --by-text "旧段落" --text "新内容"`
- `delete-paragraph --by-text "内容"`
- `insert-paragraph --after-text "锚定"`

**多步操作（≥3次修改）写脚本：**
用文本子串匹配段落，在同一个 Python 进程内完成所有操作，避免索引漂移。

### Anti-Pattern

```json
// ❌ 批量公式用绝对索引
[{"after": 45, "latex": "..."}, {"after": 52, "latex": "..."}]

// ✓ 连续公式用 "position": "last"
[{"after": 52, "latex": "...", "number": "(2.2)"},
 {"latex": "...", "number": "(2.3)", "position": "last"}]
```

## 文件存放约定

操作过程中产生的临时文件放错位置会污染 skill 目录。约定如下：

| 文件类型 | 存放位置 | 示例 |
|---------|---------|------|
| Python 操作脚本（.py） | `thesis-docx/scripts/` | `scripts/fix_chapter2.py` |
| 图表源文件（.drawio, .json） | 论文项目目录下的 `diagrams/`  | `论文项目/diagrams/fig2-1.drawio`  |
| 图表导出文件（.png, .svg） | 论文项目目录下的 `diagrams/` | `论文项目/diagrams/fig2-1.png` |
| LaTeX 公式临时文件（.txt） | `thesis-docx/scripts/` | `scripts/formula.txt` |

## 手动插入段落后的样式修复

通过 XML 直接插入的段落，样式可能不被 Word 正确识别。

**解法：** 保存后运行 `assign-styles`，自动按文本模式分配 Heading 级别。

## 批注操作

- `read-comments` 的 `selected_text` 可能为 `null`（光标位置批注），用 `paragraph_index` 定位
- `delete-comments` 已自动清理 4 个 XML 文件（`comments.xml` / `commentsExtended.xml` / `commentsIds.xml` / `commentsExtensible.xml`），**不要手工操作**
- 中英文样式名（"标题 1" / "Heading 1"）均已支持

##  图片尺寸约束

`insert-image` 自动约束图片不超出页面：宽度 ≤ 文字区域，高度 ≤ 页面可用高度。
未指定 `--width` 时默认 80%。

## 修订处理顺序

修改带修订标记的段落时，**先接受修订，再改文字**：

```python
# ✅ 正确
editor.accept_revisions(start=35, end=40)  # 先清除修订XML
editor.replace_text(index=35, text='新文字')  # 再设新文本

# ❌ 错误：先 replace_text 再 accept_revisions 会导致文字重复
# replace_text 加的新 runs + accept-revisions 从 <w:ins> 拷贝的内容叠加
```

`replace_text` 现在会自动清除段落内的 `<w:ins>` 和 `<w:del>` 元素，但先 `accept-revisions` 再修改仍然是更安全的做法。

## SVG 图片不受支持

python-docx 不支持 SVG 格式。所有插图必须为 **PNG 或 JPEG**。如有 SVG 源文件，用 draw.io 导出为 PNG（`--scale 2` 保证清晰度）。

## PowerShell 管道符导致公式插入失败

PowerShell 中 `|` 是管道操作符。`--latex "P(A|B)"` 会被解释为管道，导致命令报错。

### 安全替换策略

1. **优先用 `--latex-file`**：将 LaTeX 写入文本文件，用 `--latex-file formula.txt` 传入
2. **或用 JSON 文件**：`insert-formulas --json formulas.json`

### 需避免的字符

除 `|` 外，`>`, `<`, `&`, `;`, `$` 在 PowerShell 中也有特殊含义。传复杂 LaTeX 时始终用文件传入。

## 写操作没有 --dry-run 预览模式

替代策略：

1. **先用搜索确认定位**：`search --query "目标内容"`
2. **加 `--backup`**：每次写操作加 `--backup`，不满意时从备份重来
3. **先在副本上试**：在临时 `.docx` 文件上试操作，确认效果后再改目标文件
