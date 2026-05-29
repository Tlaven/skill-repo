"""commands/ — CLI 命令定义层，只负责 argparse + 粘合 lib/。"""
from commands.common import STRUCTURE_CHANGE_COMMANDS, register_eval
from commands import read_cmds, edit_cmds, format_cmds, ref_cmds, io_cmds


def register_all(subparsers):
    """注册所有命令组。"""
    read_cmds.register(subparsers)
    edit_cmds.register(subparsers)
    format_cmds.register(subparsers)
    ref_cmds.register(subparsers)
    io_cmds.register(subparsers)
    register_eval(subparsers)
