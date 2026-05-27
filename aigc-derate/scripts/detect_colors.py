"""
检测docx中红色/黄色标记文本，输出JSON供后续翻译使用。

用法:
    python detect_colors.py "查重报告.docx"
    python detect_colors.py "查重报告.docx" -o colors.json
    python detect_colors.py "查重报告.docx" --red FF0000 --yellow FFC000
"""
import json, sys, argparse
from docx import Document
from config import CONFIG


def detect_colors(docx_path, output_path=None, red_hex=None, yellow_hex=None):
    if red_hex is None:
        red_hex = CONFIG['red_hex']
    if yellow_hex is None:
        yellow_hex = CONFIG['yellow_hex']

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
            except (AttributeError, TypeError):
                # 部分运行的 color.rgb 不可访问（主题颜色、继承颜色等）
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
    parser.add_argument('--red', default=CONFIG['red_hex'], help=f"红色hex值（默认{CONFIG['red_hex']}）")
    parser.add_argument('--yellow', default=CONFIG['yellow_hex'], help=f"黄色hex值（默认{CONFIG['yellow_hex']}）")
    args = parser.parse_args()

    detect_colors(args.file, args.output, args.red, args.yellow)
