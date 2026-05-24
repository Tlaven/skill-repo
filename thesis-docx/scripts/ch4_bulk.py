from api import ThesisEditor

HEADING_41 = '4.1 人才画像方案设计'
HEADING_412 = '4.1.2 群体画像与个体画像的关系模型'
HEADING_42 = '4.2 基于PCA与K-Means++的人才聚类方法'

BODY_412 = (
    '群体画像与个体画像之间存在层次化的关联关系。'
    '群体画像是对某一聚类簇内全体成员共性特征的抽象概括，'
    '反映了该群体在能力结构、职业发展阶段和工作特点方面的整体特征。'
    '个体画像则是在群体画像的基础上，结合个体独有的数据'
    '（如具体的任务经历、培训记录、个人评价等）进行个性化补充和细化。'
    '群体画像与个体画像的层次关系如图4-2所示。'
)

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    editor.replace_text(index=128, text=HEADING_41)
    editor.replace_text(index=134, text=HEADING_412)
    editor.replace_text(index=135, text=BODY_412)
    editor.replace_text(index=136, text=HEADING_42)
    editor.save()
    print('OK')
