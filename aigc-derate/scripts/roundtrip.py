"""
逐句往返翻译降 AIGC。每句独立翻译，短于原文 90% 则降级语言重试。

多语言优先级: DE(最强) -> EN(术语友好) -> KO(中等)
句子级长度保护: 翻译结果 < 0.9 倍原文则降级，所有语言都短则保留原文。

用法:
    python roundtrip.py colors.json -o pairs.json --route de
    python roundtrip.py colors.json -o pairs.json --route en
    python roundtrip.py colors.json -o pairs.json --route de --glossary my_terms.json
    python roundtrip.py colors.json -o pairs.json --resume
"""
import json, requests, time, re, random, sys, io, os

# Windows 控制台 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from config import CONFIG, protect_terms, restore_terms, load_glossary
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 中日韩句子分隔符
SENT_SPLIT_RE = re.compile(r'(?<=[。！？；\n.!?;])\s*')


def get_session():
    """构建带自动重试的 requests Session（429/5xx 自动退避重试）。"""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.0,
                  status_forcelist=[429, 500, 502, 503, 504],
                  respect_retry_after_header=True)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


_session = None


def translate(text, src, dest):
    """单次翻译调用，失败返回 None。"""
    global _session
    if not text.strip():
        return ""
    if _session is None:
        _session = get_session()

    uid = CONFIG['email_template'].format(random.randint(10000, 99999))
    params = {'q': text[:450], 'langpair': f"{src}|{dest}", 'de': uid}
    try:
        r = _session.get(CONFIG['api_url'], params=params, timeout=CONFIG['request_timeout'])
        d = r.json()
        if d['responseStatus'] == 200:
            return d['responseData']['translatedText']
        sys.stderr.write(f"  API error ({src}->{dest}): status={d.get('responseStatus')}\n")
        return None
    except (requests.Timeout, requests.ConnectionError, requests.HTTPError,
            json.JSONDecodeError, KeyError) as e:
        sys.stderr.write(f"  translate error ({src}->{dest}): {type(e).__name__}: {e}\n")
        return None


def multi_hop_text(text, hops, glossary=None):
    """多跳翻译链（单段文本），自动保护/还原术语。"""
    protected, term_map = protect_terms(text, glossary)

    current = protected
    for src, dest in hops:
        r = translate(current, src, dest)
        if not r:
            return None, term_map
        current = r
        time.sleep(CONFIG['request_delay'])

    return restore_terms(current, term_map), term_map


def translate_sentence(sentence, cascade, glossary):
    """逐句翻译，按语言优先级级联。短于 0.9 倍则降级，都短则返回原文。

    Args:
        sentence: 单个句子
        cascade: [(lang_code, hops), ...] 按优先级排序
        glossary: 术语保护词汇表

    Returns:
        (translated_sentence, lang_used) - lang_used 为 None 表示保留原文
    """
    min_ratio = CONFIG['sentence_length_ratio']
    orig_len = len(sentence)

    for lang, hops in cascade:
        result, _ = multi_hop_text(sentence, hops, glossary)
        if result:
            new_len = len(result)
            ratio = new_len / orig_len if orig_len > 0 else 1
            if ratio >= min_ratio:
                return result, lang
            # 长度不够，降级到下一个语言
            sys.stderr.write(f"    [{lang}] {orig_len}->{new_len} ({ratio:.0%}), 降级\n")
        time.sleep(CONFIG['request_delay'])

    # 所有语言都不达标，保留原文
    return sentence, None


