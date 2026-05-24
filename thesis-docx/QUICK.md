# 场景速查 — 先看这里再找 CLI.md

| 场景 | 推荐命令 | 说明 |
|------|---------|------|
| 从头看全文 | `python cli.py read-full "论文.docx"` | 全文地图，含章节/图表/公式标注 |
| 只看某章内容 | `python cli.py read-section --title "第3章" --deep` | 展开章节全部内容 |
| 搜索关键词 | `python cli.py search --query "关键词"` | 支持正则、限定章节、上下文 |
| 替换一段话 | `python cli.py replace-text --by-text "旧段落" --text "新内容"` | 内容定位，不用索引 |
| 改段内几个词 | `python cli.py replace-inline --by-text "锚定段" --old "旧词" --new "新词"` | 保留原有格式 |
| 只改格式不改字 | `python cli.py format-inline --by-text "锚定段" --target "子串" --bold --size 14` | 字体/字号/颜色/加粗 |
| 删除一段 | `python cli.py delete-paragraph --by-text "要删的段落"` | 内容定位 |
| 插一张图片 | `python cli.py insert-image --after-text "锚定" --image fig.png --caption "图3-1 标题"` | 自动约束不超页面 |
| 插入表格 | `python cli.py insert-table --after-text "锚定" --data '[["列1","列2"],["v1","v2"]]'` | JSON 数据或文件 |
| 替换表格 | `python cli.py replace-table --index 2 --data-file data.json` | 按表格索引 |
| 插入公式 | `python cli.py insert-formula --after-text "锚定" --latex "E=mc^2" --number "(3.1)"` | LaTeX 语法 |
| 全文替换 | `python cli.py replace-batch --pairs '[{"old":"旧","new":"新"}]'` | 支持限定章节 |
| 插入新段落 | `python cli.py insert-paragraph --after-text "锚定" --text "新段落" --style body` | 指定样式 |
| 批量写多段 | `python cli.py write-paragraphs --after-text "锚定" --data-file data.json` | 从后往前防漂移 |
| 样式检查 | `python cli.py read-structure --verify "论文.docx"` | 标题跳号/格式异常 |
| 页面检查 | `python cli.py read-page-setup --verify "论文.docx"` | 尺寸+边距 |
| 引用检查 | `python cli.py list-references --verify "论文.docx"` | 未引用/未定义/顺序异常 |
| 格式修复 | `python cli.py fix-format "论文.docx"` | 样式+页面+引用 |
| 套模板样式 | `python cli.py apply-template --template "学校模板.docx" "论文.docx"` | 覆盖学校格式 |

**不确定用哪个参数？** → 回 SKILL.md 看操作类型对照表 → CLI.md 查详细参数。

**所有命令输出 JSON。**
