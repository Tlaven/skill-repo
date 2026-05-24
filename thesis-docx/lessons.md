---
name: thesis-docx-lessons
description: Accumulated operational lessons for thesis-docx docx editing. Index-shifting traps, content-based matching, comment cleanup, formula pitfalls.
type: reference
---

# 操作经验手册

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

## 手动插入段落后的样式修复

通过 XML 直接插入的段落，样式可能不被 Word 正确识别。

**解法：** 保存后运行 `assign-styles`，自动按文本模式分配 Heading 级别。

## 批注操作

- `read-comments` 的 `selected_text` 可能为 `null`（光标位置批注），用 `paragraph_index` 定位
- `delete-comments` 已自动清理 4 个 XML 文件（`comments.xml` / `commentsExtended.xml` / `commentsIds.xml` / `commentsExtensible.xml`），**不要手工操作**
- 中英文样式名（"标题 1" / "Heading 1"）均已支持

##  中文 + PowerShell 编码问题

PowerShell 5.1 默认用 latin-1 编码传递参数，导致命令行中的中文字符乱码。

### 安全规则

- **禁止** `python -c "..."` 内联代码带中文 — 中文字符会被 latin-1 截断，报 `SyntaxError`
- **必须**写独立 `.py` 脚本文件，然后 `python path/to/script.py`
- `--data-file` 是绕过 PowerShell 双引号被吞的推荐方式
- `_fix_all_string_args`（cli.py 内部）会自动修复 latin-1→utf-8 的参数字符串，但仅支持参数变量，不支持内联代码

### 正确做法

```bash
# ❌ 不要 — 中文直接炸
python -c "from lib.core import ThesisDoc; doc = ThesisDoc('中文论文.docx')"

# ✓ 写脚本文件
echo 'from lib.core import ThesisDoc; doc = ThesisDoc("中文论文.docx")' > tmp.py
python tmp.py

# 或直接用 CLI 命令（已内置编码修复）
python cli.py detect-revisions "中文论文.docx"
```

### 例外

`cli.py` 本身在 `main()` 开头有：
```python
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```
所以 CLI 命令输出不会乱码。仅 `python -c` 等直接调用方式受影响。

##  图片尺寸约束

`insert-image` 自动约束图片不超出页面：宽度 ≤ 文字区域，高度 ≤ 页面可用高度。
未指定 `--width` 时默认 80%。
