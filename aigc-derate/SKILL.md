---
name: aigc-derate
description: "Use when the user mentions 降重, AIGC, 查重, 标红, detect_colors, roundtrip, clear_colors, check_length_diff, run_all, or any .docx file that is a 查重报告/标红版/redundancy-check report"
---

# AIGC 降重 / 查重降重 Skill

## 定位

与 `editing-thesis-docx` skill 配合使用：
- `editing-thesis-docx`：负责文档的读写、格式修复、样式分配
- `aigc-derate`：负责文本改写降低 AIGC 检测率和查重率

## 目录结构

```
~/.claude/skills/aigc-derate/
├── SKILL.md                      ← 本文件
├── AIGC降低经验.md                ← 方法论 + 策略 + 工作流
└── scripts/
    ├── config.py                 ← 共享配置 + 术语保护机制
    ├── detect_colors.py          ← 检测docx中红/黄色标记文本
    ├── roundtrip.py              ← CN→DE→CN / CN→EN→CN 往返翻译（含术语保护）
    ├── clear_colors.py           ← 清除docx中红/黄色文字标记为黑色
    ├── check_length_diff.py      ← 比较改写前后段落字数偏差
    └── run_all.py                ← 端到端编排脚本
```

## 核心原则

1. **AIGC 检测器看的是深层统计特征**（句长方差、段落模板、句式多样性），不是表层词汇
2. **查重降重改的是标记句子/短语**，不是整段重写
3. **段落长度不能缩**：逐句翻译，每句独立判断长度，短于 90% 自动降级语言
4. **声明等法律文本不能翻译改动**，需恢复原文
5. **术语自动保护**：翻译时引用标记 `[1]`、英文缩写（CNN/GPU 等）、CamelCase 标识符自动保留
6. **多语言级联**：DE（最强改写）→ EN（术语友好）→ KO（中等），句子级自动选择最佳语言

## 快速开始（端到端）

```bash
# 一键运行全流程（自动串联：检测→翻译→写回→复查→清色）
python run_all.py --report "查重报告.docx" --thesis "论文.docx" --route de --target red

# 断点续跑（中断后可恢复）
python run_all.py --resume run_state.json

# 自定义术语保护
python run_all.py --report "查重报告.docx" --thesis "论文.docx" --glossary my_terms.json
```

## 分步工作流

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

## 逐句翻译 + 多语言级联

核心防缩水机制：段落按句拆分，每句独立翻译并检查长度。

**工作方式：**
1. 段落按 `。！？；` 拆分为句子
2. 每句按语言优先级翻译：CN→DE→CN（最强）→ CN→EN→CN → CN→KO→CN
3. 翻译后长度 < 原文 90% → 自动降级到下一个语言重试
4. 所有语言都不达标 → 保留原文不动
5. 段落重组后整体仍 < 70% → 跳过该段，标记手动处理

**效果：** 不再有"整段翻译后字数大幅缩水"的问题。每句都有独立保护，保留原文是最终保底。

## 术语保护

翻译时自动保护以下内容不被翻译改动：
- **引用标记**：`[1]`, `[2,3]`, `[1-3]` 等格式
- **英文缩写**：CNN, RNN, LSTM, GAN, BERT, GPU, API 等
- **CamelCase 标识符**：ResNet, TensorFlow, VGGNet 等

自定义术语文件（JSON 格式）：
```json
[
  "PyTorch",
  "Faster R-CNN",
  "\\b\\d+\\.\\d+%\\b"
]
```

普通字符串按字面匹配，以 `\\` 开头的视为正则表达式。

用法：
```bash
python roundtrip.py colors.json -o pairs.json --route de --glossary my_terms.json
```

禁用术语保护：`--no-glossary`

## 翻译 API 注意事项

- MyMemory 免费版每日 ~1000 次请求，500 字符/次
- 已内置自动重试（429/5xx 自动退避重试 3 次）
- HTTP 429 后换 email 参数绕过配额
- 截断（翻译结果 < 70% 原文长度）自动重试，仍失败则跳过并记录
- `--resume` 可跳过已翻译段落，断点续跑

## 脚本参考

| 脚本 | 用法 |
|------|------|
| `config.py` | 共享配置（颜色、API、阈值），无需直接运行。`python config.py` 可自测术语保护 |
| `detect_colors.py` | `python detect_colors.py "查重报告.docx" -o colors.json [--red F12828] [--yellow F39800]` |
| `roundtrip.py` | `python roundtrip.py colors.json -o pairs.json --route de/en/de-en --target red/yellow/all [--glossary FILE] [--no-glossary] [--resume]` |
| `clear_colors.py` | `python clear_colors.py "论文.docx" [--red F12828] [--yellow F39800] [--clear-all]` |
| `check_length_diff.py` | `python check_length_diff.py "备份.docx" "论文.docx" [--threshold 0.05] [--json diff.json]` |
| `run_all.py` | `python run_all.py --report "查重报告.docx" --thesis "论文.docx" [--route de] [--target red] [--glossary FILE] [--resume]` |

## 参考文件

- [AIGC降低经验.md](AIGC降低经验.md) — 方法论、降重策略、检测器特征分析、常见问题 Fix 清单、关键教训
- [scripts/](scripts/) — 所有可执行脚本的实现源码
