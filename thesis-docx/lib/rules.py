"""规则加载 — 从 checker 中抽出，供 fixer 和 checker 共同引用，打破循环依赖"""
from lib.styles import get_default_rules, load_rules_with_defaults


def load_rules(rules_path=None):
    """加载规则配置，返回与 get_default_rules() 兼容的 dict"""
    return load_rules_with_defaults(rules_path)
