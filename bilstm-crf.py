
# coding: utf-8

# In[1]:
from keras.callbacks import TensorBoard
from sklearn import metrics
import numpy as np
import keras
from keras.models import Sequential
from keras.models import Model
from keras.layers import Masking, Embedding, Bidirectional, LSTM, Dense, Input, TimeDistributed, Activation
from keras.preprocessing import sequence
from keras_contrib.layers import CRF
from keras_contrib.losses import crf_loss
from keras_contrib.metrics import crf_viterbi_accuracy
from keras import backend as K
# from keras_self_attention import  SeqSelfAttention
import  pickle
from utils.conlleval import evaluate
from keras.models import load_model
import numpy as np
char_vocab_path = "./data/char_vocabs.txt" # 字典文件
train_data_path = r"D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.train" # 训练数据
test_data_path = r"D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.test" # 测试数据

special_words = ['<PAD>', '<UNK>'] # 特殊词表示 #<PAD>:对于短句子用<PAD>填充，<EOS>代表结尾；<UNK>代表未知词汇;<GO>代表decode第一个输入，即解码的开始
# "BIO"标记的标签
# label2idx = {"O": 0,
#              "B-PER": 1, "I-PER": 2,
#              "B-LOC": 3, "I-LOC": 4,
#              "B-ORG": 5, "I-ORG": 6
#              }
label2idx={'O': 0,
           'B-CRO': 1, 'I-CRO': 2,
           'B-DIS': 3, 'I-DIS': 4,
           'B-PET': 5, 'I-PET': 6,
           'B-DRUG': 7, 'I-DRUG': 8,
           'B-FER': 9, 'I-FER': 10,
           'B-REA': 11, 'I-REA': 12,
           'B-WEE': 13, 'I-WEE': 14,
           'B-CLA': 15, 'I-CLA': 16,
           'B-PER': 17, 'I-PER': 18,
           'B-PART': 19, 'I-PART': 20,
           'B-STRAINS': 21, 'I-STRAING': 22,
           'B-SYM': 23, 'I-SYM': 24}

# 索引和BIO标签对应
idx2label = {idx: label for label, idx in label2idx.items()}

# 读取字符词典文件
with open(char_vocab_path, "r", encoding="utf8") as fo:
    char_vocabs = [line.strip() for line in fo]
char_vocabs = special_words + char_vocabs

# 字符和索引编号对应
idx2vocab = {idx: char for idx, char in enumerate(char_vocabs)}
vocab2idx = {char: idx for idx, char in idx2vocab.items()}
EPOCHS =15
BATCH_SIZE = 64
EMBED_DIM = 300
HIDDEN_SIZE = 64
MAX_LEN = 1000

# In[2]:

# 读取训练语料
def read_corpus(corpus_path, vocab2idx, label2idx):
    datas, labels = [], []
    with open(corpus_path, encoding='utf-8') as fr:
        lines = fr.readlines()
    sent_, tag_ = [], []
    for line in lines:
        if line != '\n':
            [char, label] = line.strip().split('\t')
            # print([char, label])
            sent_.append(char)
            tag_.append(label)
        else:
            sent_ids = [vocab2idx[char] if char in vocab2idx else vocab2idx['<UNK>'] for char in sent_]
            tag_ids = [label2idx[label] if label in label2idx else 0 for label in tag_]
            datas.append(sent_ids)
            labels.append(tag_ids)
            sent_, tag_ = [], []
    return datas, labels
def get_valid_nertag(input_data, result_tags):
    result_words = []
    start, end =0, 1 # 实体开始结束位置标识
    tag_label = "O" # 实体类型标识
    for i, tag in enumerate(result_tags):
        if tag.startswith("B"):
            if tag_label != "O": # 当前实体tag之前有其他实体
                result_words.append((input_data[start: end], tag_label)) # 获取实体
            tag_label = tag.split("-")[1] # 获取当前实体类型
            start, end = i, i+1 # 开始和结束位置变更
        elif tag.startswith("I"):
            temp_label = tag.split("-")[1]
            if temp_label == tag_label: # 当前实体tag是之前实体的一部分
                end += 1 # 结束位置end扩展
        elif tag == "O":
            if tag_label != "O": # 当前位置非实体 但是之前有实体
                result_words.append((input_data[start: end], tag_label)) # 获取实体
                tag_label = "O"  # 实体类型置"O"
            start, end = i, i+1 # 开始和结束位置变更
    if tag_label != "O": # 最后结尾还有实体
        result_words.append((input_data[start: end], tag_label)) # 获取结尾的实体
    return result_words
