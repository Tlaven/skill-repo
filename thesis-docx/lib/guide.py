"""_guide 机制 — 运行时状态提醒，帮助 Agent 避免操作陷阱。

只在运行时状态变化时触发，不投递静态知识（静态知识由文档覆盖）。
"""
from commands.common import STRUCTURE_CHANGE_COMMANDS

WRITE_COMMANDS = {
    'replace-text', 'replace-inline', 'format-inline', 'replace-batch',
    'replace-batch-by-index', 'insert-paragraph', 'write-paragraphs',
    'delete-paragraph', 'move-paragraph', 'set-format',
    'replace-table', 'insert-table', 'insert-image', 'replace-image',
    'set-table-border', 'insert-formula', 'insert-formulas',
    'delete-comments', 'assign-styles', 'fix-format', 'fix-page-setup',
    'set-page-setup', 'set-header', 'set-footer', 'insert-page-break',
    'renumber-captions', 'renumber-figures', 'renumber-references',
    'add-reference', 'remove-reference', 'apply-template',
    'accept-revisions', 'reject-revisions', 'accept-revision', 'reject-revision',
}


def get_guide(context):
    """根据操作上下文返回相关的运行时提醒。

    context 可包含:
        command: str               — 命令名
        is_structure_change: bool  — 是否改变了文档结构
        has_verify_issues: bool    — verify 是否发现问题
        cli_write_count: int       — 连续 CLI 写调用次数

    返回: [{"id": "...", "text": "..."}] 或 None
    """
    hints = []

    # 结构性变更 → 索引漂移警告
    if context.get('is_structure_change', False):
        hints.append({
            "id": "structure_change",
            "text": "段落索引已偏移。后续操作请用 by_text / after_text 内容定位，不要用索引。",
        })

    # verify 发现问题
    if context.get('has_verify_issues', False):
        hints.append({
            "id": "verify_issues",
            "text": "验证发现问题。格式问题可用 `editor.fix_format()` 修复。",
        })

    # 连续 CLI 写调用
    cli_write_count = context.get('cli_write_count', 0)
    if cli_write_count >= 2:
        hints.append({
            "id": "switch_to_api",
            "text": f"已连续 {cli_write_count + 1} 次 CLI 写调用。"
                    "建议切换到 eval 模式，避免多次打开/保存文件和索引漂移。",
        })

    return hints if hints else None
