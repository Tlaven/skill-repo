"""命令通用工具"""
import argparse

STRUCTURE_CHANGE_COMMANDS = {'insert-paragraph', 'delete-paragraph', 'move-paragraph', 'write-paragraphs', 'insert-formula', 'insert-formulas', 'insert-table', 'insert-image', 'insert-page-break', 'set-table-border'}


def add_common_args(parser):
    """添加编辑类命令的通用参数。"""
    parser.add_argument('-o', '--output', help='输出文件路径（默认修改原文件）')
    parser.add_argument('--backup', action='store_true', help='修改前创建带时间戳的备份文件')
    parser.add_argument('--inplace', action='store_true', help=argparse.SUPPRESS)


def register_eval(subparsers):
    """eval 命令 — 用 ThesisEditor 执行 Python 脚本"""
    p = subparsers.add_parser('eval', help='用 ThesisEditor 执行 Python 脚本（editor 变量已注入）')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--script-file', required=True, help='Python 脚本路径（editor 变量可用）')
    add_common_args(p)
