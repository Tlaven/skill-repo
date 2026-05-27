"""
共享配置和术语保护机制。

集中所有硬编码值，提供翻译前后的术语保护/还原功能。
"""
import re

CONFIG = {
    # 查重报告颜色标记
    'red_hex': 'F12828',
    'yellow_hex': 'F39800',

    # 翻译 API
    'api_url': 'https://api.mymemory.translated.net/get',
    'email_template': 'tx{:05d}@temp.com',
    'request_timeout': 15,
    'request_delay': 0.4,

    # 分块和阈值
    'chunk_size': 400,
    'truncation_threshold': 0.7,
    'length_diff_threshold': 0.05,

    # 逐句翻译：句子长度低于此比例则降级语言
    'sentence_length_ratio': 0.9,

    # 多语言优先级级联（变化力度从强到弱）
    'language_cascade': [
        ('de',  [('zh-CN', 'de'), ('de', 'zh-CN')]),     # 德文：最强改写
        ('en',  [('zh-CN', 'en'), ('en', 'zh-CN')]),     # 英文：术语友好
        ('ko',  [('zh-CN', 'ko'), ('ko', 'zh-CN')]),     # 韩文：中等改写
    ],
}

# \b 在中文字符旁不生效（中文也是 \w），改用 lookaround 断言
# (?<![A-Za-z]) = 前面不是英文字母, (?![A-Za-z]) = 后面不是英文字母
_LA = r'(?<![A-Za-z])'
_RA = r'(?![A-Za-z])'

# 默认术语保护词汇表：引用标记 + 英文缩写 + CamelCase 标识符
DEFAULT_GLOSSARY = [
    # 引用标记: [1], [2,3], [1，2], [1-3]
    r'\[\d+(?:[,，\-]\d+)*\]',
    # 常见英文缩写（不被翻译）
    _LA + r'(?:CNN|RNN|LSTM|GRU|GAN|GANs|VAE|BERT|GPT|NLP|API|HTTP|HTTPS|GPU|CPU|TPU|'
    r'IoT|IoU|mAP|FPS|TPR|FPR|ROC|AUC|BLEU|ROUGE|F1|SQL|NoSQL|REST|RPC|JSON|XML|'
    r'HTML|CSS|DOM|SDK|IDE|ORM|CRUD|SOTA|NLL|SGD|Adam|ReLU|MLP)' + _RA,
    # CamelCase 标识符 (如 ResNet, VGGNet, TensorFlow)
    _LA + r'[A-Z][a-z]+(?:[A-Z][a-z]+)+' + _RA,
    # 全大写缩写 2-6 字母 (如 BERT, GAN, NLP)
    _LA + r'[A-Z]{2,6}' + _RA,
]


def protect_terms(text, glossary=None):
    """将文本中的术语替换为占位符，返回 (protected_text, term_map)。

    使用单次扫描避免占位符被后续模式匹配。占位符格式 <tp0> 不含大写字母，
    不会被任何默认词汇表模式命中。
    """
    if glossary is None:
        glossary = DEFAULT_GLOSSARY

    # 收集所有匹配：[(start, end, matched_text), ...]
    spans = []
    for pattern in glossary:
        for m in re.finditer(pattern, text):
            spans.append((m.start(), m.end(), m.group(0)))

    # 按位置排序，跳过重叠
    spans.sort()
    merged = []
    last_end = -1
    for start, end, matched in spans:
        if start >= last_end:
            merged.append((start, end, matched))
            last_end = end

    # 从后往前替换，保持前面的索引不变
    term_map = {}
    result = list(text)
    for i, (start, end, matched) in enumerate(reversed(merged)):
        placeholder = f'<tp{len(merged) - 1 - i}>'
        term_map[placeholder] = matched
        result[start:end] = [placeholder]

    return ''.join(result), term_map


def restore_terms(text, term_map):
    """将占位符还原为原始术语。丢失的占位符会打印警告。"""
    restored = text
    missing = []
    for placeholder, original in term_map.items():
        if placeholder in restored:
            restored = restored.replace(placeholder, original)
        else:
            missing.append((placeholder, original))

    if missing:
        import sys
        sys.stderr.write(f"Warning: {len(missing)} term placeholders lost in translation:\n")
        for _, orig in missing[:5]:
            sys.stderr.write(f"  {orig}\n")

    return restored


def load_glossary(path):
    """从 JSON 文件加载自定义词汇表。

    文件格式: ["pattern1", "CNN", "LSTM"]
    普通字符串自动转义为字面匹配，以 \\ 开头的视为原始正则。
    """
    import json
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    patterns = []
    for item in raw:
        item = item.strip()
        if not item:
            continue
        # 以 \\ 开头的是原始正则，否则转义为字面匹配
        if item.startswith('\\\\'):
            patterns.append(item[1:])
        else:
            patterns.append(re.escape(item))
    return patterns


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # 自测
    test = "本文使用CNN[1]和ResNet[2,3]模型，在GPU上运行BERT推理。"
    print(f"原文: {test}")
    protected, term_map = protect_terms(test)
    print(f"保护: {protected}")
    print(f"术语表: {term_map}")
    restored = restore_terms(protected, term_map)
    print(f"还原: {restored}")
    assert restored == test, f"往返不一致!\n  期望: {test}\n  实际: {restored}"
    print("OK - 往返一致")
