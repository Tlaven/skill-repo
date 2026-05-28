---
name: thesis-docx-cli
description: "CLI command reference for thesis-docx. Read commands and eval mode entry point."
type: reference
---

# 论文 DocX CLI 参考

入口：`python cli.py <command> <file> [options]`。所有输出为 JSON。

---

## eval 模式（所有写操作）

```bash
python cli.py eval "论文.docx" --script-file ops.py
```

脚本中 `editor` 变量自动注入（ThesisEditor 实例），无需 import/save。

方法签名和操作提示见 **API.md**。

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

## 通用选项

- `--backup`：修改前创建带时间戳的备份
- `--find-file "子串"`：中文文件名模糊查找
- `--output / -o`：输出到新文件
