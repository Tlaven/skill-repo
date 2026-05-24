"""样式配置中心 — 格式定义、段落分类、样式解析"""
import copy
import re


PAGE_RULES = {
    "width_cm": 21.0,
    "height_cm": 29.7,
    "margin_top_cm": 2.5,
    "margin_bottom_cm": 2.5,
    "margin_left_cm": 2.5,
    "margin_right_cm": 2.5,
}

# deep 模式安全限制
MAX_DEEP_CHARS = 3000
MAX_DEEP_PARAS = 40

# assign-styles 跳过前 N 段（封面/声明区域）
SKIP_FIRST_N_PARAS = 13

_BASE = {
    "font": "Times New Roman",
    "font_east": "宋体",
    "size_pt": 12,
    "bold": False,
    "italic": False,
    "underline": False,
    "color": "000000",
    "alignment": "justify",
    "line_spacing": 1.5,
    "first_line_indent_cm": 0.74,
    "space_before_pt": 0,
    "space_after_pt": 0,
}

STYLE_DEFS = {
    "h1": {
        "font": "Times New Roman", "font_east": "黑体",
        "size_pt": 18, "bold": True, "alignment": "center",
        "line_spacing": None, "first_line_indent_cm": None,
        "space_before_pt": 12, "space_after_pt": 12,
    },
    "h2": {
        "font": "Times New Roman", "font_east": "黑体",
        "size_pt": 14, "bold": True, "alignment": "left",
        "first_line_indent_cm": None,
    },
    "h3": {
        "font": "Times New Roman", "font_east": "黑体",
        "size_pt": 12, "bold": True, "alignment": "left",
        "first_line_indent_cm": None,
    },
    "body": {},
    "caption_figure": {
        "size_pt": 12, "alignment": "center",
        "first_line_indent_cm": None, "bold": False,
    },
    "caption_table": {
        "font": "Times New Roman", "font_east": "黑体",
        "size_pt": 12, "alignment": "center", "bold": True,
        "first_line_indent_cm": None,
    },
    "reference": {
        "size_pt": 10.5, "first_line_indent_cm": None,
    },
    "header": {
        "size_pt": 10.5, "alignment": "center",
        "first_line_indent_cm": None, "line_spacing": None,
    },
    "footer": {
        "size_pt": 9, "alignment": "center",
        "first_line_indent_cm": None, "line_spacing": None,
    },
}

VALID_STYLE_NAMES = list(STYLE_DEFS.keys())

FONT_PRESETS = {
    "default": {},
    "gb-academic": {
        "h1": {"size_pt": 12},
        "h2": {"size_pt": 10.5},
        "h3": {"size_pt": 10.5},
        "body": {"size_pt": 10.5},
        "caption_figure": {"size_pt": 9},
        "caption_table": {"size_pt": 9},
        "reference": {"size_pt": 9},
        "header": {"size_pt": 9},
        "footer": {"size_pt": 9},
    },
}

ROLE_TO_STYLE = {
    "chapter_title":        "h1",
    "section_title":        "h2",
    "subsection_title":     "h3",
    "abstract_zh_title":    "h1",
    "abstract_en_title":    "h1",
    "toc_title":            "h1",
    "reference_title":      "h1",
    "appendix_title":       "h1",
    "acknowledgement_title": "h1",
    "conclusion_title":     "h1",
    "body_text":            "body",
    "abstract_zh_body":     "body",
    "abstract_en_body":     "body",
    "conclusion_body":      "body",
    "acknowledgement_body": "body",
    "appendix_body":        "body",
    "keywords_zh":          "body",
    "keywords_en":          "body",
    "figure_caption":       "caption_figure",
    "table_caption":        "caption_table",
    "reference_entry":      "reference",
    "header":               "header",
    "footer":               "footer",
}

STYLE_NAME_TO_WORD = {
    "h1": "Heading 1", "heading 1": "Heading 1", "Heading 1": "Heading 1", "标题 1": "Heading 1",
    "h2": "Heading 2", "heading 2": "Heading 2", "Heading 2": "Heading 2", "标题 2": "Heading 2",
    "h3": "Heading 3", "heading 3": "Heading 3", "Heading 3": "Heading 3", "标题 3": "Heading 3",
    "body": "Body Text",
    "caption": "Caption", "caption_figure": "Caption", "caption_table": "Caption",
    "reference": "Normal",
    "abstract_zh": "Body Text", "abstract_en": "Body Text",
    "keywords_zh": "Body Text", "keywords_en": "Body Text",
    "toc": "Body Text", "acknowledgement": "Body Text",
    "header": "Header", "footer": "Footer",
}

