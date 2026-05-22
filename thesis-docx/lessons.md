---
name: thesis-docx-lessons
description: Accumulated operational lessons for thesis-docx editing. Index-shifting traps, content-based matching, comment cleanup, formula pitfalls.
type: reference
---

# 操作经验手册

## 1. 段落索引漂移

每次 `insert-paragraph` / `delete-paragraph` 都会增删段落，**后续所有索引立即偏移**。

### 安全规则

| 场景 | 安全 | 原因 |
|------|------|------|
| 单次 replace-text / replace-inline | Yes | 不增删段落 |
| 单次 insert-paragraph（用 `--by-text`） | Yes | 内容定位，不用索引 |
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

## 2. 手动插入段落后的样式修复

通过 XML 直接插入的段落，样式可能不被 Word 正确识别。

**解法：** 保存后运行 `assign-styles`，自动按文本模式分配 Heading 级别。

## 3. 批注操作

- `read-comments` 的 `selected_text` 可能为 `null`（光标位置批注），用 `paragraph_index` 定位
- `delete-comments` 需清理 4 个 XML 文件：`comments.xml` / `commentsExtended.xml` / `commentsIds.xml` / `commentsExtensible.xml`
- 中英文样式名（"标题 1" / "Heading 1"）均已支持

## 4. Windows 注意事项

- 不要用 `python -c "多行代码"`（`|| goto :error` 破坏缩进），写成 `.py` 文件执行
- 临时脚本用 `sys.stdout.reconfigure(encoding='utf-8')` 防乱码

## 5. 公式占位符残留（待修）

`FORMULA_X_X` 占位符在 `insert-formula` 后不会被自动清除。

**根因：** `insert-formula` 在段落之后插入公式段落，但不清除原段落中的 `FORMULA_X_X` 文本。

**待修：** `cmd_insert_formula` 和 `cmd_insert_formulas` 中应加入占位符清理逻辑。

## 6. 公式编号右对齐

公式居中 + 编号右对齐：用 `w:tabs` 设置右对齐制表位，编号放在 `m:oMathPara` 外部的 `w:r` 中，前面加 `w:tab`。

## 7. 公式引用检查（已实现）

`check-formula-references` 命令检测：
- 公式前是否有 `如式(X.Y)所示` 引用
- 公式后是否有 `其中，` 变量解释
已集成到 `check-all`。

## 8. 字号预设

`--preset gb-academic` 切换到 GB/T 7713.2-2022 标准字号（正文 10.5pt）。
可用命令：`create` / `assign-styles` / `fix-format`。

## 9. 图片尺寸约束

`insert-image` 自动约束图片不超出页面：宽度 ≤ 文字区域，高度 ≤ 页面可用高度。
未指定 `--width` 时默认 80%。

## 10. assign-styles 误识别（已修）

`table_caption` 和 `figure_caption` 匹配增加 ≥60 字跳过，防止 `"表4-1展示了..."` 正文段落被误判为标题。测试见 `tests/test_styles.py`。

## 11. 三层架构（已实现）

`lib/`（纯函数） + `commands/`（argparse） + `scripts/`（可复用脚本）。
