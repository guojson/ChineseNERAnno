import csv
import xlrd
from utils.SQLiteTools import ConnectSqlite
from utils.CSegments import CSegment
from sklearn.model_selection import train_test_split

def gen_labels(id):
    con = ConnectSqlite()
    sql = 'SELECT * FROM category where id='+str(id)+';'
    catogory =con.fetchall_table(sql)
    return str(catogory[0][1]),str(catogory[0][3])

#动态划分，并生成train,test文件
def _train_test_split(file_path,test_size):
    try:
        with open(file_path,'r',encoding='utf-8') as f:
            lines=f.readlines()
            trains_x,tests_x=train_test_split(lines,test_size=test_size, shuffle=True)
            _parse_anno(trains_x,file_path + '.train')
            _parse_anno(tests_x, file_path + '.test')
            print("生成成功!")
    except Exception as e:
        print("出现异常\n"+e)

#将<e0>ABC</e0>转换为
# A B-LOC
# B I-LOC
# C I-LOC
def _parse_anno(sentences,save_path):
    try:
        with open(save_path,'w',encoding='utf-8') as w:
                for count,sentence in enumerate(sentences):
                    tags=[]
                    category=[]
                    first_tag=True
                    for index,character in enumerate(list(sentence.strip())):
                        # print(str(index)+'\t'+character+'\n')
                        if len(character.strip())==0:
                            continue
                        if len(tags)!=0:
                            if ''.join(tags[-2:])=='<e':
                                if character!='>':
                                    category.append(character)
                                else:
                                    tags.append(character)
                            elif len(tags)==3:
                                id=int(''.join(category))
                                _,ann=gen_labels(id)
                                if character !='<' and first_tag:
                                    w.write(character+'\t'+'B-'+ann+'\n')
                                    first_tag = False
                                elif character !='<' and not first_tag:
                                    w.write(character + '\t' + 'I-' + ann+'\n')

                                else:
                                    tags.append('<')
                                    first_tag = True
                            elif len(tags)>=4 and ''.join(tags[-2:])=='/e':
                                if character=='>':
                                    tags.clear()
                                    category.clear()
                            else:
                                tags.append(character)
                        else:
                            if character=='<' and sentence[index+1]=='e':
                                tags.append(character)
                            else:
                                w.write(character + '\t' + 'O'+'\n')
                    w.write('\n')
                    index+=1
    except Exception as e:
        print("出现异常\n"+e)

#转换为纯文本，无标签
def _parse_data(path,save_path):
    with open(save_path,'w',encoding='UTF-8') as f1:
        with open(path,'r',encoding='UTF-8') as f2:
            lines=f2.readlines()
            for line in lines:
                if line!='\n':
                    f1.write(line.strip().split('\t')[0])
                else:
                    f1.write('\n')
#将标记文本<e0>ABC</e0>转换为ABC 0
def _parse_entity(path,save_path):
    with open(path,'r',encoding='utf-8') as f:
        sentences=f.readlines()
        data=[]
        for count,sentence in enumerate(sentences):
            tags=[]
            category=[]
            first_tag=True
            entity=[]
            for index,character in enumerate(list(sentence.strip())):
                # print(str(index)+'\t'+character+'\n')
                if len(character.strip())==0:
                    continue
                if len(tags)!=0:
                    if ''.join(tags[-2:])=='<e':
                        if character!='>':
                            category.append(character)
                        else:
                            tags.append(character)
                    elif len(tags)==3:
                        id=int(''.join(category))
                        dec,ann=gen_labels(id)
                        if character != '<':
                            entity.append(character)
                        else:
                            if sentence[index:index+2]=='<e':
                                print(count)
                                continue
                            tags.append('<')
                            data.append([''.join(entity.copy()),ann,dec,str(id),count])
                            entity.clear()
                    elif len(tags)>=4 and ''.join(tags[-2:])=='/e':
                        if character=='>':
                            tags.clear()
                            category.clear()
                    else:
                        tags.append(character)
                else:
                    if character=='<' and sentence[index+1]=='e':
                        tags.append(character)
            index+=1
        with open(save_path, 'w',encoding='utf-8')as f:
            f_csv = csv.writer(f)
            f_csv.writerows(data)

def _parse_train_test_entity(file_path):
    with open(file_path,'r',encoding='utf-8') as f:
        lines=f.readlines()
    with open(file_path+'.train_test_entity','w',encoding='utf-8') as f2:
        for index,line in enumerate(lines):
            [entity,t_label,p_label]=line.strip().split('\t')
            if t_label=='O' and p_label!='O':
                print(entity,t_label,p_label)
                f2.write(str(index)+'\t'+entity+'\t'+t_label+'\t'+p_label+'\n')

            elif t_label!='O' and p_label=='O':
                print(entity, t_label, p_label)
                f2.write(str(index)+'\t'+entity+'\t'+t_label+'\t'+p_label+'\n')
            elif t_label!=p_label:
                print(entity, t_label, p_label)
                f2.write(str(index)+'\t'+entity+'\t'+t_label+'\t'+p_label+'\n')

