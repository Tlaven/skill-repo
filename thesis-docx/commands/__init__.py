"""commands/ — CLI 命令定义层，只负责 argparse + 粘合 lib/。"""
from commands.common import STRUCTURE_CHANGE_COMMANDS
from commands import read_cmds, edit_cmds, format_cmds, create_cmds, ref_cmds, export_cmds, extract_cmds


def register_all(subparsers):
    """注册所有命令组。"""
    read_cmds.register(subparsers)
    edit_cmds.register(subparsers)
    format_cmds.register(subparsers)
    create_cmds.register(subparsers)
    ref_cmds.register(subparsers)
    export_cmds.register(subparsers)
    extract_cmds.register(subparsers)
