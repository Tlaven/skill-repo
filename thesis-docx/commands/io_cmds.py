"""文档 I/O 命令组 — create / export / extract"""


def register(subparsers):
    # create
    p = subparsers.add_parser('create', help='创建空白论文模板或从模板创建')
    p.add_argument('file', help='输出 .docx 文件路径')
    p.add_argument('-o', '--output', help='输出文件路径（覆盖 file 参数）')
    p.add_argument('--preset', help='字号预设 (default|gb-academic)')
    p.add_argument('--from-template', metavar='TEMPLATE.docx', help='从学校模板 .docx 创建（保留样式/页面/页眉页脚）')

    # export
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

    # extract
    p = subparsers.add_parser('extract-text', help='提取文档全文供 LLM 分析')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('-o', '--output', help='输出文件路径 (JSON)')
    p.add_argument('--start', type=int, help='起始段落索引')
    p.add_argument('--end', type=int, help='结束段落索引')
    p.add_argument('--section', help='限定章节（标题名模糊匹配）')

    p = subparsers.add_parser('extract-rules', help='从模板提取格式规则')
    p.add_argument('file', help='输入 .docx 模板文件')
    p.add_argument('-o', '--output', help='输出规则文件路径 (YAML/JSON)')
