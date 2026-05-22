"""create 命令组"""
from commands.common import add_common_args


def register(subparsers):
    p = subparsers.add_parser('create', help='创建空白论文模板或从模板创建')
    p.add_argument('file', help='输出 .docx 文件路径')
    p.add_argument('-o', '--output', help='输出文件路径（覆盖 file 参数）')
    p.add_argument('--preset', help='字号预设 (default|gb-academic)')
    p.add_argument('--from-template', metavar='TEMPLATE.docx', help='从学校模板 .docx 创建（保留样式/页面/页眉页脚）')
