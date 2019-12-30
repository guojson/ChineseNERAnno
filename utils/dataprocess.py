
from utils.SQLiteTools import ConnectSqlite

con = ConnectSqlite()
def gen_labels(id):
    sql = 'SELECT * FROM category where id='+str(id)+';'
    catogory =con.fetchall_table(sql)
    return str(catogory[0][3])

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
                                ann=gen_labels(id)
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

def _parse_data(path,save_path):
    with open(save_path,'w',encoding='UTF-8') as f1:
        with open(path,'r',encoding='UTF-8') as f2:
            lines=f2.readlines()
            for line in lines:
                if line!='\n':
                    f1.write(line.strip().split('\t')[0])
                else:
                    f1.write('\n')


if __name__ == '__main__':
    path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.test'
    save_path=r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data.test'
    _parse_anno(path,save_path)
    # path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data.test'
    # save_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\test_data.text'
    # _parse_data(path, save_path)