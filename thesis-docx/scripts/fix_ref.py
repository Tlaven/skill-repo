from api import ThesisEditor

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    editor.replace_text(
        index=64,
        text='第七章总结与展望，总结本文的研究工作，讨论未来研究方向。各章之间的逻辑关系如图1-2所示。'
    )
    editor.save()
    print('OK')
