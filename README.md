# ChineseNERAnno
Annotation tool for Chinese named entity recognition(中文命名实体标注工具,英文通用)
***
#总体架构
```
|-- ChineseNERAnno          #the name of this tool
    |--configs              # the configuration files for this tool
    |--data                 # the raw and annoted datas
    |--utils                # 
    |--anno_main.py         # the main file for ChineseNERAnno
```
#菜单
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
#操作流程
![alt](configs/process.png)
#主窗口
![alt](configs/main.png)


#控制面板
控制面板主要用于显示预先定义的实体类别，便于实体划分。具体的实体类别可在“文件-设置”中设置，或在数据表category中设置。 \
![alt](configs/keyboard.png) ![alt](configs/categories.png)

#操作
运行主程序
```
python anno_main.py
```
打开文件
```
'文件-->打开'
```
![alt](configs/Video_2020-08-01_163914.gif) \
```
标注实体
```
![alt](configs/Video_2020-08-01_165311.gif)

```
选择性导出实体
```
![alt](configs/Video_2020-08-01_163914.gif) \
数据BIO格式显示如下：
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



#更新
在将来，我们还会继续添加实体关系标注功能。其他功能后续不断完善，请耐心等待...

#参考
```
YEDDA: https://github.com/jiesutd/YEDDA.git
```