def train():
    # 加载训练集
    train_datas, train_labels = read_corpus(train_data_path, vocab2idx, label2idx)
    # 加载测试集
    test_datas, test_labels = read_corpus(test_data_path, vocab2idx, label2idx)

    train_datas_v2=train_datas.copy()
    test_datas_v2=test_datas.copy()


    # In[3]:

    print(train_datas[5])
    print([idx2vocab[idx] for idx in train_datas[5]])
    print(train_labels[5])
    print([idx2label[idx] for idx in train_labels[5]])

    # In[4]:

    K.clear_session()

    VOCAB_SIZE = len(vocab2idx)
    CLASS_NUMS = len(label2idx)
    print(VOCAB_SIZE, CLASS_NUMS)

    print('padding sequences')
    train_datas = sequence.pad_sequences(train_datas, maxlen=MAX_LEN)  # 补零
    train_labels = sequence.pad_sequences(train_labels, maxlen=MAX_LEN)
    test_datas = sequence.pad_sequences(test_datas, maxlen=MAX_LEN)
    test_labels = sequence.pad_sequences(test_labels, maxlen=MAX_LEN)
    print('x_train shape:', train_datas.shape)
    print('x_test shape:', test_datas.shape)

    train_labels = keras.utils.to_categorical(train_labels, CLASS_NUMS)
    test_labels = keras.utils.to_categorical(test_labels, CLASS_NUMS)
    print('trainlabels shape:', train_labels.shape)
    print('testlabels shape:', test_labels.shape)

    # BiLSTM+CRF模型构建
    inputs = Input(shape=(MAX_LEN,), dtype='int32')
    x = Masking(mask_value=0)(inputs)
    x = Embedding(VOCAB_SIZE, EMBED_DIM, mask_zero=True)(x)
    x = Bidirectional(LSTM(HIDDEN_SIZE, return_sequences=True))(x)
    # x = SeqSelfAttention(attention_activation='softmax')(x)
    x = TimeDistributed(Dense(CLASS_NUMS))(x)

    outputs = CRF(CLASS_NUMS, name='output')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.summary()

    tensorboard_cb = TensorBoard(
        log_dir='./logs',
        # histogram_freq=1,
        write_graph=True,
        write_images=True
    )
    model.compile(loss=crf_loss, optimizer='adam', metrics=[crf_viterbi_accuracy])
    history = model.fit(train_datas, train_labels, epochs=EPOCHS, verbose=1, validation_split=0.1,
                        callbacks=[tensorboard_cb])

    score = model.evaluate(test_datas, test_labels, batch_size=BATCH_SIZE)
    print(model.metrics_names)
    print(score)

    y_pred = model.predict(test_datas)
    y_label = np.argmax(y_pred, axis=-1)
    y_labels = y_label.reshape(1, -1)[0]
    pre_tags= [idx2label[idx]  for idx in y_labels]

    ture_label = np.argmax(test_labels, axis=-1)
    true_labels = ture_label.reshape(1, -1)[0]
    true_tags = [idx2label[idx] for idx in true_labels]

    evaluate(true_tags,pre_tags,verbose=True)



    with open('bilstm-crf.txt', 'wb') as file_pi:
        pickle.dump(history.history, file_pi)
    # save model
    model.save("./model/bilstm_crf_model.h5")
    #
    # y_pred = model.predict(test_datas)
    #
    # y_label = np.argmax(y_pred, axis=-1)
    # y_label_v2 = y_label.reshape(1, -1)[0]
    #
    # y_true = np.argmax(test_labels, axis=-1)
    # y_true = y_true.reshape(1, -1)[0]
    # print(metrics.classification_report(y_true, y_label_v2, labels=list(label2idx.values()),
    #                                     target_names=list(label2idx.keys()), digits=4))
    #
    # with open('bilstm-crf-ner-test.txt','w',encoding='utf-8') as f:
    #     for idx in range(len(test_datas_v2)):
    #         data=test_datas_v2[idx]
    #         sent_chars=[idx2vocab[idx] for idx in data]
    #         y_ner = [idx2label[i] for i in y_label[idx]][-len(sent_chars):]
    #         result_words = get_valid_nertag(sent_chars, y_ner)
    #         for (word, tag) in result_words:
    #             print("".join(word), tag)
    #             f.write("".join(word)+'\t'+tag+'\n')
#------------------------
        # y_pred = model.predict(train_datas)
        #
        # y_label = np.argmax(y_pred, axis=-1)
        # y_label = y_label.reshape(1, -1)[0]
        #
        # y_true = np.argmax(train_labels, axis=-1)
        # y_true = y_true.reshape(1, -1)[0]
        #
        # for data in train_datas:
        #     sent_chars=[idx2vocab[idx] for idx in data]
        #     y_ner = [idx2label[i] for i in y_label][-len(sent_chars):]
        #     result_words = get_valid_nertag(sent_chars, y_ner)
        #     for (word, tag) in result_words:
        #         print("".join(word), tag)
        #         f.write("".join(word)+'\t'+tag+'\n')



