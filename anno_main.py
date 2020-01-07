import json
import math
import os
import platform
from collections import deque
from tkinter import *
import tkinter.font as tkFont
from tkinter import filedialog
import sqlite3

from utils.SQLiteTools import ConnectSqlite


class MainFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.Version = "YEDDA-V1.0 Annotator"
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
        self.textColumn =8
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
        for item in ['打开','设置','新建', '保存', '另存为']:
            fmenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        emenu = Menu(menubar)
        for item in ['复制', '粘贴', '剪切']:
            emenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        vmenu = Menu(menubar)
        for item in ['默认视图', '新式视图']:
            vmenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        amenu = Menu(menubar)
        for item in ['版权信息', '其他说明']:
            amenu.add_command(label=item,command=lambda arg=item: self.menu_event(arg))

        menubar.add_cascade(label="文件", menu=fmenu)
        menubar.add_cascade(label="编辑", menu=emenu)
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

        self.lbl = Label(self, text="File: no file is opened")
        self.lbl.grid(sticky=W, pady=4, padx=5)

        self.fnt = tkFont.Font(family='Times', size=20, weight="bold", underline=0)

        self.text = Text(self, font=self.fnt,autoseparators=False, selectbackground='light salmon',undo=True)
        self.text.grid(row=1, column=0, columnspan=self.textColumn, rowspan=self.textRow-1, padx=12, sticky=E + W + S + N)
        self.sb = Scrollbar(self)
        self.sb.grid(row=1, column=self.textColumn, rowspan=self.textRow, padx=0, sticky=E + W + S + N)
        self.text['yscrollcommand'] = self.sb.set
        self.sb['command'] = self.text.yview

        self.undobtn=Button(self,width=10, height=1,text="撤销", command=self.backToHistory)
        self.undobtn.grid(sticky=E, pady=5, padx=10, row=0, column=self.textColumn + 1)

        redobtn = Button(self, width=10, height=1, text="恢复", command=self.preToHistory)
        redobtn.grid(sticky=E, pady=5, padx=10, row=0, column=self.textColumn + 2)

        savebtn = Button(self, width=10, height=1, text="保存", command=self.savetext)
        savebtn.grid(sticky=E, pady=5, padx=10, row=1, column=self.textColumn + 1)

        yongli=Button(self, width=10, height=1, text="去除", command=self.ceshi)
        yongli.grid(sticky=E, pady=5, padx=10, row=1, column=self.textColumn + 2)

        delbtn = Button(self, width=10, height=1, text="删除", command=self.delete)
        delbtn.grid(sticky=E, pady=5, padx=10, row=2, column=self.textColumn +1)

        recbtn = Button(self, width=10, height=1, text="局部识别", command=self.recognition)
        recbtn.grid(sticky=E, pady=5, padx=10, row=2, column=self.textColumn + 2)

        globtn = Button(self, width=10, height=1, text="全局识别", command=self.global_recognition)
        globtn.grid(sticky=E, pady=5, padx=10, row=3, column=self.textColumn + 1)

        globtn = Button(self, width=10, height=1, text="全局标记", command=self.global_anno)
        globtn.grid(sticky=E, pady=5, padx=10, row=3, column=self.textColumn + 2)

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

        self.cursorIndex = Label(self, text=("row: %s\ncol: %s" % (0, 0)), foreground="red",
                                 font=(self.textFontStyle, 10, "bold"))
        self.cursorIndex.grid(row=self.textRow, column=self.textColumn + 1, pady=4)
        self.buttons=[]
        for inx,category in enumerate(self.pressCommand):
            index_row = math.floor(int(inx) / 2)
            index_column = int(inx) % 2
            print(index_row)
            button=Button(self, width=10, height=1, text=str(category['id'])+'：'+category['des'], bg=category['color'], command=lambda arg=int(inx): self.onAnnotion(arg)).grid(row=index_row+4,
                                                                                                      column=self.textColumn + index_column+1)
            self.tages[str(inx)]=[]
            self.labelEntryList[str(inx)]=[]
            self.buttons.append(button)

        self.findtext = Entry(self)
        self.findtext.grid(row=index_row+5, column=self.textColumn+1, columnspan=2, sticky=E+W, padx=10)
        self.findtext.delete(0, "end")
        self.findtext.insert(0, "查找文本...")

        self.replacetext = Entry(self,)
        self.replacetext.grid(row=index_row + 6, column=self.textColumn + 1, columnspan=2, sticky=E+W,padx=10)
        self.replacetext.delete(0, "end")
        self.replacetext.insert(0, "替代文本...")
        #替换按钮
        replacebtn = Button(self,height=1, text="替换", command=self.replace_anno)
        replacebtn.grid(sticky=E+W, pady=5, padx=10, row=index_row+7, column=self.textColumn + 1, columnspan=2)

        self.row_number = Entry(self, )
        self.row_number.grid(row=index_row + 8, column=self.textColumn + 1, sticky=E + W, padx=10)
        self.row_number.delete(0, "end")
        self.row_number.insert(0, "1")

        # 替换按钮
        row_btn = Button(self, height=1, text="定位", command=self.line_pos)
        row_btn.grid(sticky=E + W, pady=5, padx=10, row=index_row + 8, column=self.textColumn + 2)

    def line_pos(self):

        row_num = self.row_number.get()
        self.text.see(row_num+'.0')
        self.text.mark_set('insert', row_num+'.0')

    #菜单事件
    def menu_event(self,submenu):
        if submenu=="打开":
            self.onOpen()

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
    #全局标记
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
            self.setNameLabel("File: " + fl)
            self.autoLoadNewFile(self.fileName, "1.0")
            # self.setDisplay()
            # self.initAnnotate()
            self.text.mark_set(INSERT, "1.0")
            self.setCursorLabel(self.text.index(INSERT))


    def readFile(self, filename):
        f = open(filename, "rU",encoding="UTF-8")
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
            self.setNameLabel("File: " + fileName)
            self.text.mark_set(INSERT, newcursor_index)
            self.text.see(newcursor_index)
            self.setCursorLabel(newcursor_index)
            self.setColorDisplay()
    def setCursorLabel(self, cursor_index):
        if self.debug:
            print("Action Track: setCursorLabel")
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
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

if __name__ == '__main__':
    print("SUTDAnnotator launched!")
    print(("OS:%s") % (platform.system()))
    root = Tk()
    root.geometry("1300x700+200+200")
    app = MainFrame(root)
    app.setFont(14)
    root.mainloop()
