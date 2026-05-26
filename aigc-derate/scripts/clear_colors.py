"""
清除docx中指定颜色的文字标记（设为黑色/自动）。

用法:
    python clear_colors.py "论文.docx"
    python clear_colors.py "论文.docx" --red F12828 --yellow F39800
    python clear_colors.py "论文.docx" --clear-all
"""
import sys, argparse
from docx import Document


def clear_colors(docx_path, red_hex='F12828', yellow_hex='F39800', clear_all=False):
    doc = Document(docx_path)
    RED = red_hex.upper()
    YELLOW = yellow_hex.upper()
    targets = {RED, YELLOW}
    if clear_all:
        targets = None  # clear any non-default color

    cleared = 0
    for para in doc.paragraphs:
        for run in para.runs:
            try:
                if run.font.color and run.font.color.rgb:
                    c = str(run.font.color.rgb).upper()
                    if targets is None or c in targets:
                        run.font.color.rgb = None
                        cleared += 1
            except Exception:
                pass

    doc.save(docx_path)
    return cleared


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='清除docx中红色/黄色文字标记')
    parser.add_argument('file', help='docx文件路径')
    parser.add_argument('--red', default='F12828', help='红色hex值（默认F12828）')
    parser.add_argument('--yellow', default='F39800', help='黄色hex值（默认F39800）')
    parser.add_argument('--clear-all', action='store_true', help='清除所有非黑色文字颜色')
    args = parser.parse_args()

    n = clear_colors(args.file, args.red, args.yellow, args.clear_all)
    print(f"已清除 {n} 处颜色标记")
