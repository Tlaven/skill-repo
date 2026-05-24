from api import ThesisEditor

PCA_BODY = (
    '主成分分析（Principal Component Analysis, PCA）是一种经典的多元统计方法，'
    '由Pearson于1901年提出[17]，其核心思想是通过正交变换将高维数据投影到方差最大的方向上，'
    '从而在保留主要信息的前提下实现降维。给定一组d维样本数据，PCA首先对数据进行中心化处理，'
    '然后计算协方差矩阵，通过对协方差矩阵进行特征值分解得到特征值及对应的特征向量。'
    '选取前k个最大特征值对应的特征向量作为投影矩阵，即可将原始高维数据映射到低维空间。'
    'Jolliffe和Cadima对PCA的理论发展进行了系统综述[18]，指出该方法在数据压缩、特征提取和噪声过滤等领域有着广泛应用。'
    'PCA的降维原理如图2-1所示。'
)

with ThesisEditor(
    r'C:\Projects\company\zw744--JD25340\JD25340 基于大语言模型的人才画像与智能匹配技术研究.docx'
) as editor:
    editor.replace_text(index=69, text=PCA_BODY)
    editor.save()
    print('OK')
