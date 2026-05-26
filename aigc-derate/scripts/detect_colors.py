"""
检测docx中红色/黄色标记文本，输出JSON供后续翻译使用。

用法:
    python detect_colors.py "查重报告.docx"
    python detect_colors.py "查重报告.docx" -o colors.json
    python detect_colors.py "查重报告.docx" --red FF0000 --yellow FFC000
"""
import json, sys, argparse
from docx import Document


def detect_colors(docx_path, output_path=None, red_hex='F12828', yellow_hex='F39800'):
    doc = Document(docx_path)
    RED = red_hex.upper()
    YELLOW = yellow_hex.upper()

    red_paras = {}
    yellow_paras = {}

    for i, para in enumerate(doc.paragraphs):
        red_runs, yellow_runs = [], []
        for run in para.runs:
            try:
                if run.font.color and run.font.color.rgb:
                    c = str(run.font.color.rgb).upper()
                    t = run.text.strip()
                    if not t:
                        continue
                    if c == RED:
                        red_runs.append(t)
                    elif c == YELLOW:
                        yellow_runs.append(t)
            except Exception:
                pass
        if red_runs:
            red_paras[i] = {'text': para.text, 'red_samples': red_runs[:5]}
        if yellow_runs:
            yellow_paras[i] = {'text': para.text, 'yellow_samples': yellow_runs[:3]}

    result = {
        'red_count': len(red_paras),
        'red_paragraphs': red_paras,
        'yellow_count': len(yellow_paras),
        'yellow_paragraphs': yellow_paras
    }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"红色段落: {len(red_paras)}, 黄色段落: {len(yellow_paras)}")
    print(f"红色索引: {sorted(red_paras.keys())}")
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='检测docx中红色/黄色标记文本')
    parser.add_argument('file', help='docx文件路径')
    parser.add_argument('-o', '--output', default='colors.json', help='输出JSON路径')
    parser.add_argument('--red', default='F12828', help='红色hex值（默认F12828）')
    parser.add_argument('--yellow', default='F39800', help='黄色hex值（默认F39800）')
    args = parser.parse_args()

    detect_colors(args.file, args.output, args.red, args.yellow)
