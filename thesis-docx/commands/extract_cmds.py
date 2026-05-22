"""提取命令组"""


def register(subparsers):
    p = subparsers.add_parser('extract-text', help='提取文档全文供 LLM 分析')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('-o', '--output', help='输出文件路径 (JSON)')
    p.add_argument('--start', type=int, help='起始段落索引')
    p.add_argument('--end', type=int, help='结束段落索引')
    p.add_argument('--section', help='限定章节（标题名模糊匹配）')

    p = subparsers.add_parser('extract-rules', help='从模板提取格式规则')
    p.add_argument('file', help='输入 .docx 模板文件')
    p.add_argument('-o', '--output', help='输出规则文件路径 (YAML/JSON)')
