from api import ThesisEditor

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    # Delete empty old 1.2.1 paragraphs (back to front to avoid index drift)
    editor.delete_paragraph(index=45)  # deleted body text - now empty
    editor.delete_paragraph(index=44)  # deleted heading - now empty
    editor.save()
    print('OK')
