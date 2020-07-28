import csv
import datetime
import json
import math
import os
import platform
import threading
from collections import deque

from tkinter import *
import tkinter.font as tkFont
from tkinter import filedialog, ttk
import sqlite3
import tkinter as tk
from tkinter.simpledialog import askinteger
from tkinter.ttk import Treeview, Combobox, Progressbar

import jieba
from sklearn.model_selection import train_test_split

from utils.SQLiteTools import ConnectSqlite
from utils.CSegments import CSegment
from utils.bio2bioes import DataDeal


def get_screen_size(window):
    return window.winfo_screenwidth(), window.winfo_screenheight()


def get_window_size(window):
    return window.winfo_reqwidth(), window.winfo_reqheight()


def center_window(root, width, height):
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    size = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    print(size)
    root.geometry(size)


class MainFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.Version = "Chinese Annotator"
        self.OS = platform.system().lower()
        self.parent = parent
        self.fileName = ""
        self.debug = False
        self.colorAllChunk = True
        self.recommendFlag = True
        self.history = deque(maxlen=20)
        self.currentContent = deque(maxlen=1)
        self.configFile = "configs/default.config"
        self.con = ConnectSqlite("./configs/corpus_info.db")

        self.pressCommand =self.readcategory()
        # self.allKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        # self.controlCommand = {'q':"unTag", 'ctrl+z':'undo'}
        self.labelEntryList ={}
        self.shortcutLabelList = []
        self.configListLabel = None
        self.configListBox = None
        self.word_position=[]

        self.labelEntry=''
        self.labedEntry=''
        self.label_cate=0
        self.label_position=''

        # default GUI display parameter
        if len(self.pressCommand) > 20:
            self.textRow = len(self.pressCommand)
        else:
            self.textRow = 20
        self.textColumn =16
        self.tagScheme = "BMES"
        self.onlyNP = False  ## for exporting sequence
        self.keepRecommend = True
        '''
        self.seged: for exporting sequence, if True then split words with space, else split character without space
        for example, if your data is segmentated Chinese (or English) with words seperated by a space, you need to set this flag as true
        if your data is Chinese without segmentation, you need to set this flag as False
        '''
        self.seged = True  ## False for non-segmentated Chinese, True for English or Segmented Chinese
        self.configFile = "configs/default.config"
        self.entityRe = r'<e[0-9]+>[^(<e|</e)]+</e[0-9]+>'
        self.insideNestEntityRe = r'\[\@\[\@(?!\[\@).*?\#.*?\*\]\#'
        self.recommendRe = r'\[\$.*?\#.*?\*\](?!\#)'
        self.goldAndrecomRe = r'\[\@.*?\#.*?\*\](?!\#)'
        if self.keepRecommend:
            self.goldAndrecomRe = r'\[[\@\$)].*?\#.*?\*\](?!\#)'
        ## configure color
        self.entityColor = "SkyBlue1"
        self.insideNestEntityColor = "light slate blue"
        self.recommendColor = 'lightgreen'
        self.selectColor = 'light salmon'
        self.textFontStyle = "Times"

        self.tages={}

        self.initUI()

    def initUI(self):
        self.parent.title(self.Version)
        self.pack(fill=BOTH, expand=True)

        menubar= Menu(self)
        fmenu = Menu(menubar)
        for item in ['打开','设置','保存']:
            fmenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        emenu = Menu(menubar)
        for item in ['控制面板','检测','检测长度','拆分句子','分割数据集','转为实体', '转为纯文本','定位','查找和替换','统计']:
            emenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        tmenu = Menu(menubar)
        for item in ['BIOES','BMES','分词']:
            tmenu.add_command(label=item, command=lambda arg=item: self.menu_event(arg))

        vmenu = Menu(menubar)
        for item in ['默认视图', '新式视图']:
            vmenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        amenu = Menu(menubar)
        for item in ['版权信息', '其他说明']:
            amenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        menubar.add_cascade(label="文件", menu=fmenu)
        menubar.add_cascade(label="编辑", menu=emenu)
        menubar.add_cascade(label="格式", menu=tmenu)
        menubar.add_cascade(label="视图", menu=vmenu)
        menubar.add_cascade(label="关于", menu=amenu)

        self.parent.config(menu=menubar)


        for idx in range(0, self.textColumn):
            self.columnconfigure(idx, weight=2)
            # self.columnconfigure(0, weight=2)
        self.columnconfigure(self.textColumn + 2, weight=1)
        self.columnconfigure(self.textColumn + 4, weight=1)
        for idx in range(0, 16):
            self.rowconfigure(idx, weight=1)

        self.lbl = Label(self, text="no file is opened")
        self.lbl.grid(sticky=W, pady=4, padx=5)

        self.fnt = tkFont.Font(family='Times', size=20, weight="bold", underline=0)

        self.text = Text(self, font=self.fnt,autoseparators=False, selectbackground='light salmon',undo=True)
        self.text.grid(row=1, column=0, columnspan=self.textColumn, rowspan=self.textRow-1, sticky=E + W + S + N)
        self.sb = Scrollbar(self)
        self.sb.grid(row=1, column=self.textColumn, rowspan=self.textRow-1,sticky=E + W + S + N)
        self.text['yscrollcommand'] = self.sb.set
        self.sb['command'] = self.text.yview

        # self.undobtn=Button(self,width=10, height=1,text="撤销", command=self.backToHistory)
        # self.undobtn.grid(sticky=E, pady=5, padx=10, row=0, column=self.textColumn + 1)
        #
        # redobtn = Button(self, width=10, height=1, text="恢复", command=self.preToHistory)
        # redobtn.grid(sticky=E, pady=5, padx=10, row=0, column=self.textColumn + 2)
        #
        # savebtn = Button(self, width=10, height=1, text="保存", command=self.savetext)
        # savebtn.grid(sticky=E, pady=5, padx=10, row=1, column=self.textColumn + 1)

        # yongli=Button(self, width=10, height=1, text="去除", command=self.ceshi)
        # yongli.grid(sticky=E, pady=5, padx=10, row=1, column=self.textColumn + 2)

        # delbtn = Button(self, width=10, height=1, text="删除", command=self.delete)
        # delbtn.grid(sticky=E, pady=5, padx=10, row=2, column=self.textColumn +1)

        # recbtn = Button(self, width=10, height=1, text="局部识别", command=self.recognition)
        # recbtn.grid(sticky=E, pady=5, padx=10, row=2, column=self.textColumn + 2)

        # globtn = Button(self, width=10, height=1, text="全局识别", command=self.global_recognition)
        # globtn.grid(sticky=E, pady=5, padx=10, row=3, column=self.textColumn + 1)

        # globtn = Button(self, width=10, height=1, text="全局标记", command=self.global_anno)
        # globtn.grid(sticky=E, pady=5, padx=10, row=3, column=self.textColumn + 2)

        # abtn = Button(self,width=10, height=1,text="打开", command=self.onOpen)
        # abtn.grid(sticky=E, pady=5, padx=10, row=0, column=self.textColumn + 1)

        # annoButton = Button(self, width=10, height=1,text="标注",command=self.onAnnotion)
        # annoButton.grid(row=0, column=self.textColumn +2)

        #禁用键盘
        self.text.bind("<Any-KeyPress>",self.anykeypress)
        self.text.bind("<KeyRelease>",self.anykeyrelease)

        #<B1-Motion>,n=1,左键，n=2，中健，n=3, 右键, 按下并移动
        self.text.bind()
        self.text.bind("<B1-Motion>", self.button_motion)
        self.text.bind("<ButtonPress-1>", self.button_down)

        self.text.bind("<Double-Button-1>",self.dou_button_down)

        #<ButtonRelease-1> 松开
        # self.text.bind('<Control-Key-z>', self.backToHistory)
        # self.text.bind('<Control-Key-y>', self.preToHistory)
        self.text.bind('<Control-Key-s>', self.savetext)
        self.note = Label(self, text="选中: ", foreground="Blue", font=(self.textFontStyle, 10, "bold"))
        self.note.grid(row=self.textRow, column=0, padx=12, sticky=W)

        self.cursorName = Label(self, foreground="Blue", font=(self.textFontStyle, 10, "bold"))
        self.cursorName.grid(row=self.textRow, column=1, columnspan=2, sticky=W)

        self.note2 = Label(self, text="缓存实体: ", foreground="Blue", font=(self.textFontStyle, 10, "bold"))
        self.note2.grid(row=self.textRow, column=3, sticky=W)

        self.cursorName2 = Label(self, foreground="Blue", font=(self.textFontStyle, 10, "bold"))
        self.cursorName2.grid(row=self.textRow, column=4, columnspan=2, sticky=W)

        self.note3 = Label(self, text="已完成: ", foreground="Blue", font=(self.textFontStyle, 10, "bold"))
        self.note3.grid(row=self.textRow, column=6, sticky=W)

        self.cursorIndex = Label(self, text=("row: %s col: %s" % (0, 0)), foreground="red",font=(self.textFontStyle, 10, "bold"))
        self.cursorIndex.grid(row=self.textRow, column=7, pady=4, columnspan=3)
        self.state = Label(self, text="正在检测 0 条", foreground="red",
                                 font=(self.textFontStyle, 10, "bold"))
        self.state.grid(row=self.textRow, column=10, columnspan=3 , pady=4)
        self.buttons=[]
        # for inx,category in enumerate(self.pressCommand):
        #     index_row = math.floor(int(inx) / 2)
        #     index_column = int(inx) % 2
        #     print(index_row)
        #     button=Button(self, width=10, height=1, text=str(category['id'])+'：'+category['des'], bg=category['color'], command=lambda arg=int(inx): self.onAnnotion(arg)).grid(row=index_row+4,
        #                                                                                               column=self.textColumn + index_column+1)
        #     self.tages[str(inx)]=[]
        #     self.labelEntryList[str(inx)]=[]
        #     self.buttons.append(button)
        # self.findtext = Entry(self)
        # self.findtext.grid(row=index_row+5, column=self.textColumn+1, columnspan=2, sticky=E+W, padx=10)
        # self.findtext.delete(0, "end")
        # self.findtext.insert(0, "查找文本...")
        #
        # self.replacetext = Entry(self,)
        # self.replacetext.grid(row=index_row + 6, column=self.textColumn + 1, columnspan=2, sticky=E+W,padx=10)
        # self.replacetext.delete(0, "end")
        # self.replacetext.insert(0, "替代文本...")
        # #替换按钮
        # replacebtn = Button(self,height=1, text="替换", command=self.replace_anno)
        # replacebtn.grid(sticky=E+W, pady=5, padx=10, row=index_row+7, column=self.textColumn + 1, columnspan=2)
        #
        # self.row_number = Entry(self, )
        # self.row_number.grid(row=index_row + 8, column=self.textColumn + 1, sticky=E + W, padx=10)
        # self.row_number.delete(0, "end")
        # self.row_number.insert(0, "1")
        #
        # # 替换按钮
        # row_btn = Button(self, height=1, text="定位", command=self.line_pos)
        # row_btn.grid(sticky=E + W, pady=5, padx=10, row=index_row + 8, column=self.textColumn + 2)

    def line_pos(self):

        row_num = self.row_number.get()
        self.text.see(row_num+'.0')
        self.text.mark_set('insert', row_num+'.0')

    def gen_labels(self,id):

        sql = 'SELECT * FROM category where id=' + str(id) + ';'
        catogory = self.con.fetchall_table(sql)
        return str(catogory[0][1]), str(catogory[0][3])

    # 动态划分，并生成train,test文件
    def _train_test_split(self,file_path,keys,train_size,dev_size,test_size):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                trains_x, tests_x = train_test_split(lines, test_size=test_size, shuffle=True)
                if 0.0!=dev_size:
                    trains_x,devs_x=train_test_split(trains_x,test_size=dev_size,shuffle=True)
                    self._parse_anno(devs_x, file_path + '.dev',keys)
                self._parse_anno(trains_x, file_path + '.train',keys)
                self._parse_anno(tests_x, file_path + '.test',keys)
                print("生成成功!")
        except Exception as e:
            print("出现异常\n" + e)

    # 将<e0>ABC</e0>转换为
    # A B-LOC
    # B I-LOC
    # C I-LOC
    def _parse_anno(self,sentences, save_path,keys):
        try:
            with open(save_path, 'w', encoding='utf-8') as w:
                for count, sentence in enumerate(sentences):
                    tags = []
                    category = []
                    first_tag = True
                    have_entity=False
                    sent_,tag_=[],[]
                    for index, character in enumerate(list(sentence.strip())):
                        # print(str(index)+'\t'+character+'\n')
                        if len(character.strip()) == 0:
                            continue
                        if len(tags) != 0:
                            if ''.join(tags[-2:]) == '<e':
                                if character != '>':
                                    category.append(character)
                                else:
                                    tags.append(character)
                            elif len(tags) == 3:
                                id = int(''.join(category))
                                _, ann = self.gen_labels(id)
                                if character != '<' and first_tag:
                                    # w.write(character + ' ' + 'B-' + ann + '\n')
                                    sent_.append(character)
                                    if id in keys:
                                        tag_.append('B-'+ann)
                                        first_tag = False
                                        have_entity = True
                                    else:
                                        tag_.append('O')

                                elif character != '<' and not first_tag:
                                    # w.write(character + ' ' + 'I-' + ann + '\n')
                                    sent_.append(character)
                                    if id in keys:
                                        tag_.append('I-' + ann)
                                        have_entity = True
                                    else:
                                        tag_.append('O')
                                else:
                                    tags.append('<')
                                    first_tag = True
                            elif len(tags) >= 4 and ''.join(tags[-2:]) == '/e':
                                if character == '>':
                                    tags.clear()
                                    category.clear()
                            else:
                                tags.append(character)
                        else:
                            if character == '<' and sentence[index + 1] == 'e':
                                tags.append(character)
                            else:
                                # w.write(character + ' ' + 'O' + '\n')
                                sent_.append(character)
                                tag_.append('O')
                    if have_entity:
                        for index in range(len(sent_)):
                            w.write(sent_[index]+' '+tag_[index]+'\n')
                        w.write('\n')
                    index += 1
        except Exception as e:
            print("出现异常\n" + e)
    def _parse_sentence2pure(self,sentence):
        try:
            # with open(save_path, 'w', encoding='utf-8') as w:
            #     for count, sentence in enumerate(sentences):
            parse_sentence=[]
            tags = []
            category = []
            first_tag = True
            for index, character in enumerate(list(sentence.strip())):
                # print(str(index)+'\t'+character+'\n')
                if len(character.strip()) == 0:
                    continue
                if len(tags) != 0:
                    if ''.join(tags[-2:]) == '<e':
                        if character != '>':
                            category.append(character)
                        else:
                            tags.append(character)
                    elif len(tags) == 3:
                        id = int(''.join(category))
                        _, ann = self.gen_labels(id)
                        if character != '<' and first_tag:
                            # w.write(character + ' ' + 'B-' + ann + '\n')
                            parse_sentence.append(character)
                            first_tag = False
                        elif character != '<' and not first_tag:
                            # w.write(character + ' ' + 'I-' + ann + '\n')
                            parse_sentence.append(character)
                        else:
                            tags.append('<')
                            first_tag = True
                    elif len(tags) >= 4 and ''.join(tags[-2:]) == '/e':
                        if character == '>':
                            tags.clear()
                            category.clear()
                    else:
                        tags.append(character)
                else:
                    if character == '<' and sentence[index + 1] == 'e':
                        tags.append(character)
                    else:
                        # w.write(character + ' ' + 'O' + '\n')
                        parse_sentence.append(character)
            # w.write('\n')
            # index += 1
            return ''.join(parse_sentence)
        except Exception as e:
            print("出现异常\n" + e)


    # 转换为纯文本，无标签
    def _parse_data(self,path, save_path):
        with open(save_path, 'w', encoding='UTF-8') as f1:
            with open(path, 'r', encoding='UTF-8') as f2:
                lines = f2.readlines()
                for line in lines:
                    if line != '\n':
                        f1.write(line.strip().split()[0])
                    else:
                        f1.write('\n')
    # 将标记文本<e0>ABC</e0>转换为ABC 0
    def _parse_entity(self,path, save_path):
        with open(path, 'r', encoding='utf-8') as f:
            sentences = f.readlines()
            data = []
            for count, sentence in enumerate(sentences):
                tags = []
                category = []
                first_tag = True
                entity = []
                for index, character in enumerate(list(sentence.strip())):
                    # print(str(index)+'\t'+character+'\n')
                    if len(character.strip()) == 0:
                        continue
                    if len(tags) != 0:
                        if ''.join(tags[-2:]) == '<e':
                            if character != '>':
                                category.append(character)
                            else:
                                tags.append(character)
                        elif len(tags) == 3:
                            id = int(''.join(category))
                            dec, ann = self.gen_labels(id)
                            if character != '<':
                                entity.append(character)
                            else:
                                if sentence[index:index + 2] == '<e':
                                    print(count)
                                    continue
                                tags.append('<')
                                data.append([''.join(entity.copy()), ann, dec, str(id), count])
                                entity.clear()
                        elif len(tags) >= 4 and ''.join(tags[-2:]) == '/e':
                            if character == '>':
                                tags.clear()
                                category.clear()
                        else:
                            tags.append(character)
                    else:
                        if character == '<' and sentence[index + 1] == 'e':
                            tags.append(character)
                index += 1
            with open(save_path, 'w', encoding='utf-8')as f:
                f_csv = csv.writer(f)
                f_csv.writerows(data)

    def _parse_train_test_entity(self,file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(file_path + '.train_test_entity', 'w', encoding='utf-8') as f2:
            for index, line in enumerate(lines):
                [entity, t_label, p_label] = line.strip().split('\t')
                if t_label == 'O' and p_label != 'O':
                    print(entity, t_label, p_label)
                    f2.write(str(index) + '\t' + entity + '\t' + t_label + '\t' + p_label + '\n')

                elif t_label != 'O' and p_label == 'O':
                    print(entity, t_label, p_label)
                    f2.write(str(index) + '\t' + entity + '\t' + t_label + '\t' + p_label + '\n')
                elif t_label != p_label:
                    print(entity, t_label, p_label)
                    f2.write(str(index) + '\t' + entity + '\t' + t_label + '\t' + p_label + '\n')
    #菜单事件
    def menu_event(self,submenu):
        if submenu=="打开":
            self.onOpen()
        elif submenu=="检测":
            self.check_file()
        elif submenu=="检测长度":
            self.check_file_len()
        elif submenu=='拆分句子':
            segementSentence= SegementSentence(self)
            self.wait_window(segementSentence)
            # var_int = askinteger(title="拆分句子",prompt="最大长度：")
            # print(var_int)
        elif submenu=="分割数据集":
            seqDialog = SeqDialog(self)
            self.wait_window(seqDialog)  # 这一句很重要！！！

        elif submenu=="转为实体":
            path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann'
            save_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data_entity.csv'
            self._parse_entity(path, save_path)

        elif submenu=="转为纯文本":
            ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
            dlg = filedialog.Open(self, filetypes=ftypes)
            # file_opt = options =  {}
            # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
            # dlg = tkFileDialog.askopenfilename(**options)
            fl = dlg.show()
            if fl != '':
                save_path=fl+'.pure'
                self._parse_data(fl, save_path)
        elif submenu == "控制面板":
            inputDialog = MyDialog(self)
            self.wait_window(inputDialog)  # 这一句很重要！！！
        elif submenu == "定位":
            locationDialog=LocatDialog(self)
            self.wait_window(locationDialog)
        elif submenu=="查找和替换":
            replaceDialog=ReplaceDialog(self)
            self.wait_window(replaceDialog)
        elif submenu=="保存":
            self.savetext()
        elif submenu=="撤销":
            self.backToHistory()
        elif submenu=="恢复":
            self.preToHistory()
        elif submenu=="设置":
            categoryDialog = CategoryDialog(self)
            self.wait_window(categoryDialog)  # 这一句很重要！！！
        elif submenu=="统计":
            ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
            dlg = filedialog.Open(self, filetypes=ftypes)
            # file_opt = options =  {}
            # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
            # dlg = tkFileDialog.askopenfilename(**options)
            fl = dlg.show()
            if fl != '':
                with open(fl,'r',encoding='utf-8') as f:
                    lines=f.readlines()
                    entitys={}
                    for line in lines:
                        if line!='\n':
                            label=line.strip().split()[1]
                            if label.startswith('B-'):
                                if label[2:] in entitys.keys():
                                    entitys[label[2:]] = entitys[label[2:]]+1
                                else:
                                    entitys[label[2:]] = 1
                    for k,v in entitys.items():
                        print(k,v)
        elif submenu=='BIOES':
            ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
            dlg = filedialog.Open(self, filetypes=ftypes)
            # file_opt = options =  {}
            # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
            # dlg = tkFileDialog.askopenfilename(**options)
            fl = dlg.show()
            if fl != '':
                dd = DataDeal(fl)
                data_list, label_list = dd.reform_data()
                bioes_data_label = dd.bio_2_bioes(data_list, label_list)
                target_file=fl+'.bioes'
                with open(target_file,'w',encoding='utf-8') as f:
                    for sentence in bioes_data_label:
                        for word in sentence:
                            f.write(word[0]+' '+word[1]+'\n')
                        f.write('\n')
                print('运行完毕...')
        elif submenu=='BMES':
            ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
            dlg = filedialog.Open(self, filetypes=ftypes)
            # file_opt = options =  {}
            # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
            # dlg = tkFileDialog.askopenfilename(**options)
            fl = dlg.show()
            if fl != '':
                dd = DataDeal(fl)
                data_list, label_list = dd.reform_data()
                bmes_data_label = dd.bio_2_bmes(data_list, label_list)
                target_file = fl + '.bmes'
                with open(target_file, 'w', encoding='utf-8') as f:
                    for sentence in bmes_data_label:
                        for word in sentence:
                            f.write(word[0] + ' ' + word[1] + '\n')
                        f.write('\n')
                print('运行完毕...')
        elif submenu=='分词':
            ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
            dlg = filedialog.Open(self, filetypes=ftypes)
            # file_opt = options =  {}
            # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
            # dlg = tkFileDialog.askopenfilename(**options)
            fl = dlg.show()
            if fl != '':
                jieba.load_userdict('configs/save_dictionary.txt')
                with open(fl,'r',encoding='utf-8') as f:
                    lines=f.readlines()
                    with open(fl+'.seg','w',encoding='utf-8') as f2:
                        for line in lines:
                            seg_list = jieba.cut(line.strip())
                            f2.write(' '.join(seg_list)+'\n')
            print('分词完成...')

    def check_file(self):

        path= self.lbl.cget('text')
        with open(path, 'r', encoding='utf-8') as f:
            sentences = f.readlines()
            data = []
            for count, sentence in enumerate(sentences):
                self.state.config(text="正在检测\n"+str(count)+"条")
                tags = []
                category = []
                first_tag = True
                entity = []
                for index, character in enumerate(list(sentence.strip())):
                    # print(str(index)+'\t'+character+'\n')
                    if len(character.strip()) == 0:
                        continue
                    if len(tags) != 0:
                        if ''.join(tags[-2:]) == '<e':
                            if character != '>':
                                category.append(character)
                            else:
                                tags.append(character)
                        elif len(tags) == 3:
                            id = int(''.join(category))
                            # dec, ann = gen_labels(id)
                            if character != '<':
                                entity.append(character)
                            else:
                                if sentence[index:index + 2] == '<e':
                                    print(count)
                                    continue
                                tags.append('<')
                                # data.append([''.join(entity.copy()), ann, dec, str(id), count])
                                entity.clear()
                        elif len(tags) >= 4 and ''.join(tags[-2:]) == '/e':
                            if character == '>':
                                tags.clear()
                                category.clear()
                        else:
                            tags.append(character)
                    else:
                        if character == '<' and sentence[index + 1] == 'e':
                            tags.append(character)
                index += 1

    def check_file_len(self):
        path = self.lbl.cget('text')
        with open(path, 'r', encoding='utf-8') as f:
            sentences = f.readlines()
            if len(sentences)==0:
                return
            try:
                row=1
                for sentence in sentences:
                    # with open(save_path, 'w', encoding='utf-8') as w:
                    #     for count, sentence in enumerate(sentences):
                    parse_sentence = []
                    tags = []
                    category = []
                    first_tag = True
                    for index, character in enumerate(list(sentence.strip())):
                        # print(str(index)+'\t'+character+'\n')
                        if len(character.strip()) == 0:
                            continue
                        if len(tags) != 0:
                            if ''.join(tags[-2:]) == '<e':
                                if character != '>':
                                    category.append(character)
                                else:
                                    tags.append(character)
                            elif len(tags) == 3:
                                id = int(''.join(category))
                                # _, ann = self.gen_labels(id)
                                if character != '<' and first_tag:
                                    # w.write(character + ' ' + 'B-' + ann + '\n')
                                    parse_sentence.append(character)
                                    first_tag = False
                                elif character != '<' and not first_tag:
                                    # w.write(character + ' ' + 'I-' + ann + '\n')
                                    parse_sentence.append(character)
                                else:
                                    tags.append('<')
                                    first_tag = True
                            elif len(tags) >= 4 and ''.join(tags[-2:]) == '/e':
                                if character == '>':
                                    tags.clear()
                                    category.clear()
                            else:
                                tags.append(character)
                        else:
                            if character == '<' and sentences[index + 1] == 'e':
                                tags.append(character)
                            else:
                                # w.write(character + ' ' + 'O' + '\n')
                                parse_sentence.append(character)
                    if len(parse_sentence)>1000:
                        print('行号：',row)
                        print('长度：',len(parse_sentence))
                    row+=1
            except Exception as e:
                print('出现异常，',e)
        print('检测完毕')
     #读取类别配置信息
    def readcategory(self):
        # if os.path.isfile(self.configFile):
        #     with open (self.configFile, 'r',encoding='UTF-8') as fp:
        #         command=json.load(fp)
        #     return command
        sql='SELECT * FROM category'
        catogories= self.con.fetchall_table(sql)
        data=[]
        for catogory in catogories:
            map={}
            map['id']=catogory[0]
            map['des']=catogory[1]
            map['color']=catogory[2]
            map['ann']=catogory[3]
            data.append(map)
        print(data)
        return data

    def button_down(self,event):
        if self.debug:
            print("Action Track: singleLeftClick")
        cursor_index = self.text.index(INSERT)
        row_column = cursor_index.split('.')
        self.word_position.clear()
        self.setCursorLabel(cursor_index)

    def button_motion(self,event):

        if self.debug:
            print("Action Track: singleLeftClick")
        cursor_index = self.text.index(INSERT)
        row_column = cursor_index.split('.')
        self.word_position.append(row_column)
        # print('按下')
        # print(self.word_position)

        index1 = self.word_position[0]
        index2 = self.word_position[-1]

        index11 = int(index1[0])
        index12 = int(index1[1])

        index21 = int(index2[0])
        index22 = int(index2[1])
        segtex = self.text.get(str(index11) + '.' + str(index12), str(index21) + '.' + str(index22))
        if len(segtex)>10:
            segtex=segtex[::10]

        self.cursorName.config(text=segtex)
        # self.findtext.select_clear()
        # self.findtext.insert(0,segtex)

    def dou_button_down(self,event):

        self.text.mark_set("insert",self.text.index(INSERT) )
        print(self.text.index(INSERT))

    #局部识别
    def recognition(self):
        if self.debug:
            print("Action Track: setColorDisplay")
        if self.labelEntry=='':
            return

        self.text.edit_separator()

        countVar = StringVar()
        # entityRe = '<e[0-9]+>[^(<e|</e)]+</e[0-9]+>'
        # compile_name = re.compile(entityRe, re.M)
        # entityList=compile_name.findall(self.text.get('1.0',END))

        self.text.mark_set("matchStart", self.label_position+".0")
        self.text.mark_set("matchEnd", self.label_position+".0")
        self.text.mark_set("searchLimit", self.label_position+'.end')

        entityPa='[^(+>)]'+self.labelEntry+'[^(+</)]'
        # print(entityPa)
        index = 0
        while True:
            pos = self.text.search(entityPa, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            index1=pos.split('.')[0]
            index2=pos.split('.')[1]

            first_pos = index1+'.'+str(int(index2)+1)
            last_pos = "%s + %sc" % (pos, str(int(countVar.get())-1))


            segtex = self.text.get(first_pos, last_pos)
            # print(segtex)
            self.text.delete(first_pos,last_pos)
            self.text.insert(first_pos, self.labedEntry)


            entityRe = '[0-9]+'
            compile_name = re.compile(entityRe, re.M)
            entityList = compile_name.findall(self.labedEntry)

            last_pos = "%s + %sc" % (first_pos, str(len(self.labedEntry)))
            self.text.tag_add('tag' + entityList[0], first_pos, last_pos)
            self.text.tag_config('tag' + entityList[0], background=self.pressCommand[int(entityList[0])]['color'])

    #全局识别
    def global_recognition(self):
        if self.debug:
            print("Action Track: setColorDisplay")
        if self.labelEntry == '':
            return

        self.text.edit_separator()

        countVar = StringVar()
        # entityRe = '<e[0-9]+>[^(<e|</e)]+</e[0-9]+>'
        # compile_name = re.compile(entityRe, re.M)
        # entityList=compile_name.findall(self.text.get('1.0',END))

        self.text.mark_set("matchStart", self.label_position + ".0")
        self.text.mark_set("matchEnd", self.label_position + ".0")
        self.text.mark_set("searchLimit",END)

        entityPa = '[^(+>)]' + self.labelEntry + '[^(+</)]'
        # entityPa='(?<=[<e[0-9]+>).*?'+self.labedEntry+'.*?(?=[</e[0-9]+>)'
        # print(entityPa)
        index = 0
        while True:
            pos = self.text.search(entityPa, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            index1 = pos.split('.')[0]
            index2 = pos.split('.')[1]
            first_pos = index1 + '.' + str(int(index2) + 1)
            last_pos = "%s + %sc" % (pos, str(int(countVar.get()) - 1))
            segtex = self.text.get(first_pos, last_pos)
            # print(segtex)
            self.text.delete(first_pos, last_pos)
            self.text.insert(first_pos, self.labedEntry)

            entityRe = '[0-9]+'
            compile_name = re.compile(entityRe, re.M)
            entityList = compile_name.findall(self.labedEntry)

            last_pos = "%s + %sc" % (first_pos, str(len(self.labedEntry)))
            self.text.tag_add('tag' + entityList[0], first_pos, last_pos)
            self.text.tag_config('tag' + entityList[0], background=self.pressCommand[int(entityList[0])]['color'])
            index+=1
        self.savetext()
        self.cursorName.config(text="成功识别"+str(index)+"条")
    # #全局标记
    def global_anno(self):
        tags=self.text.tag_names()
        for tag in tags:
            print(tag)
            index=0;
            positoins=self.text.tag_ranges(tag)
            for pos_ in positoins:
                if index%2==0:
                    print(pos_,positoins[index+1])
                index+=1
    #替换函数
    def replace_anno(self):

        finder= self.findtext.get()
        if finder.strip()=='':
            return
        replacer=self.replacetext.get()
        if replacer.strip()=='':
            return
        self.text.edit_separator()
        _pos=self.text.index(INSERT)
        _pos=_pos.split('.')[0]
        countVar = StringVar()
        self.text.mark_set("matchStart",_pos+'.0')
        self.text.mark_set("matchEnd", _pos+'.0')
        self.text.mark_set("searchLimit", END)

        # tags=self.text.tag_names(self.text.index(INSERT))
        # if len(tags)==0:
        #     return
        index = 0
        while True:
            pos = self.text.search(finder, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            index1 = pos.split('.')[0]
            index2 = pos.split('.')[1]

            first_pos = index1 + '.' + str(index2)
            last_pos = "%s + %sc" % (pos, str(int(countVar.get())))

            segtex = self.text.get(first_pos, last_pos)
            # print(segtex)
            self.text.delete(first_pos, last_pos)
            self.text.insert(first_pos, replacer)

            entityRe = '[0-9]+'
            compile_name = re.compile(entityRe, re.M)
            entityList = compile_name.findall(replacer)

            re_pos="%s + %sc" % (first_pos, str(len(replacer)))
            self.text.tag_add('tag'+entityList[0], first_pos, re_pos)
            self.text.tag_config('tag'+entityList[0], background=self.pressCommand[int(entityList[0])]['color'])
            index+=1

        self.savetext()
        self.cursorName.config(text="成功修改"+str(index)+"条")

    # 将任何格式的索引号统一为元祖 (行,列) 的格式输出
    def getIndex(self,index):
        return tuple(map(int, str.split(self.text.index(index), ".")))

    def ceshi(self):
        self.text.edit_separator()
        print('测试')
        currentIndex= self.text.index(INSERT)
        print(currentIndex)
        currentRow= currentIndex.split('.')[0]
        currentColumn= currentIndex.split('.')[1]
        count=0
        pre_pos=0
        while True:
            suf_pos = int(currentColumn)-count
            count=count+1
            pre_pos = int(currentColumn)-count
            if self.text.get(currentRow+'.'+str(pre_pos),currentRow+'.'+str(suf_pos))=='<':
                break
        selected_pre__pos=currentRow+'.'+ str(pre_pos)
        print(selected_pre__pos)
        end_pos = 0
        count = 0
        while True:
            pre_pos = int(currentColumn) + count
            count = count + 1
            end_pos = int(currentColumn) + count

            if self.text.get(currentRow + '.' + str(pre_pos), currentRow + '.' + str(end_pos)) == '>':
                break
        selected_end_pos = currentRow + '.' + str(end_pos)
        print(selected_end_pos)
        segtex = self.text.get(selected_pre__pos, selected_end_pos)
        # print(segtex)
        print(segtex.split('</e')[0])
        end_len=len(segtex) -len(segtex.split('</e')[0])
        print(end_len)
        self.text.delete(selected_pre__pos,selected_end_pos)
        self.text.insert(selected_pre__pos,segtex[(end_len-1):(-end_len)])

        # segtex[(end_len-1):(-end_len)]

        # print(segtex[(end_len-1):(-end_len)])
        # compile_name = re.compile(prefixRe, re.M)
        # entityList = compile_name.findall(self.text.get( currentRow+'.0',currentIndex))
        # print(entityList)
        # pos=self.text.search(prefixRe, currentRow+'.0',currentIndex,regexp=True)
        # print(pos)
    def delete(self):
        self.text.edit_separator()
        text_index = self.text.index(INSERT)
        _pos=text_index.split('.')
        # print(_pos[0]+'.0')
        # print(_pos[0]+END)
        self.text.delete(_pos[0]+'.0',_pos[0]+'.'+END)

    def onAnnotion(self,index):
        if self.debug:
            print("Action Track: textReturnEnter")

        try:
            self.text.edit_separator()
            category=self.pressCommand[index]
            if len(self.word_position)>2:
                index1=self.word_position[0]
                index2=self.word_position[-1]
                index11=int(index1[0])
                index12=int(index1[1])

                index21=int(index2[0])
                index22=int(index2[1])
                start=str(index11)+'.'+str(index12)
                end=str(index21)+'.'+str(index22)
            elif len(self.word_position)==1:
                index1 = self.word_position[0]
                index11 = int(index1[0])
                index12 = int(index1[1])
                start="%d.%d" % (index11,index12)
                end = "%d.%d" % (index11,index12)
            else:
                currentIndex = self.text.index(INSERT)
                print(currentIndex)
                start=currentIndex
                end=currentIndex
            #说明是修改
            if start==end:
                currentRow = start.split('.')[0]
                currentColumn = start.split('.')[1]
                print('---->'+currentColumn)
                count = 0
                pre_pos = 0
                pos_len=0
                while True:

                    if pos_len>30:
                        break
                    pos_len+=1
                    suf_pos = int(currentColumn) - count
                    count = count + 1
                    pre_pos = int(currentColumn) - count
                    if self.text.get(currentRow + '.' + str(pre_pos), currentRow + '.' + str(suf_pos)) == '<':
                        break
                selected_pre__pos = currentRow + '.' + str(pre_pos)
                start=selected_pre__pos

                end_pos = 0
                count = 0
                while True:
                    if pos_len > 30:
                        break
                    pre_pos = int(currentColumn) + count
                    count = count + 1
                    end_pos = int(currentColumn) + count

                    if self.text.get(currentRow + '.' + str(pre_pos), currentRow + '.' + str(end_pos)) == '>':
                        break

                selected_end_pos = currentRow + '.' + str(end_pos)

                print(selected_end_pos)

                segtex=self.text.get(selected_pre__pos,selected_end_pos)

                # print(segtex)

                self.text.delete(selected_pre__pos, selected_end_pos)

                end_len = len(segtex) - len(segtex.split('</e')[0])
                segtex=segtex[(end_len - 1):(-end_len)]
                # print(segtex)
                if len(segtex)==0:
                    return
                print('---->'+currentColumn)
                print('---->'+str(len(segtex)))
                end=currentRow+'.'+str(int(selected_pre__pos.split('.')[1])+ len(segtex))

                print('---->'+end)
                self.text.insert(selected_pre__pos, segtex)

            print(start)
            print(end)
            segtex=self.text.get(start,end)
            # lexicons
            #
            # sentence=list(segtex)
            # data=[]
            # for chara in sentence:

            if len(segtex)!=0:
                self.cursorName.config(text=segtex)
                if segtex not in self.labelEntryList[str(index)]:
                    self.labelEntryList[str(index)].append(segtex)
                self.text.delete(start,end)
                self.labelEntry = segtex    #保存实体点

                self.cursorName2.config(text=segtex)
                prefix='<e'+str(index)+'>'
                suffix='</e'+str(index)+'>'
                segtex=prefix+segtex+suffix
                self.labedEntry =segtex     #保存标记点
                self.text.insert(start,segtex,'a')
                index22 = int(start.split('.')[1]) + len(segtex)
                # index22=index12+len(segtex)
                end1 = start.split('.')[0] + '.' + str(index22)
                self.label_position=start.split('.')[0]   #保存所在的行
                self.text.tag_add('tag'+str(index), start,end1)
                self.text.tag_config('tag'+str(index), background=category['color'])
                if [start, end] not in  self.tages[str(index)]:
                    self.tages[str(index)].append([start, end1])
                # self.text.delete(str(index11)+'.'+str(index12),str(index21)+'.'+str(index22))
                # self.text.tag_config('a',background=category['color'])
                # self.text.insert(str(index11)+'.'+str(index12),segtex,'a')
                print(self.tages)
                # print(self.labelEntryList)
                # 标签
                self.label_cate=index
                self.savetext()
        except:
            pass




    def savetext(self,event=None):
        ann_text=self.text.get('1.0',END)

        if self.fileName.endswith('.ann'):
            with open(self.fileName, 'w+', encoding='utf-8') as f:
                f.write(ann_text)
        else:
            with open(self.fileName+'.ann','w+',encoding='utf-8') as f:
                f.write(ann_text)

        print('保存成功!')
        self.cursorName.config(text='保存成功!')
        return
    #禁用按键按下
    def anykeypress(self,event):
        # self.text.config(state=DISABLED)
        return
    #禁用任意按键松开
    def anykeyrelease(self,event):
        # self.text.config(state=NORMAL)
        return
    def onOpen(self):
        ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
        dlg = filedialog.Open(self, filetypes = ftypes)
        # file_opt = options =  {}
        # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        # dlg = tkFileDialog.askopenfilename(**options)
        fl = dlg.show()
        if fl != '':

            self.text.delete("1.0",END)
            text = self.readFile(fl)
            self.text.insert(END, text)
            self.setNameLabel(fl)
            self.autoLoadNewFile(self.fileName, "1.0")
            # self.setDisplay()
            # self.initAnnotate()
            self.text.mark_set(INSERT, "1.0")
            self.setCursorLabel(self.text.index(INSERT))


    def readFile(self, filename):
        f = open(filename, "r",encoding="UTF-8")
        text = f.read()
        self.fileName = filename
        return text

    def setFont(self, value):
        _family = self.textFontStyle
        _size = value
        _weight = "bold"
        _underline = 0
        fnt = tkFont.Font(family=_family, size=_size, weight=_weight, underline=_underline)
        Text(self, font=fnt)
    def returnEnter(self,event):
        if self.debug:
            print("Action Track: returnEnter")
        self.pushToHistory()
        content = self.entry.get()
        self.clearCommand()
        self.executeEntryCommand(content)
        return content


    def textReturnEnter(self,event):
        press_key = event.char
        if self.debug:
            print("Action Track: textReturnEnter")
        self.pushToHistory()
        print("event: ", press_key)
        # content = self.text.get()
        self.clearCommand()
        self.executeCursorCommand(press_key.lower())
        # self.deleteTextInput()
        return press_key

    def preToHistory(self):
        self.text.edit_redo()

    def backToHistory(self):
        #这是返回键
        self.text.edit_undo()

    def pushToHistoryEvent(self):
        if self.debug:
            print("Action Track: pushToHistoryEvent")
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    def clearCommand(self):
        if self.debug:
            print("Action Track: clearCommand")
        self.entry.delete(0, 'end')

    def deleteTextInput(self,event):
        if self.debug:
            print("Action Track: deleteTextInput")
        get_insert = self.text.index(INSERT)
        print("delete insert:",get_insert)
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1])-1)
        get_input = self.text.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.text.get('1.0',last_insert).encode('utf-8')
        followHalf_content = self.text.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0:
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.writeFile(self.fileName, content, last_insert)

    def executeCursorCommand(self,command):
        if self.debug:
            print("Action Track: executeCursorCommand")
        content = self.getText()
        print("Command:"+command)
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            aboveHalf_content = self.text.get('1.0',firstSelection_index)
            followHalf_content = self.text.get(firstSelection_index, "end-1c")
            selected_string = self.text.selection_get()
            if re.match(self.entityRe,selected_string) != None :
                ## if have selected entity
                new_string_list = selected_string.strip('[@]').rsplit('#',1)
                new_string = new_string_list[0]
                followHalf_content = followHalf_content.replace(selected_string, new_string, 1)
                selected_string = new_string
                # cursor_index = "%s - %sc" % (cursor_index, str(len(new_string_list[1])+4))
                cursor_index = cursor_index.split('.')[0]+"."+str(int(cursor_index.split('.')[1])-len(new_string_list[1])+4)
            afterEntity_content = followHalf_content[len(selected_string):]

            if command == "q":
                print('q: remove entity label')
            else:
                if len(selected_string) > 0:
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string, command, cursor_index)
            aboveHalf_content += entity_content
            content = self.addRecommendContent(aboveHalf_content, afterEntity_content, self.recommendFlag)
            content = content.encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            ## not select text
            cursor_index = self.text.index(INSERT)
            [line_id, column_id] = cursor_index.split('.')
            aboveLine_content =  self.text.get('1.0', str(int(line_id)-1) + '.end')
            belowLine_content = self.text.get(str(int(line_id)+1)+'.0', "end-1c")
            line = self.text.get(line_id + '.0', line_id + '.end')
            matched_span =  (-1,-1)
            detected_entity = -1 ## detected entity type:－1 not detected, 1 detected gold, 2 detected recommend
            for match in re.finditer(self.entityRe, line):
                if  match.span()[0]<= int(column_id) & int(column_id) <= match.span()[1]:
                    matched_span = match.span()
                    detected_entity = 1
                    break
            if detected_entity == -1:
                for match in re.finditer(self.recommendRe, line):
                    if  match.span()[0]<= int(column_id) & int(column_id) <= match.span()[1]:
                        matched_span = match.span()
                        detected_entity = 2
                        break
            line_before_entity = line
            line_after_entity = ""
            if matched_span[1] > 0 :
                selected_string = line[matched_span[0]:matched_span[1]]
                if detected_entity == 1:
                    new_string_list = selected_string.strip('[@*]').rsplit('#',1)
                elif detected_entity == 2:
                    new_string_list = selected_string.strip('[$*]').rsplit('#',1)
                new_string = new_string_list[0]
                old_entity_type = new_string_list[1]
                line_before_entity = line[:matched_span[0]]
                line_after_entity =  line[matched_span[1]:]
                selected_string = new_string
                entity_content = selected_string
                cursor_index = line_id + '.'+ str(int(matched_span[1])-(len(new_string_list[1])+4))
                if command == "q":
                    print('q: remove entity label')
                elif command == 'y':
                    print("y: comfirm recommend label")
                    old_key = self.pressCommand.keys()[self.pressCommand.values().index(old_entity_type)]
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string, old_key, cursor_index)
                else:
                    if len(selected_string) > 0:
                        if command in self.pressCommand:
                            entity_content, cursor_index = self.replaceString(selected_string, selected_string, command, cursor_index)
                        else:
                            return
                line_before_entity += entity_content
            if aboveLine_content != '':
                aboveHalf_content = aboveLine_content+ '\n' + line_before_entity
            else:
                aboveHalf_content =  line_before_entity

            if belowLine_content != '':
                followHalf_content = line_after_entity + '\n' + belowLine_content
            else:
                followHalf_content = line_after_entity

            content = self.addRecommendContent(aboveHalf_content, followHalf_content, self.recommendFlag)
            content = content.encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)

    def textReturnEnter(self, event):
        press_key = event.char
        if self.debug:
            print("Action Track: textReturnEnter")
        self.pushToHistory()
        print("event: ", press_key)
        # content = self.text.get()
        self.clearCommand()
        self.executeCursorCommand(press_key.lower())
        # self.deleteTextInput()
        return press_key

    def getText(self):
        textContent = self.text.get("1.0","end-1c")
        textContent = textContent.encode('utf-8')
        return textContent

    def setNameLabel(self, new_file):
        self.lbl.config(text=new_file)
    def autoLoadNewFile(self, fileName, newcursor_index):
        if self.debug:
            print("Action Track: autoLoadNewFile")
        if len(fileName) > 0:
            self.text.delete("1.0", END)
            text = self.readFile(fileName)
            self.text.insert("end-1c", text)
            self.setNameLabel(fileName)
            self.text.mark_set(INSERT, newcursor_index)
            self.text.see(newcursor_index)
            self.setCursorLabel(newcursor_index)
            self.setColorDisplay()
    def setCursorLabel(self, cursor_index):
        if self.debug:
            print("Action Track: setCursorLabel")
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s col: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    def setColorDisplay(self):
        if self.debug:
            print("Action Track: setColorDisplay")
        countVar = StringVar()
        # entityRe = '<e[0-9]+>[^(<e|</e)]+</e[0-9]+>'
        # compile_name = re.compile(entityRe, re.M)
        # entityList=compile_name.findall(self.text.get('1.0',END))

        self.text.mark_set("matchStart", "1.0")
        self.text.mark_set("matchEnd", "1.0")
        self.text.mark_set("searchLimit", 'end-1c')

        index = 0
        while True:
            pos = self.text.search(self.entityRe, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))

            first_pos = pos
            second_pos = "%s+%sc" % (pos, str(1))

            lastsecond_pos = "%s+%sc" % (pos, str(int(countVar.get()) - 1))
            last_pos = "%s + %sc" % (pos, countVar.get())

            segtex = self.text.get(first_pos, last_pos)
            # print(segtex)
            entityRe = '[0-9]+'
            compile_name = re.compile(entityRe, re.M)
            entityList = compile_name.findall(segtex)

            self.text.tag_add('tag' + entityList[0], first_pos, last_pos)
            self.text.tag_config('tag' + entityList[0], background=self.pressCommand[int(entityList[0])]['color'])


