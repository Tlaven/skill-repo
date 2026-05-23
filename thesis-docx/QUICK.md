# 场景速查 — 我要做 X → 用 Y

## 读

| 场景 | 命令 |
|------|------|
| 全文概况（字数/段落/图表/公式分布） | `read-full` |
| 某节完整内容+格式+图表 | `read-section --title "节名" --deep` |
| 某张表的内容+边框+字体 | `read-table --index N --deep` |
| 全部表概览（位置+形状+表头） | `read-tables` |
| 公式位置+数学内容（OMML） | `read-formulas` |
| 图片列表 | `read-images` |
| 段落定位（章节路径+附近元素） | `read-location --paragraph N` |
| 搜索关键词 | `search --query "关键词"` |
| 搜索写作风格问题 | `search --writing-style` |
| 样式定义 | `extract-rules` |
| 页面设置 | `read-page-setup` |
| 全文纯文字 | `extract-text` |

## 改

| 场景 | 命令 |
|------|------|
| 替换整段 | `replace-text --by-text "旧段" --text "新段"` |
| 段内改一个词 | `replace-inline --by-text "锚定段" --old "旧词" --new "新词"` |
| 改词+同时设格式 | `replace-inline --old X --new Y --bold --font 楷体` |
| 只改格式不改字 | `format-inline --target "子串" --bold` |
| 全文关键词替换 | `replace-batch --pairs '[{"old":"旧","new":"新"}]'` |
| 替换表格数据 | `replace-table --index N --data-file data.json` |
| 删除一段 | `delete-paragraph --by-text "要删的段"` |
| 删除全部批注 | `delete-comments` |
| 清理占位符 | `replace-inline --old "FORMULA_3_1" --delete` |

## 增

| 场景 | 命令 |
|------|------|
| 插入一段 | `insert-paragraph --after-text "锚定" --text "新段"` |
| 批量插入多段 | `write-paragraphs --after TEXT --data JSON` |
| 插入图片 | `insert-image --after-text "锚定" --image fig.png --caption "图3-1 标题"` |
| 替换已有图片 | `replace-image --caption "图3-1 标题" --image new.png` |
| 插入表格 | `insert-table --after-text "锚定" --data-file data.json` |
| 插入公式 | `insert-formula --after N --latex "E=mc^2" --number "(3.1)"` |

## 格式

| 场景 | 命令 |
|------|------|
| 自动分配全部样式 | `assign-styles` |
| 手动设样式 | `set-format --by-text "标题" --style h1` |
| GB 标准字号 | `fix-format --preset gb-academic` |
| 修复页面设置 | `fix-page-setup` |
| 精确设页边距/纸张 | `set-page-setup --width 21 --height 29.7 --margin-top 2.5` |
| 设页眉 | `set-header --text "XX大学毕业论文"` |
| 设页码 | `set-footer --page-number` |
| 套模板格式 | `apply-template --template "学校模板.docx" "论文.docx"` |
| 图编号修正 | `renumber-figures` |

## 验证

验证功能附在 read-*/list-* 命令上，以 `--verify` 参数启用：

| 验证点 | 命令 |
|------|------|
| 页宽/高/边距是否符合 A4 标准 | `read-page-setup --verify` |
| 正文样式异常（字号/行距/缩进） | `read-section --title "节名" --verify` |
| 标题样式未分配（文本像标题但样式不是） | `read-structure --verify` |
| 引用编号一致性（未引用/未定义/顺序） | `list-references --verify` |

## 引用

| 场景 | 命令 |
|------|------|
| 列出正文引用标记 | `list-citations` |
| 列出参考文献列表 | `list-references` |
| 重编号引用 | `renumber-references "论文.docx" -o out.docx` |
| 添加一条引用 | `add-reference --text "[1] 作者. 标题..."` |
| 删除一条引用 | `remove-reference --number 3` |

## 创建与导出

| 场景 | 命令 |
|------|------|
| 新建论文（GB 标准） | `create "论文.docx" --preset gb-academic` |
| 从模板新建 | `create "论文.docx" --from-template "学校模板.docx"` |
| 导出 Markdown | `export-markdown "论文.docx" -o paper.md` |
| 导出图片 | `export-images --output-dir ./images` |
| 导出差异 | `export-diff "旧版.docx" "新版.docx" -o diff.json` |

## 多步操作（≥3 次修改）

不要多次调 CLI。用 api.py 或直接写 Python 脚本，在同一个进程中完成所有操作。脚本保存在 `thesis-docx/scripts/` 下，后续可提炼为正式命令。

```python
from api import ThesisEditor
with ThesisEditor("论文.docx") as editor:
    editor.replace_paragraph(43, "新内容")
    editor.insert_paragraph("新段", after=43)
    editor.save()
```

关键原则：**内容定位**（文本子串匹配段落）代替**硬索引**，防索引漂移。
