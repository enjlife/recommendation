import jieba
import csv
import re
import os
import logging
import random
import math
from gensim.models import word2vec
import data_process
import datetime
from word2vec_train import sim_test
from data_connect import sql_connect
from data_connect import sql_execute
from params import args


class Itemcf(object):
    def __init__(self,host="localhost",passwd="654321",db="test",data_from="sql",filename='/Users/enjlife/Desktop/announcement.csv'):
        self.trainSet = {}
        self.testSet = {}
        self.host=host
        self.passwd=passwd
        self.db=db
        self.data_from=data_from
        self.filename = filename
        # 先将时间设成未达到开标时间
        #self.now_time = datetime.datetime.now()
        self.now_time = datetime.datetime.strptime("2018-01-01 11:26:00",'%Y-%m-%d %H:%M:%S')

        # 用户相似度矩阵
        self.item_sim_matrix = {}
        self.word_sim_matrix = {}
        self.testitem = data_process.get_test_item(host=host, passwd=passwd, db=db)  # 包含新的项目信息的列表
        self.item_popular = {}
        self.item_count = 0

    # 基于项目的相似度计算
    def recommend_item_cf(self):
        for user, movies in self.trainSet.items():
            for m1 in movies:
                for m2 in movies:
                    if m1 == m2:
                        continue
                    self.item_sim_matrix.setdefault(m1, {})
                    self.item_sim_matrix[m1].setdefault(m2, 0)
                    self.item_sim_matrix[m1][m2] += 1
        print("Build co-rated users matrix success!")

        # 计算项目之间的相似性
        print("Calculating movie similarity matrix ...")
        for m1, related_items in self.item_sim_matrix.items():
            for m2, count in related_items.items():
                # 注意0向量的处理
                if self.item_popular[m1] == 0 or self.item_popular[m2] == 0:
                    self.item_sim_matrix[m1][m2] = 0
                else:
                    self.item_sim_matrix[m1][m2] = count / math.sqrt(self.item_popular[m1] * self.item_popular[m2])
        print('Calculate movie similarity matrix success!')

    # 基于内容的推荐
    def recommend_content(self):
        # docu = os.getcwd()
        model = word2vec.Word2Vec.load('./announce.model')
        self.trainSet = self.get_dataset2()
        result = {}
        for oneitem in self.testitem:
            if not self.time_compare(oneitem[2]):
                return "The item is out of date"
            comp_its = {}  # 1.保存公司相似度数值
            for comp, its in self.trainSet.items():  # its是一个包含多个项目信息的list
                # sim_sum = 0  # title相似度加和
                for i, it in enumerate(its):  # it是一个包含项目信息的列表

                    it_title_sim, _ = self.calc_words(it[0], oneitem[0], model, topn=5)
                    it_cate_sim = self.calc_cate(it[1], oneitem[1])
                    it_mon_sim = self.money_compare(oneitem[3],it[3])
                    sim_sum = it_title_sim + it_cate_sim + it_mon_sim
                    comp_its[comp + '+'+str(it[6])] = [it_title_sim, it_cate_sim, it_mon_sim, sim_sum]
            sorted_comp = sorted(comp_its.items(), key=lambda x: x[1][3], reverse=True)[:5]
            result[oneitem[5]] = sorted_comp
        self.write_sql(result)
    def get_dataset1(self,filename,pivot=0.75):
        trainSet_len = 0
        testSet_len = 0
        for line in self.load_file(filename):
            comp,it,money,ti = line.split(',')
            if(random.random() < pivot):
                self.trainSet.setdefault(comp, {})
                self.trainSet[comp][it] = 0
                trainSet_len += 1
            else:
                self.testSet.setdefault(comp, {})
                self.testSet[comp][it] = 0
                testSet_len += 1
        print('Split trainingSet and testSet success!')
        print('TrainSet = %s' % trainSet_len)
        print('TestSet = %s' % testSet_len)
    # 导入数据，暂时未划分训练集和测试集
    # 数据以公司名为字典

    def get_dataset2(self):
        if self.data_from=="sql":
            train_data = {}
            announce_data = data_process.load_data_sql(host=self.host,passwd=self.passwd,db=self.db)
            for oneline in announce_data:
                if oneline[5] not in train_data:
                    train_data[oneline[5]] = []
                train_data[oneline[5]].append(oneline)
            # 对金额为0.0的取该公司项目的平均值
            for comp, its in train_data.items():

                mon = 0.0
                for it in its:

                    mon += it[3]
                for it in its:
                    if it[3] == 0.0:
                        it[3] = mon / len(its)
            # print(train_data)
            return train_data
        else:
            train_data = {}
            announce_data = data_process.load_data_csv(self.filename)
            for oneline in announce_data:
                if oneline[4] not in train_data:
                    train_data[oneline[4]] = []
                train_data[oneline[4]].append([oneline[0], oneline[5], oneline[10], oneline[12], oneline[7]])
            # 对金额为0.0的取该公司项目的平均值
            for comp, its in train_data.items():
                mon = 0.0
                for it in its:
                    mon += it[3]
                for it in its:
                    if it[3] == 0.0:
                        it[3] = mon / len(its)
            return train_data
    def read_result(self,result):
        out_result = {}
        for key, value in result.items():
            out_result[key] = []
            for v1 in value:
                out_result[key].append(v1[0].split("+")[1])
            out_result[key] = list(set(out_result[key]))
        return out_result


    def write_sql(self,result):
        out_result = self.read_result(result)
        sql_insert1 = "insert into refer(cid,gid,re) values(%s,%s,%s)"
        connect, cur = sql_connect(host=self.host, passwd=self.passwd, db=self.db)
        try:
            for key,value in out_result.items():
                for v in value:
                    cur.execute(sql_insert1,(str(key),str(v),str(1)))
            connect.commit()
            print("Data saved!")
        except Exception as e:
            print("failed to write!!")
            print(e)
            connect.rollback()
        cur.close()
        connect.close()

    # 计算两个单词的相似性
    def calc_words(self,it1,it2,model,topn):

        for m1 in it1:
            for m2 in it2:
                twosim = m1+"+"+m2
                self.word_sim_matrix[twosim] = sim_test(model,m1,m2)
        sortlistm1 = sorted(self.word_sim_matrix.items(), key=lambda x: x[1], reverse=False)[:topn]

        meansim = 0.0
        for m1 in sortlistm1:
            meansim += m1[1]
        meansim = meansim/topn
        return meansim,sortlistm1
    # 计算所属类目的相似性
    def calc_cate(self,cate1,cate2):
        if cate2 == '':
            return 0.0
        if cate1==['']:
            return 0.0
        elif cate2 in cate1:
            return cate1.index(cate2)/10
        else: return 0.0
    def time_compare(self,time1):
        if time1 == None:
            return 1
        time1 = datetime.datetime.strptime(str(time1), '%Y-%m-%d %H:%M:%S')
        if (time1-self.now_time).days > 0:
            return 1
        else:
            return 0
    def money_compare(self,newmon,mon):
        if newmon == '':
            return 0.0
        diff = newmon-mon
        differ = diff if diff >= 0 else -diff
        if mon == 0.0: return 0.4
        elif 0 < differ/mon <= 0.1: return 1
        elif 0.1 < differ/mon <= 0.5: return 0.8
        elif 0.5 < differ/mon <= 1.0: return 0.6
        elif 1.0 < differ/mon <= 2.0: return 0.4
        else: return 0.2


    # 导入数据划分训练集和测试集
    # 读文件，返回文件的每一行
    def load_file(self, filename):
        with open(filename, 'r') as f:
            for i, line in enumerate(f):
                # if i == 0:  # 去掉文件第一行的title
                #     continue
                yield line.strip('\r\n')
        print('Load %s success!' % filename)

    # 产生推荐并通过准确率、召回率和覆盖率进行评估
    def evaluate(self):
        print('Evaluating start ...')
        N = self.n_rec_movie
        # 准确率和召回率
        hit = 0
        rec_count = 0
        test_count = 0
        # 覆盖率
        all_rec_movies = set()

        for i, user in enumerate(self.trainSet):
            test_moives = self.testSet.get(user, {})
            rec_movies = self.recommend(user)
            for movie, w in rec_movies:
                if movie in test_moives:
                    hit += 1
                all_rec_movies.add(movie)
            rec_count += N
            test_count += len(test_moives)

        precision = hit / (1.0 * rec_count)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_movies) / (1.0 * self.movie_count)
        print('precisioin=%.4f\trecall=%.4f\tcoverage=%.4f' % (precision, recall, coverage))
def main():
    file_name = '/Users/enjlife/Desktop/announcement.csv'
    test_file_name = '/Users/enjlife/Desktop/test.csv'
    out_file = "/Users/enjlife/Desktop/announcement.txt"
    # item = []
    # item.append(input("请输入项目信息:"))
    # item.append(input("请输入类目:"))
    # item.append(input("请输入项目开标时间:"))
    # item.append(input("请输入项目金额:"))
    #
    # newitem = data_process.new_item_process(item)
    # newitem = [['天津大学', '信网', '中心', '与', '分析', '平台', '建设项目'], ['工程', '建筑安装工程'], '2019-07-08  09:30', 30.0, '天津市']
    Test = Itemcf(host=args.host,passwd=args.passwd,db=args.db,data_from=args.data_from)
    # Test = Itemcf()
    Test.recommend_content()

if __name__=='__main__':
    main()














