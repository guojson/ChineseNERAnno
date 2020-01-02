import csv

from utils.SQLiteTools import ConnectSqlite

con = ConnectSqlite()
def gen_labels(id):
    sql = 'SELECT * FROM category where id='+str(id)+';'
    catogory =con.fetchall_table(sql)
    return str(catogory[0][1]),str(catogory[0][3])

#将<e0>ABC</e0>转换为
# A B-LOC
# B-I-LOC
# C-I-LOC
def _parse_anno(path,save_path):
    try:
        with open(save_path,'w',encoding='utf-8') as w:
            with open(path,'r',encoding='utf-8') as f:
                sentences=f.readlines()
                data=[]
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
                            tags.append('<')
                            data.append([''.join(entity.copy()),ann,dec])
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


if __name__ == '__main__':
    path=r'D:\学习资料\知识图谱\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann'
    save_path=r'D:\学习资料\知识图谱\ChineseNERAnno\data\train_data_entity.csv'
    # _parse_anno(path,save_path)
    # path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data.test'
    # save_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\test_data.text'
    # _parse_data(path, save_path)
    _parse_entity(path,save_path)