from api import ThesisEditor

BODY_1 = (
    '大量具备跨领域技能（如机械维修兵掌握编程技术、步兵具备无人机操控经验）'
    '的复合型人才，因受限于僵化的专业、岗位体系，在急需相关技能的任务中处于'
    '"不可见"状态，造成了宝贵的人力资源浪费。'
)

BODY_3 = (
    '当前人员管理侧重于个体档案审查与履历分析，'
    '缺乏从队伍整体层面对人员素质进行量化评估的有效手段，'
    '导致决策者在任务规划和人员调配时难以全面掌握队伍的能力分布与短板状况，'
    '影响了人力资源的宏观配置效率。'
)

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    # Rewrite paras 35-41 with clean text (revisions already accepted above)
    editor.replace_text(index=35, text='（1）人才"隐形"化')
    editor.replace_text(index=36, text=BODY_1)
    editor.replace_text(index=37, text='（2）匹配精度低')
    # Para 38: keep as-is
    editor.replace_text(index=39, text='（3）缺乏对人员队伍整体素质的量化评估')
    editor.replace_text(index=40, text=BODY_3)
    editor.save()
    print('OK')