# 弹窗
class MyDialog(tk.Toplevel):
    def __init__(self,parent):
        super().__init__()
        self.title('操作面板')
        self.parent = parent # 显式地保留父窗口
        self.wm_attributes('-topmost', 1)
        # self.pack(fill=BOTH, expand=True)
        # 弹窗界面
        self.setup_UI()
        self.userinfo=[]
        self.current_cursor='0'
        dic_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\train_data_entity.xls'
    def setup_UI(self):
        # 第一行（两列）
        #
        # row1 = tk.Frame(self)
        # row1.pack(fill="x")
        # tk.Label(row1, text='姓名：', width=8).pack(side=tk.LEFT)
        # self.name = tk.StringVar()
        # tk.Entry(row1, textvariable=self.name, width=20).pack(side=tk.LEFT)
        #
        # # 第二行
        # row1 = tk.Frame(self)
        # row1.pack(fill="x")
        # tk.Button(row1, text="下一条", command=self.cancel).pack(side=tk.RIGHT)
        # tk.Button(row1, text="排除", command=self.ok).pack(side=tk.RIGHT)
        # tk.Button(row1, text="修正", command=self.ok).pack(side=tk.RIGHT)
        # tk.Button(row1, text="添加", command=self.ok).pack(side=tk.RIGHT)

        self.nextbtn = Button(self, width=10,  height=1, text="下一条", command=self.next_cursor)
        self.nextbtn.grid(sticky=W+E, pady=5, padx=10, row=1, column=1)
        self.addbtn = Button(self, width=10, height=1, text="添加", command=self.addtext)
        self.addbtn.grid(sticky=W+E, pady=5, padx=10, row=1, column=2)

        self.eliminatebtn = Button(self, width=10, height=1, text="排除", command=self.remove_entity)
        self.eliminatebtn.grid(sticky=W+E, pady=5, padx=10, row=1, column=3)


        # self.globtn = Button(self, width=10, height=1, text="全局识别", command=self.parent.global_recognition)
        # self.globtn.grid(sticky=E, pady=5, padx=10, row=1, column=4)
        # self.parent.text.bind('<Control-Key-Down>', self.next_cursor)
        # self.update = Button(self, width=10, height=1, text="修正", command=self.ok)
        # self.update.grid(sticky=W+E, pady=5, padx=10, row=1, column=4)

        self.re_nextbtn = Button(self, width=10, height=1, text="重新识别", command=self.re_next_btn)
        self.re_nextbtn.grid(sticky=W + E, pady=5, padx=10, row=1, column=4)

        # 第三行
        # 第三行con
        #
        self.undobtn=Button(self,width=10, height=1,text="撤销", command=self.parent.backToHistory,bg='#FFFFFF')
        self.undobtn.grid(sticky=E, pady=5, padx=10, row=2, column=1)

        self.cancelbtn=Button(self, width=10, height=1,text="去除",bg='#FFFFFF',command=self.cancel).grid(sticky=E, pady=5, padx=10, row=2, column=2)
        self.okbtn=Button(self, width=10, height=1, bg='#FFFFFF',text="局部识别", command=self.ok).grid(sticky=E, pady=5, padx=10, row=2, column=3)

        #
        redobtn = Button(self, bg='#FFFFFF',width=10, height=1, text="恢复", command=self.parent.preToHistory)
        redobtn.grid(sticky=E, pady=5, padx=10, row=2, column=4)


        for inx, category in enumerate(self.parent.pressCommand):
            index_row = math.floor(int(inx) / 4)
            index_column = int(inx) % 4
            print(index_row)
            button = Button(self, width=10, height=1, text=str(category['id']) + '：' + category['des'],
                            bg=category['color'], command=lambda arg=int(inx): self.parent.onAnnotion(arg)).grid(
                row=index_row + 3,
                column=index_column + 1,padx=10,pady=10)
            self.parent.tages[str(inx)] = []
            self.parent.labelEntryList[str(inx)] = []
            self.parent.buttons.append(button)
    def re_next_btn(self):
        text_index=self.parent.text.index(INSERT)
        text_row = text_index.split('.')[0]
        print(text_row,text_index)
        #已标记文本
        orign_text=self.parent.text.get(text_row+'.0',text_row+'.end')
        print(orign_text)
        text_content=self._parse_anno(orign_text)
        print(text_content)

        #将标签文本替换为纯文本
        self.parent.text.replace(text_row+'.0', text_row+'.end', text_content)


        max_len = 39

        mcut = CSegment()
        mcut.read_user_dict_from_database(self.parent.con)
        mcut.MM(text_content, max_len, True)
        MM_result = mcut.get_result()

        MM_result.reverse()
        for data in MM_result:
            start = str(data[0][0])
            end = str(data[0][1])
            self.parent.text.delete(text_row + '.' + start, text_row + '.' + end)
            relace_text = '<e' + str(data[2]) + '>' + data[1] + '</e' + str(data[2]) + '>'

            last_len = text_row + '.' + str(int(start) + len(relace_text))

            self.parent.text.insert(text_row + '.' + start,
                                    '<e' + str(data[2]) + '>' + data[1] + '</e' + str(data[2]) + '>')

            self.parent.text.tag_add('tag' + str(data[2]), text_row + '.' + start, last_len)
            self.parent.text.tag_config('tag' + str(data[2]), background=self.parent.pressCommand[data[2]]['color'])
        self.parent.text.see(text_row + '.0')
        self.parent.text.mark_set('insert', text_row + '.0')
    #将标记文本转化为纯文本
    def _parse_anno(self, orign_text):
        tags = []
        category = []
        first_tag = True
        target_text=[]
        for index, character in enumerate(list(orign_text.strip())):
            # print(str(index)+'\t'+character+'\n')
            if len(character.strip()) == 0:
                continue
            if len(tags) != 0:
                if ''.join(tags[-2:]) == '<e':
                    if character != '>':
                        category.append(character)
                    else:
                        tags.append(character)
                elif len(tags) == 3:
                    id = int(''.join(category))
                    # _, ann = self.gen_labels(id)
                    if character != '<' and first_tag:
                        target_text.append(character)
                        # w.write(character + '\t' + 'B-' + ann + '\n')
                        first_tag = False
                    elif character != '<' and not first_tag:
                        target_text.append(character)
                        # w.write(character + '\t' + 'I-' + ann + '\n')
                    else:
                        tags.append('<')
                        first_tag = True
                elif len(tags) >= 4 and ''.join(tags[-2:]) == '/e':
                    if character == '>':
                        tags.clear()
                        category.clear()
                else:
                    tags.append(character)
            else:
                if character == '<' and orign_text[index + 1] == 'e':
                    tags.append(character)
                else:
                    target_text.append(character)
                    # w.write(character + '\t' + 'O' + '\n')
        return ''.join(target_text)
    def ok(self):
        if self.parent.debug:
            print("Action Track: setColorDisplay")
        if self.parent.labelEntry=='':
            return

        self.parent.text.edit_separator()

        countVar = StringVar()
        # entityRe = '<e[0-9]+>[^(<e|</e)]+</e[0-9]+>'
        # compile_name = re.compile(entityRe, re.M)
        # entityList=compile_name.findall(self.text.get('1.0',END))

        self.parent.text.mark_set("matchStart", self.parent.label_position+".0")
        self.parent.text.mark_set("matchEnd", self.parent.label_position+".0")
        self.parent.text.mark_set("searchLimit", self.parent.label_position+'.end')

        entityPa='[^(+>)]'+self.parent.labelEntry+'[^(+</)]'
        # print(entityPa)
        index = 0
        while True:
            pos = self.parent.text.search(entityPa, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.parent.text.mark_set("matchStart", pos)
            self.parent.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            index1=pos.split('.')[0]
            index2=pos.split('.')[1]

            first_pos = index1+'.'+str(int(index2)+1)
            last_pos = "%s + %sc" % (pos, str(int(countVar.get())-1))


            segtex = self.parent.text.get(first_pos, last_pos)
            # print(segtex)
            self.parent.text.delete(first_pos,last_pos)
            self.parent.text.insert(first_pos, self.parent.labedEntry)


            entityRe = '[0-9]+'
            compile_name = re.compile(entityRe, re.M)
            entityList = compile_name.findall(self.parent.labedEntry)

            last_pos = "%s + %sc" % (first_pos, str(len(self.parent.labedEntry)))
            self.parent.text.tag_add('tag' + entityList[0], first_pos, last_pos)
            self.parent.text.tag_config('tag' + entityList[0], background=self.parent.pressCommand[int(entityList[0])]['color'])


    def cancel(self):
        self.parent.text.edit_separator()
        print('测试')
        currentIndex = self.parent.text.index(INSERT)
        print(currentIndex)
        currentRow = currentIndex.split('.')[0]
        currentColumn = currentIndex.split('.')[1]
        count = 0
        pre_pos = 0
        while True:
            if count>=60:
                break
            suf_pos = int(currentColumn) - count
            count = count + 1
            pre_pos = int(currentColumn) - count
            if self.parent.text.get(currentRow + '.' + str(pre_pos), currentRow + '.' + str(suf_pos)) == '<':
                break
        selected_pre__pos = currentRow + '.' + str(pre_pos)
        print(selected_pre__pos)
        end_pos = 0
        count = 0
        while True:
            if count >= 60:
                break
            pre_pos = int(currentColumn) + count
            count = count + 1
            end_pos = int(currentColumn) + count

            if self.parent.text.get(currentRow + '.' + str(pre_pos), currentRow + '.' + str(end_pos)) == '>':
                break
        selected_end_pos = currentRow + '.' + str(end_pos)
        print(selected_end_pos)
        segtex = self.parent.text.get(selected_pre__pos, selected_end_pos)
        # print(segtex)
        print(segtex.split('</e')[0])
        end_len = len(segtex) - len(segtex.split('</e')[0])
        print(end_len)
        self.parent.text.delete(selected_pre__pos, selected_end_pos)
        self.parent.text.insert(selected_pre__pos, segtex[(end_len - 1):(-end_len)])

    def remove_entity(self):

        index1 = self.parent.word_position[0]
        index2 = self.parent.word_position[-1]
        index11 = int(index1[0])
        index12 = int(index1[1])

        index21 = int(index2[0])
        index22 = int(index2[1])
        start = str(index11) + '.' + str(index12)
        end = str(index21) + '.' + str(index22)

        # remove_entity= self.parent.cursorName["text"]
        remove_entity=self.parent.text.get(start,end)
        print(remove_entity)
        try:
            if self.parent.con.fetchall_table("select * from entitys where name='" + remove_entity + "';", True) == -1:
                timestamp= datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.parent.con.insert_table_many("insert into entitys(name, deleted, timestamp) VALUES (?,?,?)",[(remove_entity,3,timestamp)])
                self.parent.cursorName.config(text='添加成功!')
        except Exception as e :
            print(e)


    def next_cursor(self):
        self.parent.text.edit_separator()
        text_index = self.parent.text.index(INSERT)
        _pos = text_index.split('.')
        if self.current_cursor=='0':
            self.current_cursor = _pos[0]
        else:
            self.current_cursor = str(int(_pos[0]) + 1)
        # self.parent.text.see(str(row_num)+'.0')
        # self.parent.text.mark_set('insert', str(row_num)+'.0')

        max_len=39
        text_content = self.parent.text.get(self.current_cursor+".0", self.current_cursor+".end")
        print(text_content)
        mcut=CSegment()
        mcut.read_user_dict_from_database(self.parent.con)
        mcut.MM(text_content, max_len, True)
        MM_result = mcut.get_result()

        MM_result.reverse()
        for data in MM_result:
            start=str(data[0][0])
            end=str(data[0][1])
            self.parent.text.delete(self.current_cursor+'.'+start, self.current_cursor+'.'+end)
            relace_text='<e'+str(data[2])+'>'+data[1]+'</e'+str(data[2])+'>'

            last_len=self.current_cursor+'.'+str(int(start)+len(relace_text))

            self.parent.text.insert(self.current_cursor+'.'+start,'<e'+str(data[2])+'>'+data[1]+'</e'+str(data[2])+'>' )

            self.parent.text.tag_add('tag' + str(data[2]), self.current_cursor+'.'+start, last_len)
            self.parent.text.tag_config('tag' +str(data[2]), background=self.parent.pressCommand[data[2]]['color'])
        self.parent.text.see(self.current_cursor + '.0')
        self.parent.text.mark_set('insert', self.current_cursor + '.0')
    def addtext(self):
        new_entity=self.parent.labelEntry
        new_entity_tag=self.parent.label_cate
        try:
            if self.parent.con.fetchall_table("select * from entitys where name='"+new_entity+"';",True)==-1:
                # if self.parent.con.fetchall_table("select * from entitys where name='"+new_entity+"'")!=-1:
                timestamp= datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql='insert into entitys(name, category_id, row_i, deleted,timestamp) VALUES (?,?,?,?,?)'
                self.parent.con.insert_table_many(sql,[(new_entity,new_entity_tag,self.current_cursor,0,timestamp)])
                mcut=CSegment()
                mcut.read_user_dict_from_database(self.parent.con)
                self.parent.cursorName.config(text='添加成功!')
        except Exception as e:
            print(e)
class LocatDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.title('定位')
        self.parent = parent  # 显式地保留父窗口
        self.wm_attributes('-topmost', 1)
        # self.pack(fill=BOTH, expand=True)
        # 弹窗界面
        tk.Label(self, text="行数：").grid(row=0)
        self.location = tk.Entry(self,)
        self.location.grid(row=0, column=1, padx=10, pady=5)
        self.location.bind("<Return>", self.locate)
        tk.Button(self, text="定位", width=10, command=self.locate).grid(row=1, column=0,  padx=10, pady=5, columnspan=2)
    def locate(self,event=None):
        row_num = self.location.get()
        self.parent.text.see(row_num + '.0')
        self.parent.text.mark_set('insert', row_num + '.0')
class ReplaceDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.title('查找和替换')
        self.parent = parent  # 显式地保留父窗口
        self.wm_attributes('-topmost', 1)
        # self.pack(fill=BOTH, expand=True)
        # 弹窗界面
        # tk.Label(self, text="行数：").grid(row=0)
        # self.location = tk.Entry(self,)
        # self.location.grid(row=0, column=1, padx=10, pady=5)
        # tk.Button(self, text="定位", width=10, command=self.locate).grid(row=1, column=0,  padx=10, pady=5, columnspan=2)

        tk.Label(self, text="查找：").grid(row=0)
        self.findtext = Entry(self)
        self.findtext.grid(row=0, column=1, columnspan=2, sticky=E + W, padx=10, pady=10)
        self.findtext.delete(0, "end")
        self.findtext.insert(0, "查找文本...")

        tk.Label(self, text="替换：").grid(row=1)
        self.replacetext = Entry(self, )
        self.replacetext.grid(row=1, column=1, columnspan=2, sticky=E + W, padx=10,pady=10)
        self.replacetext.delete(0, "end")
        self.replacetext.insert(0, "替代文本...")
        # 替换按钮
        replacebtn = Button(self, height=1, text="替换", command=self.replace_anno)
        replacebtn.grid(sticky=E + W, pady=5, padx=10, row=2, column=0, columnspan=3)

    def replace_anno(self):
        row_num = self.location.get()
        self.parent.text.see(row_num + '.0')
        self.parent.text.mark_set('insert', row_num + '.0')
class SeqDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.title('分割数据集')
        self.parent = parent  # 显式地保留父窗口
        self.wm_attributes('-topmost', 1)
        self.geometry("400x250+100+100")

        self.init()

    def init(self):

        # 使用Frame增加一层容器
        fm1 = Frame(self, bd=1,)

        entitys = self.parent.con.fetchall_table('select * from category')
        print(entitys)
        self.vars = {}
        self.checkboxs = {}
        # self.all_var=IntVar()
        # self.all_var.set(0)
        # self.selectAll=Checkbutton(fm1, text='全选', onvalue=1, offvalue=0,variable=self.all_var,command =self.select_all)
        # self.selectAll.grid(row=0, column=0, columnspan=2, sticky=W, padx=10, pady=5)
        for index, entity in enumerate(entitys):
            var = IntVar()
            var.set(entity[4])
            # print(var)
            self.vars[entity[0]]=var
            self.checkboxs[entity[0]]=(Checkbutton(fm1, text=entity[1], onvalue=1, offvalue=0, variable=self.vars[entity[0]],
                                              command=lambda arg=entity[0]: self.select_item(arg)))
            if index % 2 == 1:
                self.checkboxs[entity[0]].grid(row=int(index / 2), column=index % 2, sticky=W, padx=10, pady=5)
            else:
                self.checkboxs[entity[0]].grid(row=int(index / 2), column=index % 2, sticky=W, padx=10, pady=5)
        fm1.pack(side=LEFT, fill='y', expand=YES)

        fm2 = Frame(self, bd=1, )


            #train
        tk.Label(fm2, text="训练集").grid(row=0, column=0 , padx=10, pady=10)
        self.train_div = Entry(fm2)
        self.train_div.grid(row=0, column=1, sticky=E + W, padx=10, pady=10)
        self.train_div.delete(0, "end")
        self.train_div.insert(0, "0.8")
        #dev
        tk.Label(fm2, text="验证集").grid(row=1,column=0 , padx=10, pady=10)
        self.dev_div = Entry(fm2)
        self.dev_div.grid(row=1, column=1,  sticky=E + W, padx=10, pady=10)
        self.dev_div.delete(0, "end")
        self.dev_div.insert(0, "0.1")

        #test
        tk.Label(fm2, text="测试集").grid(row=3,column=0 , padx=10, pady=10)
        self.test_div = Entry(fm2)
        self.test_div.grid(row=3, column=1,  sticky=E + W, padx=10, pady=10)
        self.test_div.delete(0, "end")
        self.test_div.insert(0, "0.1")
        replacebtn = Button(fm2, height=1, text="分割", command=self.dataset_seq)
        replacebtn.grid(sticky=E + W, pady=5, padx=10, row=4, column=0, columnspan=2)
        fm2.pack(side=TOP, fill='y', expand=YES)
        #分割



    def select_all(self):
        if self.all_var.get()==1:
            for var in self.vars:
                var.set(1)
        else:
            for var in self.vars:
                var.set(0)
    def select_item(self,id):
        self.vars[id].set(self.vars[id].get())
    def dataset_seq(self):
        keys=[]
        for k,v in self.vars.items():
            if v.get()==1:
                keys.append(k)
        file_path = self.parent.lbl.cget('text')
        train_size=self.train_div.get()
        dev_size=self.dev_div.get()
        test_size=self.test_div.get()
        self.parent._train_test_split(file_path,keys, train_size=float(train_size),dev_size=float(dev_size), test_size=float(test_size))
class CategoryDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.title('类别设置')
        self.parent = parent  # 显式地保留父窗口
        self.wm_attributes('-topmost', 1)
        self.init()

    def init(self):
        self.scrollbar = tk.Scrollbar(self, )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        title = ['1', '2', '3', '4', '5', ]
        self.tree = Treeview(self, columns=title,yscrollcommand=self.scrollbar.set,
                                show='headings')

        self.scrollbar.config(command=self.tree.yview)
        self.tree.column('1', width=80, anchor='center')
        self.tree.column('2', width=100, anchor='center')
        self.tree.column('3', width=100, anchor='center')
        self.tree.column('4', width=100, anchor='center')
        self.tree.column('5', width=80, anchor='center')

        self.tree.heading('1', text='Id')
        self.tree.heading('2', text='des')
        self.tree.heading('3', text='color')
        self.tree.heading('4', text='ann')
        self.tree.heading('5', text='deleted')

        results=self.parent.con.fetchall_table('select * from category')
        print(results)
        for result in results:
            self.tree.insert('', 'end', values=result)
        self.tree.bind("<Double-1>", self.onDBClick)
        self.tree.pack()

    def onDBClick(self,event):
        item = self.tree.selection()[0]
        print("you clicked on ", self.tree.item(item, "values"))

class SegementSentence(tk.Toplevel):
    def __init__(self,parent):
        super().__init__()
        self.title('句子拆分')
        self.parent = parent  # 显式地保留父窗口
        self.wm_attributes('-topmost', 1)
        self.init()
    def init(self):
        # train
        tk.Label(self, text="最大长度：").grid(row=0, column=0, padx=10, pady=10)
        self.train_div = Entry(self)
        self.train_div.grid(row=0, column=1, sticky=E + W, padx=10, pady=10)
        self.train_div.delete(0, "end")
        self.train_div.insert(0, "300")

        tk.Label(self, text="分隔符：").grid(row=1, column=0, padx=10, pady=10)
        self.seg_mode = Combobox(self)
        self.seg_mode.grid(row=1, column=1, sticky=E + W, padx=10, pady=10)
        self.seg_mode['value']=('｡','.','！')
        self.seg_mode.current(0)

        # 分割
        segbtn = Button(self, height=1, text="剪辑", command=lambda :self.thread_it(self.sentence_seg))
        segbtn.grid(sticky=E + W, pady=5, padx=10, row=2, column=0, columnspan=2)

        self.progressbar=Progressbar(self,orient="horizontal", length=200, mode="determinate")
        self.progressbar.grid_forget()

    def sentence_seg(self):
        file_path = self.parent.lbl.cget('text')
        max_len = self.train_div.get()
        segmode=self.seg_mode.get()
        print(file_path,max_len,segmode)

        with open(file_path,'r',encoding='utf-8') as f:
            sentences=f.readlines()

        self.progressbar.grid(sticky=E + W, pady=5, padx=10, row=3, column=0, columnspan=2)
        # self.progressbar["maximum"] = 100
        self.progressbar["value"] = 0

        sent_num=len(sentences)
        self.progressbar["maximum"] = sent_num
        # sen_length=[]
        file_path = self.parent.lbl.cget('text')

        with open(file_path+'.shot','w',encoding='utf-8') as w:
            for sentence_index in range(sent_num):
                sentence=sentences[sentence_index]
                # parse_sentence=self._parse_sentence2pure(sentence)
                for subsentence in  sentence.strip().split(segmode):
                    print(len(subsentence))
                    if len(subsentence)>10:
                        w.write(subsentence+'\n')
                        # sen_length.append(len(subsentence))
                self.progressbar["value"] =sentence_index
                self.update()

    def _parse_sentence2pure(self,sentence):
        try:
            # with open(save_path, 'w', encoding='utf-8') as w:
            #     for count, sentence in enumerate(sentences):
            parse_sentence=[]
            tags = []
            category = []
            first_tag = True
            for index, character in enumerate(list(sentence.strip())):
                # print(str(index)+'\t'+character+'\n')
                if len(character.strip()) == 0:
                    continue
                if len(tags) != 0:
                    if ''.join(tags[-2:]) == '<e':
                        if character != '>':
                            category.append(character)
                        else:
                            tags.append(character)
                    elif len(tags) == 3:
                        id = int(''.join(category))
                        # _, ann = self.gen_labels(id)
                        if character != '<' and first_tag:
                            # w.write(character + ' ' + 'B-' + ann + '\n')
                            parse_sentence.append(character)
                            first_tag = False
                        elif character != '<' and not first_tag:
                            # w.write(character + ' ' + 'I-' + ann + '\n')
                            parse_sentence.append(character)
                        else:
                            tags.append('<')
                            first_tag = True
                    elif len(tags) >= 4 and ''.join(tags[-2:]) == '/e':
                        if character == '>':
                            tags.clear()
                            category.clear()
                    else:
                        tags.append(character)
                else:
                    if character == '<' and sentence[index + 1] == 'e':
                        tags.append(character)
                    else:
                        # w.write(character + ' ' + 'O' + '\n')
                        parse_sentence.append(character)
            # w.write('\n')
            # index += 1
            return ''.join(parse_sentence)
        except Exception as e:
            print("出现异常\n" + e)


    @staticmethod
    def thread_it(func, *args):
        t = threading.Thread(target=func, args=args)
        t.setDaemon(True)  # 守护--就算主界面关闭，线程也会留守后台运行（不对!）
        t.start()  # 启动
        # t.join()          # 阻塞--会卡死界面！



if __name__ == '__main__':
    print("SUTDAnnotator launched!")
    print(("OS:%s") % (platform.system()))
    root = Tk()
    # center_window(root,1300,700)
    root.geometry("1300x700")
    app = MainFrame(root)
    app.setFont(13)
    root.mainloop()
