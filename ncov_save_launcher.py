import sqlite3
import time
import threading
import random

from ncov_post import ncov_post

global_update = time.localtime().tm_min
check_period = 600


def mday_from_second(x):
    return time.localtime(x).tm_mday


def current_mday():
    return time.localtime().tm_mday


need_to_post = False

while True:
    conn = sqlite3.connect('ncov_save_list.db')
    c = conn.cursor()
    c1 = conn.cursor()
    if need_to_post:
        cursor = c.execute("SELECT ROWID, STUDENT_ID, PASSWORD, LAST_SAVE_DATE, ENABLE from NCOV_ACCOUNT")

        first_failed_rowid = []

        # e: -1 出现未知错误
        # e: 0 操作成功
        # e: 1 今天已经填报过了
        # e: 2 无法登录验证平台，检查账号密码
        # e: 3 网络连接失败
        # e: 4 网络连接超时

        time_start = time.time()
        for index, id, password, last_save_date,enable in c:
            # 手动超控
            if enable == 0:
                print("第[%d]个人手动关闭打卡功能" % index)
                continue
            # 如果正常执行,status会被之后的返回值更新,只有在出现未catch的异常时才会将这条写入数据库
            status, cookie = {'e': -1, 'm': '出现未知错误', 'd': {}}, {'eai-sess': None, 'UUkey': None}
            if last_save_date is not None and mday_from_second(last_save_date) != current_mday():
                print('正在为第%d个人打卡' % index)
                try:
                    status, cookie = ncov_post(id, password)
                    c1.execute("UPDATE NCOV_ACCOUNT set LAST_SAVE_DATE = ?,FORMATTED_DATE= ? where ROWID=?",
                               (time.time(), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), index))
                except ConnectionError:
                    print('此人打卡出现异常')
                    first_failed_rowid.append(index)
                    status = {'e': 3, 'm': '网络连接失败', 'd': {}}
                except TimeoutError:
                    print('连接超时')
                    first_failed_rowid.append(index)
                    status = {'e': 4, 'm': '网络连接超时', 'd': {}}

            elif last_save_date is None:
                print('正在为第%d个新人打卡' % index)
                try:
                    status, cookie = ncov_post(id, password)
                    c1.execute("UPDATE NCOV_ACCOUNT set LAST_SAVE_DATE = ?,FORMATTED_DATE= ? where ROWID=?",
                               (time.time(), time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), index))
                except ConnectionError:
                    print("此人打卡出现异常")
                    first_failed_rowid.append(index)
                    status = {'e': 3, 'm': '网络连接失败', 'd': {}}
                except TimeoutError:
                    print('连接超时')
                    first_failed_rowid.append(index)
                    status = {'e': 4, 'm': '网络连接超时', 'd': {}}

            else:
                print('第%d个人今天已经打过了' % index)
                continue
            if status['e'] == 2 or status['e'] == 3 or status['e'] == 4:
                c1.execute("UPDATE NCOV_ACCOUNT set FAILED_ATTEMPT = ? where ROWID = ?", (1, index))
            c1.execute("INSERT INTO NCOV_SAVE_HISTORY (STUDENT_ID, TIMESTAMP, STATUS_CODE, MESSAGE, DETAIL, FORMATTED_DATE, EAI_SESS, UUID)\
            VALUES (?,?,?,?,?,?,?,?)", (id, time.time(), status['e'], status['m'], str(status['d']),
                                        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), cookie['eai-sess'],
                                        cookie['UUkey']))
            conn.commit()

        elapsed_time = time.time() - time_start
        print("本轮打卡总用时为%.3fs\n" % elapsed_time)
        conn.close()

        # print(first_failed_rowid)

    if current_mday() == global_update:
        current_time = time.localtime()
        time_wait = (60 - current_time.tm_min) * 60 + (60 - current_time.tm_sec)
        print("%s 全部填报完毕,下一次检查在%d秒后" % (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), time_wait))
        need_to_post = False
        time.sleep(time_wait)
    else:
        print("%s还未填报,正在启动填报" % time.strftime('%Y-%m-%d', time.localtime()))
        global_update = current_mday()
        need_to_post = True
