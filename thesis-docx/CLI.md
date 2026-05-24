# 论文 DocX CLI 命令参考

入口：`python cli.py <command> <file> [options]`。所有输出为 JSON。

> 先看 QUICK.md 按场景找命令，再到本文件确认详细参数。

---

## 了解文档结构 (READ)

```bash
# 全文地图（~3k tokens，含图表公式标注）
python cli.py read-full "论文.docx"

# 展开某一节全文（支持 --range 指定段落范围）
python cli.py read-full --section "节名" "论文.docx"
python cli.py read-full --range 10 30 "论文.docx"

# 章节树（--format tree|flat，默认 tree）
python cli.py read-structure "论文.docx"
python cli.py read-structure --format flat "论文.docx"

# 章节深展开（格式+表格+图片+公式内容，≤3000字）
# 可选：--level 层数 / --index 第N个匹配项
python cli.py read-section --title "节名" --deep "论文.docx"
python cli.py read-section --level 2 --index 1 --deep "论文.docx"

# 段落定位（章节路径+附近元素）
python cli.py read-location --paragraph N "论文.docx"

# 段落详细（含 runs 格式；--with-format 输出完整格式）
python cli.py read-paragraph --index N --deep "论文.docx"
python cli.py read-paragraph --index N --with-format "论文.docx"

# 读某一章段落列表
python cli.py read-section --title "章名" "论文.docx"
python cli.py read-paragraphs --start N --end M "论文.docx"

# 表格完整上下文
python cli.py read-table --index N --deep "论文.docx"

# 表格概览
python cli.py read-tables "论文.docx"

# 表格摘要（标题+数据+所在章节，不含边框/字体明细）
python cli.py read-table-context --index N "论文.docx"

# 图片列表（元数据：位置/尺寸/标题，不提取文件）
python cli.py read-images "论文.docx"

# 图片详情 + 单张提取（--extract 配合 --output-dir）
python cli.py read-image --id rIdN --deep "论文.docx"
python cli.py read-image --id rIdN --extract --output-dir ./images "论文.docx"

# 公式列表（含章节位置和上下文；--summary 精简输出）
python cli.py read-formulas "论文.docx"
python cli.py read-formulas --summary "论文.docx"    # 精简：类型/位置/数学概要/所在章节

# 公式概要（已弃用，请用 read-formulas --summary）
python cli.py list-formulas "论文.docx"

# 关键词/正则/写作风格搜索（--from-file 从文件读取查询）
# --context 指定前后段落数，--limit 限制返回条数
python cli.py search --query "关键词" "论文.docx"
python cli.py search --query "模式" --regex "论文.docx"
python cli.py search --query "内容" --chapter 3 "论文.docx"
python cli.py search --query "关键词" --section "节名" "论文.docx"
python cli.py search --query "关键词" --context 2 --limit 50 "论文.docx"
python cli.py search --writing-style "论文.docx"
python cli.py search --from-file query.txt "论文.docx"

# 按样式搜索
python cli.py search-by-style --style "Body Text" "论文.docx"
```

## 统计与验证

```bash
python cli.py read-stats "论文.docx"                    # 字数/段落/图表/引用统计
python cli.py read-page-setup --verify "论文.docx"      # 页面尺寸+边距+标准值核对
python cli.py read-comments "论文.docx"                  # 批注列表
python cli.py read-structure --verify "论文.docx"        # 章节树+标题样式异常标注
python cli.py read-section --title "节名" --verify "论文.docx"  # 正文格式检查
python cli.py list-references --verify "论文.docx"       # 引用一致性检查
python cli.py search-format --target all "论文.docx"         # 格式一致性检查
python cli.py search-format --target headings "论文.docx"    # 仅检查标题
python cli.py search-format --target body "论文.docx"        # 仅检查正文
```

## 修改文字 (WRITE)

所有命令支持 `--paragraph N`（索引）和 `--by-text "子串"`（内容定位）。

```bash
# 替换整段（支持 --text-file 从文件读入）
python cli.py replace-text --paragraph 43 --text "新内容" "论文.docx"
python cli.py replace-text --by-text "旧段落内容" --text "新内容" "论文.docx"
python cli.py replace-text --by-text "旧段落" --text-file new_content.txt "论文.docx"

# 段内子串替换（保留原有格式）
python cli.py replace-inline --paragraph 43 --old "旧词" --new "新词" "论文.docx"
python cli.py replace-inline --by-text "包含旧词的段落" --old "旧词" --new "新词" "论文.docx"

# 替换+设格式
python cli.py replace-inline --paragraph 43 --old "旧词" --new "新词" \
    --bold true --font-east "楷体" --size 14 --color FF0000 "论文.docx"

# 不改文字，只改格式
python cli.py format-inline --paragraph 43 --target "目标子串" \
    --bold --font-east "黑体" --color 000000 "论文.docx"

# 全文关键词替换（--chapter N 限定章节）
python cli.py replace-batch --pairs '[{"old":"旧","new":"新"}]' "论文.docx"
python cli.py replace-batch --pairs '[{"old":"旧","new":"新"}]' --chapter 3 "论文.docx"

# 按段落索引批量替换
python cli.py replace-batch-by-index --pairs-file pairs.json "论文.docx"
# pairs.json: {"43": "新文本", "49": "新文本"}
```

## 段落操作

```bash
# 插入一段（支持 --text-file 从文件读入）
python cli.py insert-paragraph --after-text "锚定文字" --text "新段" --style body "论文.docx"
python cli.py insert-paragraph --after 43 --text "新段" "论文.docx"
python cli.py insert-paragraph --after-text "锚定" --text-file new_para.txt "论文.docx"

# 批量插入多段（从后往前，防索引漂移；支持 --after-text）
python cli.py write-paragraphs --after 43 --data '[{"text":"第一段","style":"body"},{"text":"第二段","style":"body"}]' "论文.docx"
python cli.py write-paragraphs --after-text "锚定文字" --data-file data.json "论文.docx"

# 删除段落
python cli.py delete-paragraph --paragraph 43 "论文.docx"
python cli.py delete-paragraph --by-text "要删除的段落文字" "论文.docx"
```

