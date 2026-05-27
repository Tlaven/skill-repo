"""read-* 命令组"""


def register(subparsers):
    p = subparsers.add_parser('read-structure', help='输出章节树')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--format', choices=['tree', 'flat'], default='tree', help='输出格式')
    p.add_argument('--verify', action='store_true', help='附加样式异常标注（文本像标题但未设样式）')

    p = subparsers.add_parser('read-paragraph', help='输出指定段落')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--index', type=int, required=True, help='段落索引')
    p.add_argument('--with-format', action='store_true', help='输出完整格式')
    p.add_argument('--deep', action='store_true', help='深度模式：章节路径+上下文+附近元素')

    p = subparsers.add_parser('read-paragraphs', help='输出段落范围')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--start', type=int, required=True, help='起始索引')
    p.add_argument('--end', type=int, required=True, help='结束索引')
    p.add_argument('--with-format', action='store_true', help='输出完整格式信息')

    p = subparsers.add_parser('read-section', help='输出章节内容')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--title', help='章节标题（模糊匹配）')
    p.add_argument('--level', type=int, help='标题层级')
    p.add_argument('--index', type=int, help='第N个匹配项 (1-based)')
    p.add_argument('--deep', action='store_true',
                   help='深度模式：展开完整格式/表格/图片/公式（限≤3000字/≤40段）')
    p.add_argument('--verify', action='store_true',
                   help='附加正文格式检查（字号/行距/首行缩进异常）')

    p = subparsers.add_parser('read-image', help='输出图片信息')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--id', required=True, help='图片 rId')
    p.add_argument('--extract', action='store_true', help='提取图片文件')
    p.add_argument('--output-dir', help='提取目录')
    p.add_argument('--deep', action='store_true', help='深度模式：布局+位置+上下文')

    p = subparsers.add_parser('read-images', help='输出所有图片')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('read-table', help='输出表格')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--index', type=int, required=True, help='表格索引')
    p.add_argument('--deep', action='store_true', help='深度模式：边框+字体+位置+上下文')

    p = subparsers.add_parser('read-tables', help='输出所有表格概览')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('read-page-setup', help='输出页面设置')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--verify', action='store_true', help='附加标准值核对（页宽/高/边距 vs A4 2.5cm）')

    p = subparsers.add_parser('read-stats', help='输出文档统计')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('read-formulas', help='列出所有公式（含章节位置和上下文段落；--summary 精简输出）')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--summary', action='store_true', help='精简模式：仅类型/位置/数学概要/所在章节')

    p = subparsers.add_parser('read-location', help='查询段落索引所在的章节路径及附近元素')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--paragraph', type=int, required=True, help='段落索引')

    p = subparsers.add_parser('read-table-context', help='读取表格完整内容（数据+标题+上下文段落+所在章节）')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--index', type=int, required=True, help='表格索引')

    p = subparsers.add_parser('read-comments', help='输出所有批注')
    p.add_argument('file', help='输入 .docx 文件')

    p = subparsers.add_parser('read-full', help='输出论文完整地图（轻量）或展开某一节')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--section', help='展开指定章节的完整内容')
    p.add_argument('--range', nargs=2, type=int, metavar=('START', 'END'),
                   help='展开指定段落范围')

    p = subparsers.add_parser('search-xml', help='搜索底层 XML 文本（覆盖 TOC 字段）')
    p.add_argument('file', help='输入 .docx 文件')
    p.add_argument('--query', '-q', required=True, help='搜索字符串或正则')
    p.add_argument('--regex', action='store_true', help='启用正则模式')
    p.add_argument('--context', '-c', type=int, default=80, help='匹配上下文字符数')
    p.add_argument('--limit', '-l', type=int, default=50, help='最大结果数')
