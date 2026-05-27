"""eval 命令 — 用 ThesisEditor 执行 Python 脚本"""
from commands.common import add_common_args


def register(subparsers):
    p = subparsers.add_parser('eval', help='用 ThesisEditor 执行 Python 脚本（editor 变量已注入）')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--script-file', required=True, help='Python 脚本路径（editor 变量可用）')
    add_common_args(p)