## 插入元素

```bash
# 图片
python cli.py insert-image --after-text "锚定" --image "fig.png" --width 12 --caption "图3-1 标题" "论文.docx"

# 替换已有图片
python cli.py replace-image --caption "图3-1 标题" --image "new.png" "论文.docx"

# 表格
python cli.py insert-table --after-text "锚定" --data '[["列1","列2"],["值1","值2"]]' "论文.docx"
python cli.py replace-table --index 2 --data '[["列1","列2"],["值1","值2"]]' "论文.docx"

# 公式（全部 save_zip，可随时插入；支持 --after-text）
python cli.py insert-formulas --json formulas.json "论文.docx"
python cli.py insert-formula --after 50 --latex "E=mc^2" --number "(3.1)" "论文.docx"
python cli.py insert-formula --after-text "锚定文字" --latex "E=mc^2" --number "(3.1)" "论文.docx"

# 删除批注
python cli.py delete-comments "论文.docx"
```

## 格式修复

```bash
python cli.py assign-styles "论文.docx"                  # 样式识别+分配
python cli.py fix-format "论文.docx"                    # 综合修复（样式+页面+引用）
python cli.py fix-page-setup "论文.docx"                # 仅修复页面设置
python cli.py set-format --by-text "标题" --style h1 "论文.docx"        # 手动设样式（单段）
python cli.py set-format --start 10 --end 20 --style h1 "论文.docx"     # 范围模式（多段）
python cli.py set-format --target headings --style h1 "论文.docx"       # 批量目标（headings|body）
python cli.py apply-template --template "学校模板.docx" "论文.docx"     # 套用模板样式
```

## 页面布局

```bash
python cli.py set-page-setup --width 21 --height 29.7 --margin-top 2.5 --margin-bottom 2.5 --margin-left 2.5 --margin-right 2.5 "论文.docx"
python cli.py set-header --text "XX大学毕业论文" "论文.docx"
python cli.py set-footer --page-number "论文.docx"
python cli.py insert-page-break --after-text "章末" "论文.docx"
python cli.py renumber-captions "论文.docx"         # 图/表编号修正（推荐）
python cli.py renumber-figures "论文.docx"          # 已弃用，请用 renumber-captions
```

## 引用管理

```bash
python cli.py list-citations "论文.docx"                 # 正文引用标记
python cli.py list-references "论文.docx"                 # 参考文献列表
python cli.py list-references --verify "论文.docx"       # 引用一致性验证（未引用/未定义/顺序异常）
python cli.py renumber-references "论文.docx" -o out.docx
python cli.py add-reference --text "[1] 作者. 标题..." "论文.docx"
python cli.py remove-reference --number 3 "论文.docx"
```

## 创建

```bash
python cli.py create "论文.docx" --preset gb-academic
python cli.py create "论文.docx" --from-template "学校模板.docx"
```

## 导出

```bash
python cli.py export-markdown "论文.docx" -o paper.md
python cli.py export-section --title "第3章" "论文.docx" -o ch3.md
python cli.py export-images --output-dir ./images "论文.docx"   # 批量提取所有图片到目录
python cli.py export-diff "旧版.docx" "新版.docx" -o diff.json
```

## 提取

```bash
python cli.py extract-text "论文.docx" -o full.json                   # 全文（JSON）
python cli.py extract-text "论文.docx" --start 10 --end 50 -o part.json  # 段落范围
python cli.py extract-text "论文.docx" --section "第3章" -o ch3.json      # 限定章节
python cli.py extract-rules "论文.docx"                                   # 样式定义（字体/字号/行距）
```

## 内容定位参数

| 参数 | 适用命令 | 说明 |
|------|---------|------|
| `--by-text "子串"` | replace-text / replace-inline / delete-paragraph / set-format / format-inline | 按段落实质内容查找 |
| `--after-text "子串"` | insert-paragraph / insert-image / insert-table / insert-page-break / write-paragraphs / insert-formula | 在匹配段落后插入 |
| `--old / --new` | replace-inline | 段内查找替换 |
| `--target` | format-inline | 定位要改格式的子串 |

## 通用选项

- `--backup`：修改前创建带时间戳的备份
- `--find-file "子串"`：中文文件名模糊查找
- `--output / -o`：输出到新文件
- `--from-file path`：搜索内容从文件读取
- `--text-file path`：从文件读取替换/插入文本内容（适用于 `replace-text` / `insert-paragraph`）
- `--data-file path`：从文件读取 JSON 数据（适用于 `insert-table` / `replace-table` / `write-paragraphs`）

## 脚本

`scripts/` 目录包含可复用的独立脚本，CLI 命令无法满足的复杂场景可考虑：

| 脚本 | 功能 |
|------|------|
| `batch_fix.py` / `batch_fix2.py` | 多步批量修复（页面设置/编号/占位符/段落删除） |
| `check_abbrev.py` | 扫描英文简称首次出现是否符合全称规范 |

## 架构参考

```
Document Model:
├── Page Setup（页面尺寸 + 边距）
├── Style Definitions（h1/h2/h3/body/caption/reference）
├── Section Tree（章节树，含层级/字数）
└── Paragraph Array（段落数组，含索引/样式/内容）
```

操作块：READ（无副作用）/ WRITE（段落索引偏移）/ FORMAT（样式变）/ CHECK（无副作用）/ CREATE（全新模型）。

---
