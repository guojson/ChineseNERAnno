#coding=utf8
import io
import sys

import jieba


from utils.SQLiteTools import ConnectSqlite
import random

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') #改变标准输出的默认编码
if __name__ == '__main__':
    # filepath='../demotext/水稻玉米小麦大豆大麦.txt.pre'
    # # with open(filepath+'.pre','a',encoding='utf-8') as f2:
    # with open(filepath,'r',encoding='utf-8') as f:
    #     for abstrct in f:
    #         print(abstrct)
    #         abstrct=abstrct.strip()
    #         if abstrct.startswith('"'):
    #             abstrct=abstrct[1:-1]
    #             print(abstrct)
    #             if abstrct.startswith('<正>'):
    #                 abstrct=abstrct[3:].strip()
    #                 abstrct=abstrct.replace(' ','')
    #                 abstrct = abstrct.replace('""', '')
    #                     # f2.write(abstrct+'\n')

    # con=ConnectSqlite()
    # path='../configs/total_dict.utf8'
    #
    # with open(path,'r',encoding='utf8') as f:
    #       index=1
    #       for line in f:
    #         line=line.strip().replace('\n','')
    #         data=line.split(' ')
    #         data = str(index)+",'"+data[0]+"','"+data[1]+"'"
    #         print('insert into lexicons(id,lexicon,categoryone) values (%s)' %data)
    #         con.insert_update_table('insert into lexicons(id,lexicon,categoryone) values (%s)' %data)
    #         index+=1
    # sql="select count(*) from lexicons where lexicon='"
    # with open('../configs/lexicon.txt','w',encoding='utf-8') as f2:
    #     with open('../configs/sougou.txt','r',encoding='GBK') as f:
    #         lines=f.readlines()
    #         for line in lines:
    #             word=line.strip().split(' ')[1]
    #             data=con.fetchall_table(sql + word + "';")
    #
    #             if data[0][0]==0:
    #                 print(word)
    #                 f2.write(word + '\n')
    #     datas = con.fetchall_table('''select lexicon from lexicons''')
    #     for index in range(len(datas)):
    #         print(datas[index][0])
    #         f2.write(datas[index][0]+'\n')
    #
    #
    #
    #
    #
    # # seg_list = jieba.cut("我来到北京清华大学", cut_all=False)
    # # print("精准模式: " + "/ ".join(seg_list))  # 精确模式

    with open('../demotext/水稻玉米小麦大豆大麦.txt','r',encoding='UTF-8') as f:
        lines=f.readlines()
        print(len(lines))
        random.shuffle(lines)
        with open('../demotext/水稻玉米小麦大豆大麦_shuffle.txt','w',encoding='UTF-8') as s_f:
            for line in lines:
                s_f.write(line)

