"""命令通用工具"""
import argparse

STRUCTURE_CHANGE_COMMANDS = {'insert-paragraph', 'delete-paragraph', 'write-paragraphs', 'insert-formula', 'insert-formulas', 'insert-table', 'insert-image', 'insert-page-break'}


def add_common_args(parser):
    """添加编辑类命令的通用参数。"""
    parser.add_argument('-o', '--output', help='输出文件路径（默认修改原文件）')
    parser.add_argument('--backup', action='store_true', help='修改前创建带时间戳的备份文件')
    parser.add_argument('--inplace', action='store_true', help=argparse.SUPPRESS)
