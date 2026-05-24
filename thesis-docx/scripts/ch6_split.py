from api import ThesisEditor

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    # Fix heading (remove note)
    editor.replace_text(index=254, text='6.5 实验与结果分析')
    # Fix caption missing space
    editor.replace_text(index=258, text='图6-6 实验环境架构图')
    # Insert subsection headings (back to front)
    editor.insert_paragraph(after=264, text='6.5.4 实验结果与分析', style='heading 3')
    editor.insert_paragraph(after=259, text='6.5.3 实验内容', style='heading 3')
    editor.insert_paragraph(after=258, text='6.5.2 评价指标体系', style='heading 3')
    editor.insert_paragraph(after=255, text='6.5.1 实验环境', style='heading 3')
    editor.save()
    print('OK')
