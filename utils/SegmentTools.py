# -*- coding: utf-8 -*-
# @Author  : guoxuchao
# @time    : 2019-12-16 20:35
# @File    : SegmentTools.py
# @Software: PyCharm
import jieba
import jieba.posseg as pseg
from openccpy.opencc import *
# jieba.load_userdict('../configs/lexicon.txt')

# test_sent = (
# "李小福是创新办主任也是云计算方面的专家; 什么是八一双鹿\n"
# "例如我输入一个带“韩玉赏鉴”的标题，在自定义词库中也增加了此词为N类\n"
# "「台中」正確應該不會被切開。mac上可分出「石墨烯」；此時又可以分出來凱特琳了。"
# )

# jieba.add_word('创新办主任')
# jieba.add_word('云计算')
# jieba.add_word('八一双鹿')

with open('../demotext/水稻玉米小麦大豆大麦.txt(1).pre','r',encoding='utf-8') as f:
    for line in f.readlines():
       print(line)




