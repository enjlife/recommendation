import pymysql
import pandas as pd
import jieba
import jieba.analyse
import re
import matplotlib
import requests
import string
import logging


host1 = '172.16.22.105'
host2 = '172.16.16.97'  # 服务器的库
host3 = '172.16.13.178'
host4 = 'localhost'
sql_select1 = "select * from companys "

title = "中文".encode("utf8")
sql_insert1 = "insert into companys(cid,company_name) values(%s,%s)"

sql_delete1 = 'delete from companys where cid=136'

# 连接数据库
def sql_connect(host="localhost",port=3306,user='root',passwd='654321',db='test',charset='utf8'):
    connect = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db, charset=charset)
    cur = connect.cursor()
    return connect,cur

def sql_execute(connect,cur,sqlcmd=sql_select1):
    # logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    cmdlist = sqlcmd.split(" ")
    if cmdlist[0]=="select":
        cur.execute(sqlcmd)
        print(cur.rowcount)
        data = cur.fetchone()
        return data
    elif cmdlist[0]=="insert":
        try:
            cur.execute(sqlcmd,('136',title))
            connect.commit()
        except Exception as e:
            print(e)
            connect.rollback()  # 捕获到异常并回滚事务
    elif cmdlist[0]=="delete":

        try:
            cur.execute(sqlcmd)
            connect.commit()
        except Exception as e:
            print(e)
            connect.rollback()  # 捕获到异常并回滚事务


    cur.close()
    connect.close()
    # a = pd.read_sql(sqlcmd1, connect)

connect,cur = sql_connect()
sql_execute(connect,cur,sqlcmd=sql_delete1)


