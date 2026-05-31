# 格式角色与自定义配置

`fix_format()` 通过角色自动识别段落类型并套用格式标准。

## 角色 → 论文元素映射

| 角色 | 识别方法 | 对应论文元素 |
|------|---------|-------------|
| `body` | 非标题、非图题、非参考文献的正文段落 | 摘要内容、引言、各章节正文、结论等 |
| `heading_1` | `ParagraphInfo.level == 1` | 一级标题（第一章、第二章……） |
| `heading_2` | `ParagraphInfo.level == 2` | 二级标题（1.1、1.2……） |
| `heading_3` | `ParagraphInfo.level == 3` | 三级标题（1.1.1、1.1.2……） |
| `caption` | 文本以 "图/表/Figure/Table" + 编号开头 | 图题、表题、图内文字、表内文字 |
| `reference` | 位于"参考文献"标题之后、非标题的段落 | 参考文献条目 |

## 角色检测优先级

1. 标题级别已知（Heading 1/2/3）→ 直接对应
2. 正文段落以"图 X-Y""表 X.Y" 开头 → caption
3. 正文段落位于 "参考文献" 节内 → reference
4. 其他 → body

## 默认格式标准

| 角色 | 字体 | 字号 | 加粗 | 对齐 | 行距 | 首行缩进 | 段前/段后 |
|------|------|------|------|------|------|---------|----------|
| body | 宋体 | 12pt | ❌ | 两端 | 1.5 倍 | 0.74cm | 0 |
| heading_1 | 黑体 | 16pt | ✅ | 居中 | 1.25 倍 | 无 | 12pt/6pt |
| heading_2 | 黑体 | 14pt | ✅ | 左 | 1.25 倍 | 无 | 6pt/3pt |
| heading_3 | 黑体 | 13pt | ✅ | 左 | 1.25 倍 | 无 | 3pt/3pt |
| caption | 宋体 | 10.5pt | ❌ | 居中 | 1.0 倍 | 无 | 3pt/3pt |
| reference | 宋体 | 10.5pt | ❌ | 两端 | 1.25 倍 | 无 | 0 |

## 自定义配置

传入自定义 dict 覆盖默认标准。只传需要改的角色和字段，没传的用默认值：

```python
from core import SafeDocument

custom = {
    "body": {
        "font_name": "宋体",
        "font_size": 12,
        "bold": False,
        "alignment": "justify",
        "line_spacing": 1.5,
        "line_spacing_rule": "multiple",
        "first_line_indent_cm": 0.74,
        "space_before": 0,
        "space_after": 0,
    },
    "heading_1": {
        "font_name": "黑体",
        "font_size": 16,
        "bold": True,
        "alignment": "center",
        "line_spacing": 1.25,
    },
}

safe = SafeDocument("thesis.docx")
safe.fix_format(config=custom)
```

### 配置字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `font_name` | str | 中文字体（宋体/黑体/楷体/仿宋） |
| `font_name_ascii` | str | ASCII 字体（默认 Times New Roman） |
| `font_size` | float | 字号，pt 值 |
| `bold` | bool | 是否加粗 |
| `italic` | bool | 是否斜体 |
| `alignment` | str | left / center / right / justify |
| `line_spacing` | float | 行距值 |
| `line_spacing_rule` | str | multiple / exact / atLeast |
| `first_line_indent_cm` | float 或 None | 首行缩进 cm，None = 无缩进 |
| `space_before` | float | 段前距 pt |
| `space_after` | float | 段后距 pt |

不存在的角色或角色中缺失的字段自动跳过。
