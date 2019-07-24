from gensim.models import word2vec
import logging

def train(input_file):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    # 打开语料文本
    sentences = word2vec.Text8Corpus(input_file)
    model = word2vec.Word2Vec(sentences, hs=1, min_count=1, window=5, size=100)
    model.save('announce.model')
def load_model(filename):
    model = word2vec.Word2Vec.load('announce.model')
    return model

# 相似度计算
def sim_test(model,str1,str2):
    try:
        sim1 = model.similarity(str1,str2)
    except KeyError:
        return 0.0
    return sim1

def sim_word(model,str1):
    try:
        sim = model.most_similar(str1, topn=20)
        print(u'和'+str1+'与相关的词有：\n')
        for key in sim:
            print(key[0], key[1])
    except:
        print('error')





