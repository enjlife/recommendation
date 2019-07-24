import jieba
import csv
import re
import logging
import string
from data_connect import sql_connect
from data_connect import sql_execute


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
file_name = '/Users/enjlife/Desktop/announcement.csv'
out_file = "/Users/enjlife/Desktop/announcement.txt"

# 导入csv数据
def load_data_csv(file_name=file_name, out_file=out_file):
    announce_data = []
    with open(file_name, encoding="GB18030") as csvfile:
        csv_reader = csv.reader(csvfile)  # 使用csv.reader读取csvfile中的文件
        data_header = next(csv_reader)  # 读取第一行每一列的标题

        for row in csv_reader:  # 将csv文件中的数据保存到birth_data中
            announce_data.append(row)
    data = title_process(announce_data,data_from="csv")
    return data
# 导入sql数据
def load_data_sql(host="localhost",passwd="654321",db="test"):

    connect,cur = sql_connect(host=host,passwd=passwd,db=db)
    cur.execute("select g.gname,g.bid_time,g.classify,g.price,g.producer,c.company_name,c.cid from goods g join refer r on g.gid=r.gid join companys c on c.cid=r.cid where r.uid<30;")
    data = cur.fetchall()
    data = title_process(data,data_from="sql")
    cur.close()
    connect.close()
    print("train data loaded")
    return data
# 导入test数据
def get_test_item(host="localhost", passwd="654321", db="test"):
    connect, cur = sql_connect(host=host, passwd=passwd, db=db)
    # cur.execute("select title,time2,category,money,location,gid from announce where gid>100;")
    cur.execute("select gname,bid_time,classify,price,producer,gid from goods where gid>60;")
    data = cur.fetchall()
    data = title_process(data,data_from="sql",test=True)
    cur.close()
    connect.close()
    print("test data loaded")
    return data

# 数据过滤
def title_process(announce_data,data_from="sql",test=False):
    if data_from == "sql":
        data = []
        for i,oneline in enumerate(announce_data):
            subdata = []
            line = delpunctuation(oneline[0])
            seg_list = seg(line)
            subdata.append(seg_list)
            # 对品类进行划分
            if oneline[2]==None:
                subdata.append([])
            else:
                subdata.append(oneline[2].split("/"))

            subdata.append(oneline[1])

            subdata.append(float(oneline[3]))
            subdata.append(oneline[4])
            subdata.append(oneline[5])
            if not test:
                subdata.append(oneline[6])
            data.append(subdata)

        return data
    else:
        for oneline in announce_data:
            line = delpunctuation(oneline[0])
            seg_list = seg(line)
            oneline[0] = seg_list
            # 对品类进行划分
            oneline[5] = oneline[5].split("/")
            oneline[10] = oneline[10].replace("年", "-").replace("月", "-").replace("日", "")
            if oneline[12] == "详见公告正文":
                oneline[12] = 0.0
            else:
                oneline[12] = float(oneline[12].strip("￥").strip("万元（人民币）"))
        return announce_data




# 去除标点符号(中文+英文)
def delpunctuation(str):
    line = re.sub(r'[0-9\s+\.\!\/_,$%^*()?;；:-【】+\"\']+|[+——！，;：。？、~@#￥%……&*（）]+', '', str)
    return line

# 分词
def seg(line):
    seg_list = [str for str in jieba.cut(line) if str not in ['-', '公开招标', '公告', '招标', '项目']]
    return seg_list


# def removePunctuation(text):
#     # 去掉字符串中标点符号
#     temp = []
#     for c in text:
#         # punctuation 不包含中文字符
#         if c not in string.punctuation:
#             temp.append(c)
#     newTextt = ''.join(temp)
#     newText = newTextt.replace(' ', '')#去掉空格
#     return newText


# with open(file_name,encoding="GB18030") as csvfile:
#     csv_reader = csv.reader(csvfile)  # 使用csv.reader读取csvfile中的文件
#     birth_header = next(csv_reader)  # 读取第一行每一列的标题
#     for row in csv_reader:  # 将csv 文件中的数据保存到birth_data中
#         birth_data.append(row)
# birth_data = [row[0] for row in birth_data]  # 将数据从string形式转换为float形式
# N = len(birth_data)
# seg_dict = {}
# target = open(out_file,'w',encoding='utf8')
# for i in range(0,N):
#     line = re.sub(r'[0-9\s+\.\!\/_,$%^*()?;；:-【】+\"\']+|[+——！，;：。？、~@#￥%……&*（）]+','', birth_data[i])
#     seg_list = [str for str in jieba.cut(line) if str not in ['-','公开招标','公告','招标']]
#     seg_dict[i] = seg_list
#     target.writelines(" ".join(seg_list)+'\n')
# print(seg_dict)
# target.close()


#