STYLE_TO_ROLES = {}
for _role, _style in ROLE_TO_STYLE.items():
    STYLE_TO_ROLES.setdefault(_style, []).append(_role)

CLASSIFY_PATTERNS = {
    "chapter_title":        re.compile(r'^[1-9]\s+\S+'),
    "section_title":        re.compile(r'^[1-9]\.\d+\s+\S+'),
    "subsection_title":     re.compile(r'^[1-9]\.\d+\.\d+\s+\S+'),
    "abstract_zh_title":    re.compile(r'^摘\s*要$'),
    "abstract_en_title":    re.compile(r'^ABSTRACT$'),
    "toc_title":            re.compile(r'^目\s*录$'),
    "reference_title":      re.compile(r'^参考文献$'),
    "reference_entry":      re.compile(r'^\[\d+\]'),
    "figure_caption":       re.compile(r'^图\s*\d+[-‐–—.]\d+'),
    "table_caption":        re.compile(r'^表\s*\d+[-‐–—.]\d+'),
    "keywords_zh":          re.compile(r'^关键词[：:]'),
    "keywords_en":          re.compile(r'^Keywords[：:]'),
    "appendix_title":       re.compile(r'^附录'),
    "acknowledgement_title": re.compile(r'^致\s*谢'),
    "conclusion_title":     re.compile(r'^结\s*论$'),
}

CLASSIFY_ORDER = [
    "subsection_title",
    "section_title",
    "chapter_title",
    "abstract_zh_title",
    "abstract_en_title",
    "toc_title",
    "reference_title",
    "appendix_title",
    "acknowledgement_title",
    "conclusion_title",
    "reference_entry",
    "table_caption",
    "figure_caption",
    "keywords_zh",
    "keywords_en",
]

ROLE_TO_WORD_STYLE = {
    "chapter_title":        "Heading 1",
    "section_title":        "Heading 2",
    "subsection_title":     "Heading 3",
    "abstract_zh_title":    "Heading 1",
    "abstract_en_title":    "Heading 1",
    "toc_title":            "Heading 1",
    "reference_title":      "Heading 1",
    "appendix_title":       "Heading 1",
    "acknowledgement_title": "Heading 1",
    "conclusion_title":     "Heading 1",
    "body_text":            "Body Text",
    "abstract_zh_body":     "Body Text",
    "abstract_en_body":     "Body Text",
    "conclusion_body":      "Body Text",
    "acknowledgement_body": "Body Text",
    "appendix_body":        "Body Text",
    "keywords_zh":          "Body Text",
    "keywords_en":          "Body Text",
    "figure_caption":       "Caption",
    "table_caption":        "Caption",
    "reference_entry":      "Reference",
    "header":               "Header",
    "footer":               "Footer",
}


def classify_paragraph(text, index=None, context=None):
    """根据文本内容自动识别段落角色。"""
    if not text or not text.strip():
        return None
    text = text.strip()
    for role in CLASSIFY_ORDER:
        pattern = CLASSIFY_PATTERNS.get(role)
        if pattern and pattern.match(text):
            # 图表标题长度约束：真正的标题不超过 60 字
            # 防止 "表4-1展示了..." 这种正文段落的误匹配
            if role in ('figure_caption', 'table_caption') and len(text) >= 60:
                continue
            return role
    return None


