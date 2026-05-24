from api import ThesisEditor

DATA_BODY = (
    '本文设计了面向警务（军队）人员信息的数据模型，将原始CSV数据映射为统一的结构化对象。'
    '数据模型采用字段名映射机制，支持中英文双语字段名的自动识别和转换。'
    '模型的核心字段包括：人员编号（person_id）作为唯一标识，'
    '基本信息字段（姓名、性别、年龄、民族、政治面貌），'
    '职业信息字段（文化程度、任职时间、工作年限、警衔等级、现任职务、部职别），'
    '以及多维度描述字段（自我评价、工作经历、培训经历、任务执行情况、表彰奖励、任职经历、兴趣爱好、家庭成员）。'
    '数据模型通过Pydantic进行字段验证，确保数据的类型安全和完整性。'
    '数据模型的字段结构如图3-3所示，具体的警务人员数据模型主要字段定义如表3-1所示。'
)

# Fix heading: remove diagram note from tracked changes
HEADING_CLEAN = '3.1.1 数据模型设计'

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    editor.replace_text(index=96, text=HEADING_CLEAN)
    editor.replace_text(index=97, text=DATA_BODY)
    editor.save()
    print('OK')
