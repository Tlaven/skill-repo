"""创建空白论文模板 — 纯库函数"""
import os
import shutil
from docx.shared import Cm
from lxml import etree
from lib.styles import PAGE_RULES, ROLE_TO_WORD_STYLE, resolve_style
from lib.utils import NSMAP
from lib.fixer import get_or_create_style, configure_style


def create_thesis(doc, output=None, preset=None):
    output_path = output or doc.filepath
    _setup_page(doc)
    _setup_styles(doc, preset)
    _insert_skeleton(doc)
    doc.save(output_path)
    doc.save_zip(output_path)
    return {"output": output_path, "message": "空白论文模板已创建"}


def create_from_template(template_path, output=None):
    """从学校模板 .docx 创建论文（保留原模板的样式、页面设置、页眉页脚）。"""
    output_path = output or template_path.replace('.docx', '_论文.docx')
    if not os.path.exists(template_path):
        return {"error": f"模板文件不存在: {template_path}"}

    # 复制模板到目标路径
    shutil.copy2(template_path, output_path)

    # 打开并清除内容段落（保留样式/设置/页眉页脚）
    from lib.core import ThesisDoc
    doc = ThesisDoc(output_path)
    W = NSMAP["w"]
    body = doc.doc.element.body
    ns_body = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body'
    # 收集所有 p 和 tbl 元素并删除
    to_remove = []
    for child in body:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag in ('p', 'tbl'):
            to_remove.append(child)
    for child in to_remove:
        body.remove(child)

    # 读取模板样式名映射：找到 Heading 1/2/3 和 Body Text 的 style_id
    style_map = {}
    for style in doc.doc.styles:
        if style.type == 1:  # PARAGRAPH
            style_map[style.name] = style.style_id

    _insert_skeleton_from_template(doc, style_map)
    doc.save_zip(output_path)
    return {"output": output_path, "message": f"已基于模板创建论文: {os.path.basename(template_path)}"}


def _insert_skeleton_from_template(doc, style_map):
    """使用模板的实际 style_id 插入骨架段落。"""
    W = NSMAP["w"]
    body = doc.doc.element.body
    xml_space = '{http://www.w3.org/XML/1998/namespace}space'

    h1 = style_map.get("Heading 1", "Heading 1")
    h2 = style_map.get("Heading 2", "Heading 2")
    h3 = style_map.get("Heading 3", "Heading 3")
    bt = style_map.get("Body Text", "Body Text")

    skeleton = [
        (h1, "摘  要"), (bt, "【摘要内容占位】"),
        (bt, "关键词：大语言模型；代码生成；质量评估"),
        (h1, "ABSTRACT"), (bt, "[Abstract placeholder]"),
        (bt, "Keywords: LLM; Code Generation; Quality Assessment"),
        (h1, "目  录"), (bt, "【目录占位】"),
        (h1, "第1章 绪论"), (h2, "1.1 研究背景"), (bt, "【正文占位】"),
        (h2, "1.2 研究目标"), (bt, "【正文占位】"),
        (h1, "第2章 相关工作"), (bt, "【正文占位】"),
        (h1, "第3章 方法"), (bt, "【正文占位】"),
        (h1, "第4章 实验与分析"), (bt, "【正文占位】"),
        (h1, "第5章 结论"), (bt, "【正文占位】"),
        (h1, "参考文献"), (bt, "[1] 【参考文献占位】"),
    ]
    for style_id, text in skeleton:
        p = etree.Element(f'{{{W}}}p')
        pPr = etree.SubElement(p, f'{{{W}}}pPr')
        pStyle = etree.SubElement(pPr, f'{{{W}}}pStyle')
        pStyle.set(f'{{{W}}}val', style_id)
        r = etree.SubElement(p, f'{{{W}}}r')
        t = etree.SubElement(r, f'{{{W}}}t')
        t.set(xml_space, 'preserve')
        t.text = text
        body.append(p)


def _setup_page(doc):
    section = doc.doc.sections[0]
    section.page_width = Cm(PAGE_RULES["width_cm"])
    section.page_height = Cm(PAGE_RULES["height_cm"])
    section.top_margin = Cm(PAGE_RULES["margin_top_cm"])
    section.bottom_margin = Cm(PAGE_RULES["margin_bottom_cm"])
    section.left_margin = Cm(PAGE_RULES["margin_left_cm"])
    section.right_margin = Cm(PAGE_RULES["margin_right_cm"])


def _setup_styles(doc, preset=None):
    needed = set(ROLE_TO_WORD_STYLE.values())
    for style_name in needed:
        style = get_or_create_style(doc.doc, style_name)
        if style is None:
            continue
        role = None
        for r, ws in ROLE_TO_WORD_STYLE.items():
            if ws == style_name:
                role = r
                break
        if role:
            resolved = resolve_style(role, preset=preset)
            configure_style(style, resolved)


def _style_id_for(doc, style_name):
    try:
        return doc.doc.styles[style_name].style_id
    except KeyError:
        return style_name


def _insert_skeleton(doc):
    W = NSMAP["w"]
    body = doc.doc.element.body
    for p in body.findall(f'{{{W}}}p'):
        body.remove(p)
    skeleton = [
        ("Heading 1", "摘  要"),
        ("Body Text", "【摘要内容占位】"),
        ("Body Text", "关键词：大语言模型；代码生成；质量评估"),
        ("Heading 1", "ABSTRACT"),
        ("Body Text", "[Abstract placeholder]"),
        ("Body Text", "Keywords: Large Language Model; Code Generation; Quality Assessment"),
        ("Heading 1", "目  录"),
        ("Body Text", "【目录占位——生成后由 Word 自动更新】"),
        ("Heading 1", "第1章 绪论"),
        ("Heading 2", "1.1 研究背景"),
        ("Body Text", "【正文占位】"),
        ("Heading 2", "1.2 研究目标"),
        ("Body Text", "【正文占位】"),
        ("Heading 1", "第2章 相关工作"),
        ("Body Text", "【正文占位】"),
        ("Heading 1", "第3章 方法"),
        ("Body Text", "【正文占位】"),
        ("Heading 1", "第4章 实验与分析"),
        ("Body Text", "【正文占位】"),
        ("Heading 1", "第5章 结论"),
        ("Body Text", "【正文占位】"),
        ("Heading 1", "参考文献"),
        ("Body Text", "[1] 【参考文献占位】"),
    ]
    for style_name, text in skeleton:
        style_id = _style_id_for(doc, style_name)
        p = _make_paragraph(style_id, text)
        body.append(p)


def _make_paragraph(style_id, text):
    W = NSMAP["w"]
    xml_space = '{http://www.w3.org/XML/1998/namespace}space'
    p = etree.Element(f'{{{W}}}p')
    pPr = etree.SubElement(p, f'{{{W}}}pPr')
    pStyle = etree.SubElement(pPr, f'{{{W}}}pStyle')
    pStyle.set(f'{{{W}}}val', style_id)
    r = etree.SubElement(p, f'{{{W}}}r')
    t = etree.SubElement(r, f'{{{W}}}t')
    t.set(xml_space, 'preserve')
    t.text = text
    return p