def resolve_style(style_name, overrides=None, rules_path=None, preset=None):
    if style_name in ROLE_TO_STYLE:
        style_name = ROLE_TO_STYLE[style_name]
    if style_name not in STYLE_DEFS:
        raise ValueError(f"未知样式 '{style_name}'，可选: {VALID_STYLE_NAMES}")
    resolved = {k: v for k, v in _BASE.items()}
    named = STYLE_DEFS[style_name]
    none_keys = set()
    for k, v in named.items():
        if v is None:
            none_keys.add(k)
        else:
            resolved[k] = v
    if preset and preset in FONT_PRESETS:
        preset_overrides = FONT_PRESETS[preset].get(style_name, {})
        for k, v in preset_overrides.items():
            if v is not None:
                resolved[k] = v
                none_keys.discard(k)
    if rules_path:
        yaml_rules = _load_yaml_rules(rules_path)
        style_overrides = _extract_style_overrides(yaml_rules, style_name)
        for k, v in style_overrides.items():
            if v is not None:
                resolved[k] = v
                none_keys.discard(k)
    if overrides:
        for k, v in overrides.items():
            if v is not None:
                resolved[k] = v
                none_keys.discard(k)
    for k in none_keys:
        resolved.pop(k, None)
    return resolved


def style_to_font_info(resolved):
    return {
        "font_name": resolved.get("font"),
        "font_name_east": resolved.get("font_east"),
        "font_size": resolved.get("size_pt"),
        "bold": resolved.get("bold"),
        "italic": resolved.get("italic"),
        "underline": resolved.get("underline"),
        "color": resolved.get("color"),
    }


def get_default_rules():
    return {
        "page": dict(PAGE_RULES),
        "headings": {
            "h1": {k: STYLE_DEFS["h1"].get(k, _BASE.get(k))
                   for k in ("font", "font_east", "size_pt", "bold", "alignment")},
            "h2": {k: STYLE_DEFS["h2"].get(k, _BASE.get(k))
                   for k in ("font", "font_east", "size_pt", "bold", "alignment")},
            "h3": {k: STYLE_DEFS["h3"].get(k, _BASE.get(k))
                   for k in ("font", "font_east", "size_pt", "bold", "alignment")},
        },
        "body": {k: STYLE_DEFS["body"].get(k, _BASE.get(k))
                 for k in ("font", "font_east", "size_pt", "line_spacing", "first_line_indent_cm")},
        "caption": {
            "pattern": r"^图\s*\d+-\d+|^表\s*\d+-\d+",
            "font": STYLE_DEFS["caption_figure"].get("font_east", _BASE["font_east"]),
            "size_pt": STYLE_DEFS["caption_figure"].get("size_pt", _BASE["size_pt"]),
            "alignment": STYLE_DEFS["caption_figure"].get("alignment", _BASE["alignment"]),
        },
        "reference": {
            "font": STYLE_DEFS["reference"].get("font_east", _BASE["font_east"]),
            "size_pt": STYLE_DEFS["reference"].get("size_pt", _BASE["size_pt"]),
        },
    }


_LEGACY_STYLE_MAP = {
    "abstract_zh": "body",
    "abstract_en": "body",
    "keywords_zh": "body",
    "keywords_en": "body",
    "toc": "body",
    "acknowledgement": "body",
}
VALID_STYLE_NAMES = list(set(VALID_STYLE_NAMES + list(_LEGACY_STYLE_MAP.keys())))


def _normalize_style_name(style_name):
    if style_name in ROLE_TO_STYLE:
        return ROLE_TO_STYLE[style_name]
    if style_name in _LEGACY_STYLE_MAP:
        return _LEGACY_STYLE_MAP[style_name]
    return style_name


def deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml_rules(path):
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _extract_style_overrides(yaml_rules, style_name):
    if not yaml_rules:
        return {}
    if style_name in yaml_rules and isinstance(yaml_rules[style_name], dict):
        return yaml_rules[style_name]
    old_map = {
        "h1": ("headings", "h1"),
        "h2": ("headings", "h2"),
        "h3": ("headings", "h3"),
        "body": ("body",),
        "caption": ("caption",),
        "caption_figure": ("caption",),
        "caption_table": ("caption",),
        "reference": ("reference",),
    }
    if style_name in old_map:
        path = old_map[style_name]
        node = yaml_rules
        for key in path:
            if isinstance(node, dict):
                node = node.get(key, {})
            else:
                return {}
        return node if isinstance(node, dict) else {}
    return {}


def load_rules_with_defaults(rules_path=None):
    defaults = get_default_rules()
    if not rules_path:
        return defaults
    yaml_rules = _load_yaml_rules(rules_path)
    if not yaml_rules:
        return defaults
    return deep_merge(defaults, yaml_rules)
