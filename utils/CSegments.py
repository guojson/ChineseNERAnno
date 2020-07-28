# -*- coding: utf-8 -*-
# @Author  : guoxuchao
# @time    : 2020-01-11 10:53
# @File    : CSegments.py
# @Software: PyCharm
# !/usr/bin/python3
# -*- coding:utf-8 -*-
# Author:ChenYuan
import time
import os

import xlrd

from utils.SQLiteTools import ConnectSqlite


class CSegment(object):
    def __init__(self):
        self.question = None
        self.true_index = []
        self.with_user_dict = False
        self.reverse = False
        self.result_reverse = False
        self.MM_result_index = []
        self.RMM_result_index = []
        self.MM_result_list = []
        self.RMM_result_list = []
        self.word_pos_dict = {}
        self.no_words=[]
    def read_user_dict(self, dict_path):
        """
        :param dict_path: 用户定义的词典文件
        :return:
        """
        tic = time.clock()
        word_pos = {}
        if not os.path.exists(dict_path):
            print('该文件不存在')
            assert os.path.exists(dict_path) is True

        excel = xlrd.open_workbook(dict_path)
        sheet = excel.sheets()[0]
        rowNum = sheet.nrows  # sheet行数
        MAX_LENGTH = 0
        for i in range(rowNum):
            data_list = list(sheet.row_values(i))
            word = data_list[0]
            pos = int(data_list[3])
            word_pos[word] = pos
        self.word_pos_dict = word_pos
        self.with_user_dict = True
        toc = time.clock()
        time_clock = toc - tic
        print('\033[1;31;47m')
        print('*' * 50)
        print('*Load user dict:\t', dict_path)
        print('*Load time:\t', time_clock)
        print('*' * 50)
        print('\033[0m')

    def read_user_dict_from_database(self,con):
        """
        :param dict_path: 用户定义的词典文件
        :return:
        """
        tic = time.clock()
        word_pos = {}

        datas=con.fetchall_table('select name,category_id from entitys where deleted=0',True)


        for data_list in datas:
            word = data_list[0]
            pos = int(data_list[1])
            word_pos[word] = pos
        self.word_pos_dict = word_pos
        # toc = time.clock()
        # time_clock = toc - tic
        # print('\033[1;31;47m')
        # print('*' * 50)
        # print('*Load user dict:\t', dict_path)
        # print('*Load time:\t', time_clock)
        # print('*' * 50)
        # print('\033[0m')
        #获取排除词语.
        no_datas=con.fetchall_table('select name from entitys where deleted=3',True)
        for no_data in no_datas:
            self.no_words.append(no_data[0])

        print(self.no_words)
        self.with_user_dict = True

    def read_true_sentence(self, true_result):
        """
        :param true_result: 正确的分词结果
        :return: 分词结果的下表元组列表
        """
        if len(true_result) == 0:
            return []
        else:
            true_list = [t.strip() for t in true_result.split('/')]
            true_index = []
            index = 0
            for t in true_list:
                lth = len(t)
                if index + lth == len(self.question):
                    break
                if self.question[index:index + lth] == t:
                    true_index.append(str((index, index + lth)))
                    index += lth
            return true_index

    def get_true_index(self, result_list):
        """
        :param result_list: 结果列表
        :return: 结果对应的下表列表
        """
        if self.reverse:
            self.reverse = False
            return self.RMM_result_index
        else:
            return self.MM_result_index

    def evaluate(self, true_list, result_list):
        """
        :param true_list: 正确的分词列表
        :param result_list: 算法得到的分词列表
        :return: 三种评价指标：{正确率，召回率，F1-score}
        """
        true_index = self.read_true_sentence(true_list)
        result_index = self.get_true_index(result_list)
        if len(true_index) == 0:
            print('未导入正确结果，不能进行评估')
            assert len(true_index) > 0
        tp = 0
        fp = 0
        fn = 0
        for r, t in zip(result_index, true_index):
            if r in true_index:
                tp += 1
            if r not in true_index:
                fp += 1
            if t not in result_index:
                fn += 1
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        F1 = 2 * precision * recall / (precision + recall)
        evaluate_result = {'Precision': precision, 'Recall': recall, 'F1': F1}

        return evaluate_result

    @staticmethod
    def read_own_dict():
        dict_path = './chineseDic.txt'
        word_pos_dict = {}
        if not os.path.exists(dict_path):
            print('该文件不存在')
            assert os.path.exists(dict_path) is True

        with open(dict_path, 'r')as fp:
            for line in fp:
                line = line.strip()
                word = line.split(',')[0]
                w_pos = line.split(',')[1]
                word_pos_dict[word] = w_pos

        return word_pos_dict

    def MM(self, sentence, lth, pos=False):
        """
        :param sentence: 待分词句子
        :param lth: 正向匹配的最大长度
        :param pos: 结果是否显示词性标注
        """
        self.reverse = False
        self.result_reverse = False
        if lth <= 1:
            print('max_len 不能小于2')
            assert lth > 1
        if len(sentence) == 0:
            print('原句子不能为空')
            assert len(sentence) > 0
        self.question = sentence
        if self.with_user_dict:
            word_pos_dict = self.word_pos_dict
        else:

            word_pos_dict = self.read_own_dict()

        result_list = []
        result_index = []
        max_lth = lth
        index = 0
        index_last = min(index + max_lth,len(sentence))

        length=len(sentence)
        while index <= len(sentence)-1:

            sub=sentence[index:index_last]
            # print(sub)

            if sub in self.no_words:
                index = index_last
                index_last = index + max_lth
            elif sub in word_pos_dict.keys():
                print(sub)
                result_list.append([[index,index_last],sentence[index:index_last],word_pos_dict[sentence[index:index_last]]])
                # result_index.append(str((index, index_last)))
                index = index_last
                index_last = index + max_lth
            else:
                index_last -= 1

            if index_last == index:
                # print(index)
                index = index + 1
                index_last = min(index + max_lth, len(sentence))
        self.MM_result_index = result_index
        self.MM_result_list = result_list

    def RMM(self, sentence, lth, pos=False):
        """
        :param sentence: 待分词句子
        :param lth: 反向匹配的最大长度
        :param pos: 结果是否显示词性标注
        :return:
        """
        self.reverse = True
        self.result_reverse = True
        if lth <= 1:
            print('max_len 不能小于2')
            assert lth > 1
        if len(sentence) == 0:
            print('原句子不能为空')
            assert len(sentence) > 0
        self.question = sentence
        if self.with_user_dict:
            word_pos_dict = self.word_pos_dict
        else:
            word_pos_dict = self.read_own_dict()

        result_list = []
        result_index = []
        max_lth = lth
        index_last = len(sentence)
        index = index_last - max_lth
        while index_last != 0:
            if sentence[index:index_last] in word_pos_dict.keys():
                if pos:
                    result_list.append(sentence[index:index_last] + '/' + word_pos_dict[sentence[index:index_last]])
                else:
                    result_list.append(sentence[index:index_last])
                result_index.append(str((index, index_last)))
                index_last = index
                index = index_last - max_lth
            else:
                index += 1
        result_list.reverse()
        result_index.reverse()
        self.RMM_result_index = result_index
        self.RMM_result_list = result_list

    def get_result(self):
        """
        :return: 返回结果
        """
        if self.result_reverse:
            return self.RMM_result_list
        else:
            return self.MM_result_list

if __name__ == '__main__':
    cut=CSegment()
    cut.read_user_dict_from_database()
    print(cut.word_pos_dict)
