"""_guide 机制 — 按需投递文档提示，帮助 Agent 正确使用 skill。

只在关键节点触发，避免信号疲劳。
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

VERIFY_COMMANDS = {'read-structure', 'read-section', 'read-page-setup', 'list-references', 'search-format'}


def get_guide(context):
    """根据操作上下文返回相关的提示列表。

    context 可包含:
        command: str        — 命令名
        is_first_write: bool — 是否是本次会话/脚本的第一次写操作
        is_structure_change: bool — 是否改变了文档结构
        has_verify_issues: bool — verify 是否发现问题
        cli_write_count: int — 连续 CLI 写调用次数（仅 CLI 层使用）

    返回: [{"id": "...", "text": "..."}] 或 None
    """
    hints = []
    command = context.get('command', '')
    is_first_write = context.get('is_first_write', False)

    # 第一次写操作 → 定位校准
    if is_first_write:
        hints.append({
            "id": "orientation",
            "text": "本工具是论文文档的结构/格式领域专家，不做内容判断（内容质量由你负责）。"
                    "多步修改建议用 ThesisEditor API 或 `python cli.py eval`（见 SKILL.md §操作方式）。",
        })

    # 结构性变更 → 索引漂移警告
    if context.get('is_structure_change', False):
        hints.append({
            "id": "structure_change",
            "text": "段落索引已偏移。后续操作请用 by_text / after_text 内容定位，不要用索引。"
                    "详见 lessons.md §段落索引漂移。",
        })

    # verify 发现问题
    if context.get('has_verify_issues', False):
        hints.append({
            "id": "verify_issues",
            "text": "验证发现问题。格式问题可用 `editor.fix_format()` 自动修复，"
                    "引用问题见 checklist.md，页边距问题见 lessons.md。",
        })

    # 连续 CLI 写调用
    cli_write_count = context.get('cli_write_count', 0)
    if cli_write_count >= 2:
        hints.append({
            "id": "switch_to_api",
            "text": f"已连续 {cli_write_count + 1} 次 CLI 写调用。"
                    "建议切换到 ThesisEditor API 脚本或 `python cli.py eval`，"
                    "避免多次打开/保存文件和索引漂移。见 SKILL.md §操作方式。",
        })

    return hints if hints else None
