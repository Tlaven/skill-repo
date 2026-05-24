# thesis-docx — AGENTS.md

## 入口

- **CLI**: `python cli.py <command> <file> [options]`，所有输出 JSON
- **Python API**: `from api import ThesisEditor`（支持 context manager）
- **脚本**: `scripts/` — 独立可复用，以 `sys.path.insert(0, '..')` 引入 `api.py`

## 分层

`lib/`（纯函数，无 argparse）→ `commands/`（argparse 注册）→ `cli.py`（路由）

## 依赖

```
pip install -r requirements.txt  # python-docx, latex2mathml
```

## 核心类

`lib/core.py` → `ThesisDoc`：加载 .docx、构建索引（段落/章节树/图片/表格）、保存。 `save_zip()` 用 lxml 序列化 `document.xml` 回写 zip（不是 `doc.save`）。

## lib/ 结构

```
reader.py         — 结构/段落/章节/统计/页面设置（374行）
reader_loc.py     — read_location（62行）
reader_table.py   — 表格读取 + 边框/字体检测（172行）
reader_media.py   — 图片/公式/批注读取（192行）
reader_full.py    — 全文地图 read-full（236行）
                   ↑ 全部通过 reader.py re-export
editor.py         — 插入/替换/删除段落/表格/图片/文字
fixer.py          — 样式分配/格式修复/模板应用/批注删除
formula.py        — LaTeX→OMML 公式插入
layout.py         — 页面设置/页眉页脚/分页符/图表重编号
reference.py      — 引用收集/重编号/一致性验证
searcher.py       — 文本搜索/写作风格检测
checker.py        — 内部检查函数（被 reader --verify 和 fixer 调用）
styles.py         — 样式定义/段落分类/字号预设/规则加载
rules.py          — 薄封装（打破 checker↔fixer 循环依赖）
utils.py          — 共享工具函数
creator.py        — 创建空白/模板论文
exporter.py       — 导出 markdown/section/images/diff
extractor.py      — 提取文本/样式/页面设置到 JSON/YAML
```

## 关键陷阱

1. **段落索引漂移** — `insert-paragraph` / `delete-paragraph` / `insert-table` / `insert-formula` / `insert-image` / `insert-page-break` / `write-paragraphs` 后索引全变。总是用 `--by-text "子串"` / `--after-text "子串"` 代替 `--paragraph N` / `--after N`。API 版用 `by_text=` / `after_text=`（内部调用 `_resolve_by_text`）
2. **≥3 次 insert/delete 写脚本** — 在同一个 Python 进程内通过 `ThesisEditor` API 完成，不要多次调 CLI
3. **FORMULA_X_X 不会自动清理** — 插入公式后手动 `replace-inline --old "FORMULA_3_1" --delete`
4. **结构修改后重建索引** — API 在所有 `insert_*` / `delete_paragraph` / `write_paragraphs` 之后自动调 `doc._build_index()`。CLI 不会自动重建——它每次重新打开文件
5. **PowerShell 中文乱码** — CLI 的 `_fix_all_string_args` 自动修复 `latin-1→utf-8` 被吞的中文。 `--data-file` 绕过双引号被吞问题

## 样式系统

`lib/styles.py`：STYLE_DEFS 定义 h1-h3 / body / caption / reference / header / footer。段落角色由 `classify_paragraph()` 通过正则匹配（如 `^第[1-9]章`、`^摘\s*要$`）。 `--preset gb-academic` 切换到 GB/T 7713.2-2022 字号（正文 10.5pt）。

## 规则系统

`lib/rules.py` 是薄封装（避免 checker↔fixer 循环依赖）。规则可来自 YAML 文件，`load_rules_with_defaults()` 做 deep merge。

## 测试

无测试文件。 `.pytest_cache/` 存在但无 `tests/` 目录，无 pytest 配置文件。

## scripts/ 参考

`batch_fix.py` 展示推荐模式：`ThesisEditor` → 多次 API 调用 → `_build_index()` → `save()`
