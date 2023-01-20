import datetime
import json
import logging
import os
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta

from ncov_post import NcovPostHandler, Status

"""
数据库配置
"""
conn = sqlite3.connect('ncov_db.sqlite')
cur = conn.cursor()

"""
日志数据配置
"""
LOG_FILE_PATH = os.getcwd() + "/logs"
if not os.path.exists(LOG_FILE_PATH):
    os.makedirs(LOG_FILE_PATH)

LOG_FILE = LOG_FILE_PATH + "/" + datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d %H_%M_%S') + ".log"
LOG_FILE_INFO = LOG_FILE_PATH + "/ez_" + datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d %H_%M_%S') + ".log"

logFormatter = logging.Formatter("[%(levelname)s]\t[%(asctime)s] [%(module)s:%(lineno)d]\t%(message)s")

file_handler = logging.FileHandler(f"{LOG_FILE}")
file_handler.setFormatter(logFormatter)

file_info_handler = logging.FileHandler(f"{LOG_FILE_INFO}")
file_info_handler.setFormatter(logFormatter)
file_info_handler.setLevel(logging.INFO)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(
    logging.Formatter("[%(levelname)s] [%(asctime)s] [%(module)s:%(lineno)d]\t%(message)s", datefmt="%d-%m-%Y %H:%M:%S")
)

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.NOTSET)

rootLogger.addHandler(file_handler)
rootLogger.addHandler(stream_handler)
rootLogger.addHandler(file_info_handler)


def second_to_next_hour(trigger_time: datetime) -> float:
    now = datetime.now()
    due = trigger_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return (due - now).total_seconds()


def post_trigger():
    logging.info(f"开始一轮打卡")
    start = datetime.now()
    next_trigger = one_round_post()
    delta = datetime.now()-start
    logging.info(f"本轮打卡结束,总用时{str(delta).split('.')[0]+'.'+str(delta).split('.')[1][:3]},距离下次检查还有{next_trigger:.1f}s")
    time.sleep(next_trigger)


def one_round_post() -> float:
    post_count = 0
    cur.execute("SELECT stu_id, password, cookie, enable FROM user")
    pending_user_list = cur.fetchall()
    for user in pending_user_list:
        cur2 = conn.cursor()
        cur2.execute("SELECT post_time FROM save_history WHERE stu_id=?", (user[0],))
        record = cur2.fetchone()
        if record is None or datetime.fromtimestamp(record[0]).day != datetime.now().day:
            # 如果查询不到今天有一条打卡记录，就进行一次打卡
            post_for_one_user(user)
            post_count += 1
    logging.info(f"本轮共打卡{post_count}人")
    return second_to_next_hour(datetime.now())


def post_for_one_user(user):
    cur1 = conn.cursor()
    if not user[3]:
        logging.info(f"{user[0]}关闭自动打卡")
    logging.info(f"正在构造{user[0]}的handler")
    handler = NcovPostHandler(user[0], user[1], json.loads(user[2]))
    match handler.login(2):
        case Status.success:
            logging.info(f"{user[0]}登录成功")
        case Status.reach_max_retry:
            logging.warning(f"{user[0]}登陆重试次数过多,登陆失败")
            cur1.execute("INSERT INTO save_history VALUES(?,?,?,?,?,?)",
                         (user[0], time.time(), None, None, None, Status.reach_max_retry.value))
            conn.commit()
            return
        case Status.cookie_failed_and_no_pwd:
            logging.warning(f"{user[0]}用户cookie失效,并且没有提供账号密码,无法登录")
            cur1.execute("INSERT INTO save_history VALUES(?,?,?,?,?,?)",
                         (user[0], time.time(), None, None, None, Status.cookie_failed_and_no_pwd.value))
            conn.commit()
            return

    is_cookie_updated = (handler.get_cookie() != json.loads(user[2]))
    if is_cookie_updated:
        logging.info(f"{user[0]}cookie已更新")
        cur1.execute("UPDATE user SET cookie=? WHERE stu_id=?",
                     (json.dumps(handler.get_cookie()), user[0])
                     )
    last_post_data = handler.get_last_data()
    result = handler.post_data().json()
    logging.info(f"{user[0]}打卡完成,结果为{result}")
    cur1.execute("INSERT INTO save_history VALUES(?,?,?,?,?,?)",
                 (user[0],
                  time.time(),
                  json.dumps(last_post_data, ensure_ascii=False),
                  json.dumps(result, ensure_ascii=False),
                  json.dumps(handler.get_cookie()),
                  Status.success.value)
                 )
    conn.commit()
    sleep_sec = random.random() * 20
    logging.info(f"数据保存完成,线程暂停{sleep_sec: .3f}s")
    time.sleep(sleep_sec)


if __name__ == "__main__":
    while True:
        post_trigger()
