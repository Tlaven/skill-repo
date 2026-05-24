from api import ThesisEditor

KMEANS_BODY = (
    'K-Means++是最经典的无监督聚类算法之一，由MacQueen于1967年提出[19]。'
    '该算法将n个样本划分为K个簇，通过最小化簇内平方误差和'
    '（Sum of Squared Errors, SSE）来优化聚类结果。'
    '其目标函数定义为各样本到所属簇质心的欧氏距离平方之和，'
    '即SSE等于对K个簇内所有样本与其质心偏差的平方求和。'
    '算法采用迭代优化方式：首先随机初始化K个质心，'
    '然后交替执行分配步骤（将每个样本分配到最近的质心所在簇）和更新步骤'
    '（重新计算各簇质心），直到质心收敛或达到最大迭代次数。'
    '杨俊闯和赵超对K-Means++算法的研究进行了综述[20]，'
    '系统分析了算法的收敛性质、初始质心敏感性及其改进方向。'
)

EMBED_BODY = (
    'Embedding是将（任何类型的）数据转换为向量的过程，'
    'Embedding不仅适用于文本，还可以应用于图像、音频甚至图数据。'
    'Mikolov等人提出的Word2Vec模型[21][22]通过浅层神经网络学习词的分布式表示，'
    '使语义相近的词在向量空间中距离接近。'
    '在此基础上，Le和Mikolov提出了Doc2Vec[23]，'
    '将文档级别的语义信息编码为固定长度的向量。'
    '随着深度学习的发展，Devlin等人提出的BERT模型[24]利用Transformer架构的双向注意力机制，'
    '能够生成富含上下文信息的动态词向量，显著提升了文本表示的质量。'
)

COSINE_BODY = (
    '余弦相似度是衡量两个向量方向一致性的常用指标，'
    '定义为两个向量夹角的余弦值，即两个向量的内积除以各自模长的乘积。'
    '在文本语义匹配中，余弦相似度仅关注向量的方向而忽略其绝对大小，'
    '因而对文本长度差异具有较好的鲁棒性。'
    '李晓等[26]验证了基于向量空间的余弦相似度方法在句子语义相似度计算中的有效性，'
    '结果表明该方法能够较好地捕捉句子间的语义关联。'
)

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    # Step 1: Delete old note-paragraphs (back to front)
    editor.delete_paragraph(index=76)  # 2.4 with note
    editor.delete_paragraph(index=73)  # 2.3 with note
    editor.delete_paragraph(index=70)  # 2.2 with note
    editor.delete_paragraph(index=66)  # 2.1 with note
    # Step 2: Restore lost body texts (indices shifted by -4 total)
    editor.replace_text(index=69, text=KMEANS_BODY)   # was 73
    editor.replace_text(index=71, text=EMBED_BODY)    # was 75
    editor.replace_text(index=73, text=COSINE_BODY)   # was 77
    editor.save()
    print('OK')
