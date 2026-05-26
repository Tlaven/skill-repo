"""
CN→DE→CN往返翻译（强力）。用于红色标记段落。
CN→EN→CN往返翻译（轻量）。用于黄色标记段落。

用法:
    python roundtrip.py colors.json -o pairs.json --route de    # 德文路线
    python roundtrip.py colors.json -o pairs.json --route en    # 英文路线
"""
import json, requests, time, re, random, sys

def translate(text, src, dest):
    if not text.strip():
        return ""
    uid = f"tx{random.randint(10000,99999)}@temp.com"
    url = "https://api.mymemory.translated.net/get"
    params = {'q': text[:450], 'langpair': f"{src}|{dest}", 'de': uid}
    try:
        r = requests.get(url, params=params, timeout=15)
        d = r.json()
        if d['responseStatus'] == 200:
            return d['responseData']['translatedText']
        return None
    except:
        return None

def translate_all(text, src, dest, max_c=400):
    if len(text) <= max_c:
        return translate(text, src, dest)
    sents = re.split(r'(?<=[。！？；\n.!?;])\s*', text)
    chunks, cur = [], ""
    for s in sents:
        if s.strip() and len(cur) + len(s) > max_c:
            if cur:
                chunks.append(cur)
            cur = s
        else:
            cur += s
    if cur.strip():
        chunks.append(cur)
    results = []
    for c in chunks:
        if not c.strip():
            continue
        r = translate(c.strip(), src, dest)
        if r:
            results.append(r)
        time.sleep(0.4)
    return "".join(results) if results else None

def multi_hop(text, hops):
    current = text
    mid_results = []
    for src, dest in hops:
        r = translate_all(current, src, dest)
        if not r:
            return None, mid_results
        current = r
        mid_results.append(r)
        time.sleep(0.4)
    return current, mid_results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='往返翻译降AIGC')
    parser.add_argument('colors_json', help='detect_colors.py的输出JSON')
    parser.add_argument('-o', '--output', default='pairs.json', help='输出pairs.json')
    parser.add_argument('--route', choices=['de', 'en', 'de-en'], default='de',
                        help='翻译路线: de=中德中(强力), en=中英中(轻量), de-en=中德英中(最强)')
    parser.add_argument('--target', choices=['red', 'yellow', 'all'], default='red',
                        help='处理目标: red=仅红色, yellow=仅黄色, all=全部')
    args = parser.parse_args()

    with open(args.colors_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 选择处理哪些段落
    if args.target in ('red', 'all'):
        paras = {int(k): v for k, v in data['red_paragraphs'].items()}
    else:
        paras = {}

    if args.target in ('yellow', 'all'):
        paras.update({int(k): v for k, v in data['yellow_paragraphs'].items()})

    # 翻译路线
    if args.route == 'de':
        hops = [('zh-CN', 'de'), ('de', 'zh-CN')]
    elif args.route == 'en':
        hops = [('zh-CN', 'en'), ('en', 'zh-CN')]
    elif args.route == 'de-en':
        hops = [('zh-CN', 'de'), ('de', 'en'), ('en', 'zh-CN')]

    pairs = {}
    for idx in sorted(paras.keys()):
        text = paras[idx]['text']
        if not text.strip():
            continue
        orig_len = len(text)
        print(f"P{idx} ({orig_len}字): ", end='')
        result, mids = multi_hop(text, hops)
        if result:
            new_len = len(result)
            # 截断检测：翻译结果明显短于原文（<70%）→ 可能被截断
            ratio = new_len / orig_len if orig_len > 0 else 1
            if ratio < 0.7 and orig_len > 50:
                print(f"⚠️ 截断({orig_len}→{new_len}, {ratio:.0%}) ", end='')
            pairs[str(idx)] = result
            print(f"OK -> {new_len}字")
        else:
            # fallback: try CN->EN->CN
            print("DE失败,尝试EN...", end='')
            result, _ = multi_hop(text, [('zh-CN', 'en'), ('en', 'zh-CN')])
            if result:
                pairs[str(idx)] = result
                print(f"OK -> {len(result)}字")
            else:
                print("全部失败")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)

    print(f"\n完成！共翻译 {len(pairs)} 段，输出: {args.output}")
    print("用以下命令写回文档：")
    print(f"  python cli.py replace-batch-by-index --pairs-file {args.output} 论文.docx")

if __name__ == '__main__':
    main()
