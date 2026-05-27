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
