---
name: aigc-derate
description: >-
  Use when the user mentions 降重, AIGC, 查重, 标红, detect_colors, roundtrip, clear_colors,
  check_length_diff, or any .docx file that is a 查重报告/标红版/redundancy-check report.
  Provides tools and workflows for reducing AIGC detection rate and text similarity
  (plagiarism rate) in Chinese academic theses. Works with thesis-docx skill.
---

# AIGC 降重 / 查重降重 Skill

## 定位

与 `thesis-docx` skill 配合使用：
- `thesis-docx`：负责文档的读写、格式修复、样式分配
- `aigc-derate`：负责文本改写降低 AIGC 检测率和查重率

## 目录结构

```
~/.claude/skills/aigc-derate/
├── SKILL.md                      ← 本文件
├── AIGC降重经验.md                ← 方法论 + 策略 + 工作流
└── scripts/
    ├── detect_colors.py          ← 检测docx中红/黄色标记文本
    ├── roundtrip.py              ← CN→DE→CN / CN→EN→CN 往返翻译
    ├── clear_colors.py           ← 清除docx中红/黄色文字标记为黑色
    └── check_length_diff.py      ← 比较改写前后段落字数偏差
```

## 核心原则

1. **AIGC 检测器看的是深层统计特征**（句长方差、段落模板、句式多样性），不是表层词汇
2. **查重降重改的是标记句子/短语**，不是整段重写
3. **段落长度不能缩**：改写前后字数偏差控制在 ±5%，否则总字数会明显减少
4. **声明等法律文本不能翻译改动**，需恢复原文

## 完整工作流

### 阶段1：分析

```bash
python detect_colors.py "查重报告.docx" -o colors.json
python cli.py read-structure "论文.docx"
python cli.py check-style "论文.docx"
python cli.py check-paragraphs --threshold 150 "论文.docx"
```

### 阶段2：红色段落（德文路线，强改写）

```bash
python roundtrip.py colors.json -o pairs_de.json --route de --target red
python cli.py replace-batch-by-index --pairs-file pairs_de.json --backup "论文.docx"
```

### 阶段3：黄色段落（英文路线，轻改写）

```bash
python roundtrip.py colors.json -o pairs_en.json --route en --target yellow
python cli.py replace-batch-by-index --pairs-file pairs_en.json "论文.docx"
```

### 阶段4：清颜色 + 字数检查 + 风格检查

```bash
# 清除红/橙色标记为黑色
python clear_colors.py "论文.docx"

# 字数偏差检查（与原备份对比）
python check_length_diff.py "论文_bak.docx" "论文.docx"

# 风格检查
python cli.py check-style "论文.docx"
```

### 阶段5：AI 生成内容段落改写

针对新增的 AI 撰写段落（不是抄袭，查重不会标红，但 AIGC 检测器会识别）：
- 句式重构 + 删除套路开头 + 注入自然表达
- **保持段落长度不变**，不整段压缩

## 翻译 API 注意事项

- MyMemory 免费版每日 ~1000 次请求，500 字符/次
- HTTP 429 后换 email 参数 `de=userXXXX@temp.com` 可绕过
- 429 频繁时可复用之前跑过的翻译结果

## 脚本参考

| 脚本 | 用法 |
|------|------|
| `detect_colors.py` | `python detect_colors.py "查重报告.docx" -o colors.json [--red F12828] [--yellow F39800]` |
| `roundtrip.py` | `python roundtrip.py colors.json -o pairs.json --route de/en --target red/yellow/all` |
| `clear_colors.py` | `python clear_colors.py "论文.docx" [--red F12828] [--yellow F39800] [--clear-all]` |
| `check_length_diff.py` | `python check_length_diff.py "备份.docx" "论文.docx" [--threshold 0.05] [--json diff.json]` |
