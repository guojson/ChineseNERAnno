# -*- coding: utf-8 -*-
# @Author  : guoxuchao
# @time    : 2019-12-15 20:56
# @File    : SQLiteTools.py
# @Software: PyCharm
import sys
import os
import sqlite3

# sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
# sys.path.append("..")


class ConnectSqlite:

    def __init__(self, dbName="../configs/corpus_info.db"):
        """
        初始化连接--使用完记得关闭连接
        :param dbName: 连接库名字，注意，以'.db'结尾
        """
        self._conn = sqlite3.connect(dbName)
        self._cur = self._conn.cursor()
        self._time_now = "[" + sqlite3.datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + "]"

    def close_con(self):
        """
        关闭连接对象--主动调用
        :return:
        """
        self._cur.close()
        self._conn.close()

    def create_tabel(self, sql):
        """
        创建表初始化
        :param sql: 建表语句
        :return: True is ok
        """
        try:
            self._cur.execute(sql)
            self._conn.commit()
            return True
        except Exception as e:
            print(self._time_now, "[CREATE TABLE ERROR]", e)
            return False

    def drop_table(self, table_name):
        """
        删除表
        :param table_name: 表名
        :return:
        """
        try:
            self._cur.execute('DROP TABLE {0}'.format(table_name))
            self._conn.commit()
            return True
        except Exception as e:
            print(self._time_now, "[DROP TABLE ERROR]", e)
            return False

    def delete_table(self, sql):
        """
        删除表记录
        :param sql:
        :return: True or False
        """
        try:
            if 'DELETE' in sql.upper():
                self._cur.execute(sql)
                self._conn.commit()
                return True
            else:
                print(self._time_now, "[EXECUTE SQL IS NOT DELETE]")
                return False
        except Exception as e:
            print(self._time_now, "[DELETE TABLE ERROR]", e)
            return False

    def fetchall_table(self, sql, limit_flag=True):
        """
        查询所有数据
        :param sql:
        :param limit_flag: 查询条数选择，False 查询一条，True 全部查询
        :return:
        """
        try:
            self._cur.execute(sql)
            war_msg = self._time_now + ' The [{}] is empty or equal None!'.format(sql)
            if limit_flag is True:
                r = self._cur.fetchall()
                return r if len(r) > 0 else -1
            elif limit_flag is False:
                r = self._cur.fetchone()
                return r if len(r) > 0 else -1
        except Exception as e:
            print(self._time_now, "[SELECT TABLE ERROR]", e)

    def insert_update_table(self, sql):
        """
        插入/更新表记录
        :param sql:
        :return:
        """
        try:
            self._cur.execute(sql)
            self._conn.commit()
            return True
        except Exception as e:
            print(self._time_now, "[INSERT/UPDATE TABLE ERROR]", e)
            return False

    def insert_table_many(self, sql, value):
        """
        插入多条记录
        :param sql:
        :param value: list:[(),()]
        :return:
        """
        try:
            self._cur.executemany(sql, value)
            self._conn.commit()
            return True
        except Exception as e:
            print(self._time_now, "[INSERT MANY TABLE ERROR]", e)
            return False


class conTest:
    """测试类"""

    def __init__(self):
        self.con = ConnectSqlite("./corpus_info.db")

    def create_table_test(self):
        sql = '''CREATE TABLE `category` (
                  `id` INTEGER(12) DEFAULT 0,
                  `des` VARCHAR(12) DEFAULT NULL,
                  `color` VARCHAR(12) DEFAULT NULL,
                  `ann` VARCHAR(12) DEFAULT NULL
                )'''
        print(self.con.create_tabel(sql))

    def drop_table_test(self):
        print(self.con.drop_table("mytest"))

    def fetchall_table_test(self):
        sql = "SELECT * from category WHERE user='1003';"
        sql_all = "SELECT * from category;"
        print("全部记录", self.con.fetchall_table(sql_all))
        print("单条记录", self.con.fetchall_table(sql_all, False))
        print("条件查询", self.con.fetchall_table(sql))

    def delete_table_test(self):
        sql = "DELETE FROM mytest WHERE user='1003';"
        print(self.con.delete_table(sql))

    def update_table_test(self):
        sql_update = "UPDATE mytest SET id={0},user={1},name={2},number={3} WHERE number={4}".format(1, 1002, "'王五'",
                                                                                                     1002,
                                                                                                     1002)
        print(self.con.insert_update_table(sql_update))

    def insert_table_test_one(self):
        sql = """INSERT INTO mytest VALUES (3, 1003, "王五", 1003);"""
        print(self.con.insert_update_table(sql))

    def insert_table_test_many(self):
        sql = """INSERT INTO category VALUES (?, ?, ?, ?)"""
        value = [(0,'作物', '#FF4500', 'CRO'), (1, '病害','"#FFBBFF', "DIS")]
        print(self.con.insert_table_many(sql, value))

    def close_con(self):
        self.con.close_con()


if __name__ == '__main__':
    contest = conTest()
    # contest.create_table_test()
    # contest.insert_table_test_many()
    contest.fetchall_table_test()
    # contest.insert_table_test_one()
    # contest.fetchall_table_test()
    # contest.update_table_test()
    # contest.drop_table_test()
    contest.close_con()
