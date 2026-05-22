"""检查命令组"""
from commands.common import add_common_args


def register(subparsers):
    for name, help_text in [
        ('check-headings', '标题格式检查'),
        ('check-body', '正文格式检查'),
        ('check-captions', '图表标题格式检查'),
        ('check-page-setup', '页面设置检查'),
    ]:
        p = subparsers.add_parser(name, help=help_text)
        p.add_argument('file', help='输入 .docx 文件')
        p.add_argument('--rules', help='自定义规则文件 (YAML)')

    p = subparsers.add_parser('check-format', help='综合格式检查（支持 --template 对照模板检查）')
    p.add_argument('file', nargs='?', help='输入 .docx 文件')
    p.add_argument('--rules', help='自定义规则文件 (YAML)')
    p.add_argument('--target', choices=['headings', 'body', 'all'], help='检查目标')
    p.add_argument('--find-file', help='按文件名子串查找文件')
    p.add_argument('--template', metavar='TEMPLATE.docx', help='对照学校模板检查格式一致性')

    p = subparsers.add_parser('check-style', help='AI 写作风格检查')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('check-paragraphs', help='段落长度检查')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--threshold', type=int, default=200, help='超长阈值（默认200字）')
    p.add_argument('--start', type=int, help='起始段落索引')
    p.add_argument('--end', type=int, help='结束段落索引')

    p = subparsers.add_parser('check-placeholders', help='占位符文本检测')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('check-figure-references', help='检查图片引用')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('check-formula-references', help='检查公式前后引用和变量解释')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('check-all', help='全面检查')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--rules', help='自定义规则文件 (YAML)')
    p.add_argument('--threshold', type=int, default=200, help='超长段落阈值')
