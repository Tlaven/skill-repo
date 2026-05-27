---
name: thesis-docx-cli
description: "CLI command reference for thesis-docx. Covers read commands, eval mode, and escape hatch commands."
type: reference
---

# 论文 DocX CLI 参考

入口：`python cli.py <command> <file> [options]`。所有输出为 JSON。

---

## eval 模式（所有写操作的推荐方式）

```bash
python cli.py eval "论文.docx" --script-file ops.py
```

脚本中 `editor` 变量自动注入（ThesisEditor 实例），无需 import/save。

详见 SKILL.md §eval 模式。

## 读操作

```bash
# 全文地图
python cli.py read-full "论文.docx"
python cli.py read-full --section "节名" "论文.docx"
python cli.py read-full --range 10 30 "论文.docx"

# 章节树
python cli.py read-structure "论文.docx"
python cli.py read-structure --format flat "论文.docx"
python cli.py read-structure --verify "论文.docx"          # +样式异常标注

# 章节内容
python cli.py read-section --title "节名" --deep "论文.docx"
python cli.py read-section --title "节名" --verify "论文.docx"

# 段落
python cli.py read-paragraph --index N --deep "论文.docx"
python cli.py read-paragraphs --start N --end M "论文.docx"

# 搜索
python cli.py search --query "关键词" "论文.docx"
python cli.py search --query "模式" --regex "论文.docx"
python cli.py search --query "内容" --chapter 3 "论文.docx"
python cli.py search --writing-style "论文.docx"

# XML 搜索（覆盖 TOC 字段等 python-docx 盲区）
python cli.py search-xml --query "关键词" "论文.docx"
python cli.py search-xml --query "chapter|summary" --regex "论文.docx"
python cli.py search-xml --query "CONTENTS" --context 120 "论文.docx"
python cli.py search-xml --query "search term" --limit 5 "论文.docx"

# 表格
python cli.py read-tables "论文.docx"
python cli.py read-table --index N --deep "论文.docx"
python cli.py read-table-context --index N "论文.docx"

# 图片
python cli.py read-images "论文.docx"
python cli.py read-image --id rIdN --extract --output-dir ./images "论文.docx"

# 公式
python cli.py read-formulas "论文.docx"
python cli.py read-formulas --summary "论文.docx"

# 统计与验证
python cli.py read-stats "论文.docx"
python cli.py read-page-setup --verify "论文.docx"
python cli.py read-comments "论文.docx"
python cli.py list-references --verify "论文.docx"
python cli.py search-format --target all "论文.docx"
python cli.py detect-revisions "论文.docx"

# 位置定位
python cli.py read-location --paragraph N "论文.docx"

# 导出
python cli.py export-markdown "论文.docx" -o paper.md
python cli.py export-section --title "第3章" "论文.docx" -o ch3.md
python cli.py export-images --output-dir ./images "论文.docx"
python cli.py export-diff "旧版.docx" "新版.docx" -o diff.json

# 提取
python cli.py extract-text "论文.docx" -o full.json
python cli.py extract-text "论文.docx" --section "第3章" -o ch3.json
python cli.py extract-rules "论文.docx" -o rules.yaml
```

## 写操作（仅作为 eval 不够时的补充）

这些命令仍可用，但**推荐优先用 eval 模式**。eval 更安全（无索引漂移、无 PowerShell 引用问题）。

```bash
# 文字替换
python cli.py replace-text --by-text "旧" --text "新" "论文.docx"
python cli.py replace-inline --by-text "锚定" --old "旧" --new "新" "论文.docx"
python cli.py replace-inline --by-text "锚定" --old "占位符" --delete "论文.docx"
python cli.py format-inline --by-text "锚定" --target "子串" --bold "论文.docx"

# 段落操作
python cli.py insert-paragraph --after-text "锚定" --text "新段" "论文.docx"
python cli.py delete-paragraph --by-text "内容" "论文.docx"
python cli.py move-paragraph --by-text "源" --after-text "目标" "论文.docx"

# 插入元素
python cli.py insert-image --after-text "锚定" --image fig.png --caption "图3-1 标题" "论文.docx"
python cli.py insert-table --after-text "锚定" --data-file data.json --caption "表3-1" --three-line "论文.docx"
python cli.py insert-formula --after-text "锚定" --latex "E=mc^2" --number "(3.1)" "论文.docx"
python cli.py insert-formula --after-text "锚定" --latex-file formula.txt --number "(3.2)" "论文.docx"

# 替换已有元素
python cli.py replace-image --caption "图3-1" --image new.png "论文.docx"
python cli.py replace-table --index 2 --data-file data.json "论文.docx"
python cli.py replace-table --by-text "表2.3" --data-file data.json "论文.docx"
python cli.py set-table-border --index 0 --three-line "论文.docx"

# 格式修复
python cli.py fix-format "论文.docx"
python cli.py fix-format --preset gb-academic "论文.docx"
python cli.py fix-page-setup "论文.docx"
python cli.py assign-styles "论文.docx"
python cli.py assign-styles --preset gb-academic "论文.docx"
python cli.py apply-template --template "学校模板.docx" "论文.docx"
python cli.py set-format --by-text "标题" --style h1 "论文.docx"
python cli.py delete-comments "论文.docx"

# 页面布局
python cli.py set-page-setup --width 21 --height 29.7 --margin-top 2.5 --margin-bottom 2.5 --margin-left 2.5 --margin-right 2.5 "论文.docx"
python cli.py set-header --text "标题" "论文.docx"
python cli.py set-footer --page-number "论文.docx"
python cli.py insert-page-break --after-text "锚定" "论文.docx"
python cli.py renumber-captions "论文.docx"

# 引用管理
python cli.py list-citations "论文.docx"
python cli.py add-reference --text "[1] 作者. 标题..." "论文.docx"
python cli.py remove-reference --number 3 "论文.docx"
python cli.py renumber-references "论文.docx" -o out.docx

# 修订
python cli.py accept-revisions --start 10 --end 50 "论文.docx"
python cli.py reject-revisions "论文.docx"

# 创建
python cli.py create "论文.docx" --preset gb-academic
python cli.py create "论文.docx" --from-template "学校模板.docx"
```

## 内容定位参数

| 参数 | 适用命令 | 说明 |
|------|---------|------|
| `--by-text "子串"` | replace-text / replace-inline / delete-paragraph / set-format / format-inline | 按内容定位段落 |
| `--after-text "子串"` | insert-paragraph / insert-image / insert-table / insert-formula / insert-page-break | 内容定位锚定段落 |
| `--text-file path` | replace-text / insert-paragraph | 从文件读取文本（解决 PowerShell 引用问题） |
| `--data-file path` | insert-table / replace-table | 从文件读取 JSON 数据 |
| `--latex-file path` | insert-formula | 从文件读取 LaTeX |

## 通用选项

- `--backup`：修改前创建带时间戳的备份
- `--find-file "子串"`：中文文件名模糊查找
- `--output / -o`：输出到新文件
