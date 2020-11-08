# ChineseNERAnno
Annotation tool for Chinese named entity recognition(中文命名实体标注工具,英文通用)
***

```
|-- ChineseNERAnno          #the name of this tool
    |--configs              # the configuration files for this tool
    |--data                 # the raw and annoted datas
    |--utils                # 
    |--anno_main.py         # the main file for ChineseNERAnno
```
# menu
```
|--文件
   |--打开
   |--设置
   |--保存
|--编辑
   |--控制面板
   |--检测
   |--检测长度
   |--拆分句子
   |--分割数据集
   |--转为实体
   |--转为纯文本
   |--定位
   |--查找和替换
|--格式
   |--BMES
   |--BIOES
   |--分词
```
# operation process
![alt](configs/process.png)
# main windows
![alt](configs/main.png)


# keyboard
控制面板主要用于显示预先定义的实体类别，便于实体划分。具体的实体类别可在“文件-设置”中设置，或在数据表category中设置。 \
![alt](configs/keyboard.png) ![alt](configs/categories.png)

# operation
* run the main file
```
python anno_main.py
```
* open the file
```
'文件-->打开'
```
![alt](configs/Video_2020-08-01_163914.gif)

* label the entity

![alt](configs/Video_2020-08-01_165311.gif)


* export the entities with BIO format

![alt](configs/Video_2020-08-01_170452.gif) \
* the example for the export dataset：
```
甲 B-DRUG
丙 I-DRUG
硫 I-DRUG
磷 I-DRUG
是 O
一 O
种 O
高 O
效 O
､ O
广 O
谱 O
､ O
低 O
毒 O
杀 B-CLA
虫 I-CLA
剂 I-CLA
```



# update

In the future, we will continue to add entity relationship annotation. Other functions continue to improve, please wait patiently
# reference
```
YEDDA: https://github.com/jiesutd/YEDDA.git
```
# Cited
```
@article{GUO2020105830,
title = "Chinese agricultural diseases and pests named entity recognition with multi-scale local context features and self-attention mechanism",
journal = "Computers and Electronics in Agriculture",
volume = "179",
pages = "105830",
year = "2020",
issn = "0168-1699",
doi = "https://doi.org/10.1016/j.compag.2020.105830",
url = "http://www.sciencedirect.com/science/article/pii/S0168169920321207",
author = "Xuchao Guo and Han Zhou and Jie Su and Xia Hao and Zhan Tang and Lei Diao and Lin Li",
keywords = "Chinese agricultural diseases and pests named entity recognition, Corpus, Multi-scale local context features, Convolutional neural networks, Self-attention mechanism",
abstract = "Chinese named entity recognition is a crucial initial step of information extraction in the field of agricultural diseases and pests. This step aims to identify named entities related to agricultural diseases and pests from unstructured texts but presents challenges. The available corpus in this domain is limited, and most existing named entity recognition methods only focus on the global context information but neglect potential local context features, which are also equally important for named entity recognition. To solve the above problems and tackle the named entity recognition task in this paper, an available corpus toward agricultural diseases and pests, namely AgCNER, which contains 11 categories and 34,952 samples, was established. Compared with the corpora in the same field, this corpus has additional categories and more sample sizes. Then, a novel Chinese named entity recognition model via joint multi-scale local context features and the self-attention mechanism was proposed. The original Bi-directional Long Short-Term Memory and Conditional Random Field model (BiLSTM-CRF) was improved by fusing the multi-scale local context features extracted by Convolutional Neural Network (CNN) with different kernel sizes. The self-attention mechanism was also used to break the limitation of BiLSTM-CRF in capturing long-distance dependencies and further improve the model performance. The performance of the proposed model was evaluated on three corpora, namely AgCNER, Resume, and MSRA, which achieved the optimal F1-values of 94.15%, 94.56%, and 90.55%, respectively. Experimental results in many aspects illustrated the effective performance of the proposed model in this paper."
}
```
