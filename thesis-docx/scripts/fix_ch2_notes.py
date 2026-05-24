from api import ThesisEditor

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    # Delete standalone diagram note paragraph
    editor.delete_paragraph(index=65)
    # Fix headings with diagram notes mixed in
    editor.replace_text(index=67, text='2.1 主成分分析（PCA）')
    editor.replace_text(index=71, text='2.2 聚类算法')
    editor.replace_text(index=74, text='2.3 Embedding技术')
    editor.replace_text(index=77, text='2.4 语义相似度度量技术')
    editor.save()
    print('OK')