def translate_paragraph_by_sentences(text, cascade, glossary):
    """逐句翻译整段，每句独立选择最佳语言。返回组装后的段落。"""
    sentences = SENT_SPLIT_RE.split(text)
    sentences = [s for s in sentences if s.strip()]

    if not sentences:
        return text

    results = []
    lang_stats = {}
    for sent in sentences:
        translated, lang = translate_sentence(sent, cascade, glossary)
        results.append(translated)
        lang_stats[lang] = lang_stats.get(lang, 0) + 1

    return ''.join(results), lang_stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description='逐句往返翻译降AIGC（多语言级联）')
    parser.add_argument('colors_json', help='detect_colors.py的输出JSON')
    parser.add_argument('-o', '--output', default='pairs.json', help='输出pairs.json')
    parser.add_argument('--route', choices=['de', 'en', 'de-en'], default='de',
                        help='起始路线: de=德文(默认), en=英文, de-en=三跳')
    parser.add_argument('--target', choices=['red', 'yellow', 'all'], default='red',
                        help='处理目标: red=仅红色, yellow=仅黄色, all=全部')
    parser.add_argument('--glossary', help='自定义术语保护词汇表JSON文件')
    parser.add_argument('--no-glossary', action='store_true', help='禁用术语保护')
    parser.add_argument('--resume', action='store_true',
                        help='断点续跑：跳过已有输出中已翻译的段落')
    args = parser.parse_args()

    # 加载词汇表
    glossary = [] if args.no_glossary else None
    if args.glossary and not args.no_glossary:
        glossary = load_glossary(args.glossary)
        print(f"已加载词汇表: {len(glossary)} 条规则")

    # 构建语言级联：根据 --route 选择起始语言，向后拼接
    full_cascade = CONFIG['language_cascade']
    if args.route == 'de-en':
        # 三跳模式作为首选项，失败则走正常级联
        de_en_hops = [('zh-CN', 'de'), ('de', 'en'), ('en', 'zh-CN')]
        cascade = [('de-en', de_en_hops)] + list(full_cascade)
    else:
        # 找到起始语言在级联中的位置，从该位置开始
        start_idx = 0
        for i, (lang, _) in enumerate(full_cascade):
            if lang == args.route:
                start_idx = i
                break
        cascade = list(full_cascade[start_idx:])

    lang_names = '/'.join(lang for lang, _ in cascade)
    print(f"语言级联: {lang_names} (句子 < {CONFIG['sentence_length_ratio']:.0%} 则降级)")

    # 加载已有结果（--resume 模式）
    existing = {}
    if args.resume and os.path.exists(args.output):
        with open(args.output, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f"断点续跑: 已有 {len(existing)} 段翻译结果")

    with open(args.colors_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 选择处理哪些段落
    paras = {}
    if args.target in ('red', 'all'):
        paras.update({int(k): v for k, v in data['red_paragraphs'].items()})
    if args.target in ('yellow', 'all'):
        paras.update({int(k): v for k, v in data['yellow_paragraphs'].items()})

    pairs = dict(existing) if args.resume else {}
    skipped = []
    total_lang_stats = {}

    for idx in sorted(paras.keys()):
        key = str(idx)
        if key in pairs:
            print(f"P{idx}: 已存在，跳过")
            continue

        text = paras[idx]['text']
        if not text.strip():
            continue

        orig_len = len(text)
        print(f"P{idx} ({orig_len}字): ", end='')

        result, lang_stats = translate_paragraph_by_sentences(text, cascade, glossary)
        new_len = len(result)

        # 累计语言统计
        for lang, count in lang_stats.items():
            total_lang_stats[lang] = total_lang_stats.get(lang, 0) + count

        ratio = new_len / orig_len if orig_len > 0 else 1

        # 整段仍严重截断（< 70%）则跳过
        if ratio < CONFIG['truncation_threshold'] and orig_len > 50:
            skipped.append((idx, orig_len, new_len))
            print(f"严重缩水({orig_len}->{new_len}, {ratio:.0%}), 跳过")
            continue

        pairs[key] = result
        kept = lang_stats.get(None, 0)
        changed = sum(v for k, v in lang_stats.items() if k is not None)
        print(f"OK -> {new_len}字 (改{changed}句/留{kept}句)")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)

    print(f"\n完成! 共翻译 {len(pairs)} 段，输出: {args.output}")

    if total_lang_stats:
        print(f"语言使用统计:")
        for lang, count in sorted(total_lang_stats.items(), key=lambda x: -x[1]):
            label = lang if lang else "保留原文"
            print(f"  {label}: {count} 句")

    if skipped:
        print(f"跳过 {len(skipped)} 段（严重缩水），需手动处理:")
        for idx, orig, new in skipped:
            print(f"  P{idx}: {orig}->{new}字")

    print(f"\n写回文档命令:")
    print(f"  python cli.py replace-batch-by-index --pairs-file {args.output} 论文.docx")


if __name__ == '__main__':
    main()
