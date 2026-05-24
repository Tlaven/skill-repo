"""格式修复命令组"""
from commands.common import add_common_args


def register(subparsers):
    p = subparsers.add_parser('assign-styles', help='自动识别段落角色并分配 Word 样式')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--rules', help='自定义样式规则文件 (YAML)')
    p.add_argument('--preset', help='字号预设 (default|gb-academic)')
    add_common_args(p)

    p = subparsers.add_parser('fix-format', help='综合格式修复')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--rules', help='自定义规则文件 (YAML)')
    p.add_argument('--preset', help='字号预设 (default|gb-academic)')
    add_common_args(p)

    p = subparsers.add_parser('fix-page-setup', help='自动修复页面设置')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--rules', help='自定义规则文件 (YAML)')
    add_common_args(p)

    # 页面布局
    p = subparsers.add_parser('set-page-setup', help='设置页面尺寸和页边距')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--width', type=float, help='页面宽度 (cm)')
    p.add_argument('--height', type=float, help='页面高度 (cm)')
    p.add_argument('--margin-top', type=float, help='上边距 (cm)')
    p.add_argument('--margin-bottom', type=float, help='下边距 (cm)')
    p.add_argument('--margin-left', type=float, help='左边距 (cm)')
    p.add_argument('--margin-right', type=float, help='右边距 (cm)')
    add_common_args(p)

    p = subparsers.add_parser('insert-page-break', help='在指定段落后插入分页符')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--after', type=int, required=True, help='在哪个段落之后插入（索引）')
    add_common_args(p)

    p = subparsers.add_parser('set-header', help='设置页眉')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--text', required=True, help='页眉文字')
    p.add_argument('--font', default='宋体', help='字体名')
    p.add_argument('--size', default='9', help='字号 (pt)')
    add_common_args(p)

    p = subparsers.add_parser('set-footer', help='设置页脚')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--text', help='页脚文字')
    p.add_argument('--page-number', action='store_true', help='插入页码')
    p.add_argument('--align', default='center', help='对齐方式')
    p.add_argument('--font', default='宋体', help='字体名')
    p.add_argument('--size', default='9', help='字号 (pt)')
    add_common_args(p)

    p = subparsers.add_parser('renumber-captions', help='按章节顺序重编图/表编号')
    p.add_argument('file', help='输入 .docx 文件')
    add_common_args(p)

    p = subparsers.add_parser('renumber-figures', help='已弃用，请用 renumber-captions')
    p.add_argument('file', help='输入 .docx 文件')
    add_common_args(p)

    p = subparsers.add_parser('apply-template', help='将学校模板的样式和页面设置应用到现有论文')
    p.add_argument('file', help='目标论文 .docx 文件')
    p.add_argument('--template', required=True, help='学校模板 .docx 文件路径')
    add_common_args(p)
