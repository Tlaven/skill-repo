"""引用命令组"""
from commands.common import add_common_args


def register(subparsers):
    p = subparsers.add_parser('list-citations', help='列出引用标记')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('list-references', help='列出参考文献')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--verify', action='store_true', help='附加引用一致性检查（未引用/未定义/出现顺序异常）')

    p = subparsers.add_parser('renumber-references', help='重编引用号')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('-o', '--output', required=True, help='输出文件路径')

    p = subparsers.add_parser('add-reference', help='添加引用')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--text', required=True, help='参考文献文字')
    p.add_argument('--position', type=int, help='插入位置编号')
    add_common_args(p)

    p = subparsers.add_parser('remove-reference', help='删除引用')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--number', type=int, required=True, help='引用编号')
    add_common_args(p)

    # 公式
    p = subparsers.add_parser('insert-formula', help='插入 LaTeX 公式')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--after', type=int, default=None, help='在该段落索引之后插入')
    p.add_argument('--after-text', help='在此文本的段落后插入（内容定位，优先于 --after）')
    p.add_argument('--latex', help='LaTeX 公式字符串')
    p.add_argument('--latex-file', help='从文件读取 LaTeX 公式（解决 PowerShell 管道符问题）')
    p.add_argument('--number', help='公式编号，如 (4.1)')
    add_common_args(p)

    p = subparsers.add_parser('insert-formulas', help='批量插入公式')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--json', dest='file_json', required=True, help='公式定义 JSON 文件路径')
    add_common_args(p)

    p = subparsers.add_parser('list-formulas', help='列出文档中所有公式')
    p.add_argument('file', help='输入 .docx 文件')