def val(file_path,file_label_path, save_path):

    char_vocab_path = "./data/char_vocabs.txt" # 字典文件
    model_path = "./model/bilstm_crf_model.h5" # 模型文件

    special_words = ['<PAD>', '<UNK>']

    with open(char_vocab_path, "r", encoding="utf8") as fo:
        char_vocabs = [line.strip() for line in fo]
    char_vocabs = special_words + char_vocabs

    idx2vocab = {idx: char for idx, char in enumerate(char_vocabs)}
    vocab2idx = {char: idx for idx, char in idx2vocab.items()}

    idx2label = {idx: label for label, idx in label2idx.items()}
    model = load_model(model_path, custom_objects={'CRF': CRF}, compile=False)
    pre_labels=[]
    cha_ners=[]
    ture_lables=[]
    with open(file_path,'r',encoding='utf-8') as f:
        sentences = f.readlines()
        with open(file_label_path,'r',encoding='utf-8') as f3:
            lable_sentence=f3.readlines()
            cha_ner=[]
            ture_lable=[]

            for labels in lable_sentence:
                if labels!='\n':
                    cha,cat=labels.strip().split('\t')
                    cha_ners.append(cha)
                    ture_lables.append(cat)
                    # cha_ner.append(cha)
                    # ture_lable.append(cat)
                # else:
                #     cha_ners.append(cha_ner.copy())
                #     ture_lables.append(ture_lable.copy())
                #     cha_ner.clear()
                #     ture_lable.clear()

            for idx in range(len(sentences)):
                sentence=sentences[idx].strip()
                sent_chars=list(sentence)
                # print(sentence)
                lab_sen_chars=list(lable_sentence[idx])

                with open(save_path,'a+',encoding='utf-8') as f2:
                    for sent_char in sent_chars:
                        f2.write(sent_char)
                    f2.write('\n')
                    sent2id = [vocab2idx[word] if word in vocab2idx else vocab2idx['<UNK>'] for word in sent_chars]

                    sent2input = np.array([[0] * (MAX_LEN-len(sent2id)) + sent2id[:MAX_LEN]])
                    y_pred = model.predict(sent2input)
                    y_label = np.argmax(y_pred, axis=2)
                    y_label = y_label.reshape(1, -1)[0]
                    y_ner = [idx2label[i] for i in y_label][-len(sent_chars):]

                    print(idx2label)
                    print(sent_chars)
                    print(sent2id)

                    print(y_ner)
                    pre_labels.extend(y_ner)

                    # if not len(cha_ners[idx])==len(sentence)==len(y_ner):
                    #     print('-------------------------------------------------')
                    #     print(idx+1,len(cha_ners[idx]),len(sentence),len(y_ner))
                    #     print(''.join(cha_ners[idx]))
                    #     print(sentence)
                    #     print(len(y_ner))


                    # 对预测结果进行命名实体解析和提取
                    result_words = get_valid_nertag(sent_chars, y_ner)
                    for (word, tag) in result_words:
                        print("".join(word), tag)
                        f2.write("".join(word) + '\t' + tag + '\n')

    with open(save_path+'.list','w',encoding='utf-8') as f4:
        for i in range(len(cha_ners)):
            # f4.write(cha_ners[i] + '\t' + ture_lables[i] + '\t' + pre_labels[i] + '\n')
            if ture_lables[i]=='O' and pre_labels[i]!='O':
                # print(entity,t_label,p_label)
                f4.write(cha_ners[i] + '\t' + ture_lables[i] + '\t' + pre_labels[i] + '\t'+'0'+'\n')
                # f2.write(str(index)+'\t'+entity+'\t'+t_label+'\t'+p_label+'\n')

            elif ture_lables[i]!='O' and pre_labels[i]=='O':
                # print(entity, t_label, p_label)
                f4.write(cha_ners[i] + '\t' + ture_lables[i] + '\t' + pre_labels[i] + '\t'+'0'+'\n')
            elif ture_lables[i]!=pre_labels[i]:
                # print(entity, t_label, p_label)
                f4.write(cha_ners[i] + '\t' + ture_lables[i] + '\t' + pre_labels[i] + '\t'+'0'+'\n')
            else:
                f4.write(cha_ners[i] + '\t' + ture_lables[i] + '\t' + pre_labels[i] + '\t'+'1'+'\n')

if __name__ == '__main__':

    train()
    # file_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.train.data'
    # file_label_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\data\水稻玉米小麦大豆大麦_shuffle_4.txt.ann.train'
    # save_path = r'D:\博士期间相关资料\理论知识相关\知识图谱\知识图谱源码\ChineseNERAnno\bilstm-crf-ner-train-5000.txt'
    # val(file_path,file_label_path, save_path)