def B2Q(uchar):
    """单个字符 半角转全角"""
    inside_code = ord(uchar)
    if inside_code < 0x0020 or inside_code > 0x7e: # 不是半角字符就返回原来的字符
        return uchar
    if inside_code == 0x0020: # 除了空格其他的全角半角的公式为: 半角 = 全角 - 0xfee0
        inside_code = 0x3000
    else:
        inside_code += 0xfee0
    return chr(inside_code)

def Q2B(uchar):
    """单个字符 全角转半角"""
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0
    if inside_code < 0x0020 or inside_code > 0x7e: #转完之后不是半角字符返回原来的字符
        return uchar
    return chr(inside_code)
def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([Q2B(uchar) for uchar in ustring])

def stringpartQ2B(ustring):
    """把字符串中数字和字母全角转半角"""
    return "".join([Q2B(uchar) if is_Qnumber(uchar) or is_Qalphabet(uchar) else uchar for uchar in ustring])
#
# b = strQ2B("ｍｎ123abc博客园".decode('cp936'))
# print
# b
#
# c = strB2Q("ｍｎ123abc博客园".decode('cp936'))

#读取分词词典,返回分词词典list
def read_dic(dic_path):
    data={}
    excel = xlrd.open_workbook(dic_path)
    sheet = excel.sheets()[0]
    rowNum = sheet.nrows  # sheet行数
    MAX_LENGTH=0
    for i in range(rowNum):
        data_list = list(sheet.row_values(i))
        entity=stringQ2B(data_list[0])
        if entity in data.keys():
            if str(int(data_list[3]))!=data[entity]:
                print('当前entity',entity,'当前类别',str(int(data_list[3])),'已存入类别',data[entity],'当前行',data_list[4])
            continue
        else:
            data[entity]=str(int(data_list[3]))
        if MAX_LENGTH<len(data_list[0]):
            MAX_LENGTH=len(data_list[0])
    return data,MAX_LENGTH


if __name__ == '__main__':
    #-------------------------------划分训练集合测试集，并转为X  B-PET形式
    # file_path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann'
    # _train_test_split(file_path,test_size=0.1)
    # ------------------------------将anno转化为实体
    # path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann'
    # save_path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data_entity.csv'
    # _parse_entity(path, save_path)

    # path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann'
    # save_path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data.txt'
    # _parse_anno(path,save_path)

    #----------------将X  B-PET形式转为纯文本形式
    # path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.train'
    # save_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.test.train'
    # _parse_data(path, save_path)

    # myList = ['青海省', '内蒙古自治区', '西藏自治区', '新疆维吾尔自治区', '广西壮族自治区']
    # myList.sort(key=lambda i: len(i), reverse=True)
    # print(myList)
    # with open(file_path,'r',encoding='utf-8') as f:
    #     lines=f.readlines()
    #     index=1
    #     for line in lines:
    #         if len(line)>1000:
    #
    #             print(index,len(line))
    #         index+=1

    dic_path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data_entity.xls'
    # data,MAX_LENGTH=read_dic(dic_path)
    # print(data)
    # print(MAX_LENGTH)

    # cut=CSegment()
    # max_len =39
    # cut.read_user_dict(dic_path)


    #
    # with open(r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.test.train','r',encoding='utf-8') as f:
    #
    #     lines=f.readlines()
    #     anno_list =lines.copy()
    #     for i in range(len(lines)):
    #         cut.MM(lines[i],max_len,True)
    #         MM_result=cut.get_result()
    #         MM_result.reverse()
    #         for data in MM_result:
       # start = 0
       # end = len(lines[0])
       # while start < len(lines[0]):
       #     if lines[0][start:end] in data:
       #         print(lines[0][start:end])
       #         start = end
       #         end = len(lines[0])
       #     else:
       #         end -= 1
       # word_cut=cut_words(lines[0],data,MAX_LENGTH)
       # print(word_cut)
    # #-------------对比真实实体和测试实体
    # file_path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\bilstm-crf-ner-5000.txt.list'
    # _parse_train_test_entity(file_path)
    con = ConnectSqlite()
    excel = xlrd.open_workbook(dic_path)
    sheet = excel.sheets()[0]
    rowNum = sheet.nrows  # sheet行数
    MAX_LENGTH = 0
    rows=[]
    for i in range(rowNum):
        data_list = list(sheet.row_values(i))
        rows.append((data_list[0],data_list[3],data_list[4],0))

    sql='insert into entitys(name, category_id, row_i, deleted) values (?,?,?,?)'
    con.insert_table_many(sql,rows)