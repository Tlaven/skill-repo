"""导出命令组"""


def register(subparsers):
    p = subparsers.add_parser('export-markdown', help='导出 Markdown')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('-o', '--output', help='输出文件路径')

    p = subparsers.add_parser('export-section', help='导出章节')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--title', help='章节标题')
    p.add_argument('-o', '--output', help='输出文件路径')

    p = subparsers.add_parser('export-images', help='提取图片')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--output-dir', required=True, help='输出目录')

    p = subparsers.add_parser('export-diff', help='差异报告')
    p.add_argument('file', help='旧版 .docx 文件')
    p.add_argument('file_new', help='新版 .docx 文件')
    p.add_argument('-o', '--output', help='输出文件路径')
