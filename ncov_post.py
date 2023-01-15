import base64
import hashlib
import json
import logging
import os
import re
import time

import bs4
import requests

from UA_login_structure import UA_login_form

UA_front_302 = r"https://wfw.scu.edu.cn/ncov/wap/default/index"
UA_front = r'https://ua.scu.edu.cn/login?service=https%3A%2F%2Fwfw.scu.edu.cn%2Fa_scu%2Fapi%2Fsso%2Fcas-index%3Fredirect%3Dhttps%253A%252F%252Fwfw.scu.edu.cn%252Fncov%252Fwap%252Fdefault%252Findex'
UA_login = r'https://ua.scu.edu.cn/login'

UA_captcha_url = r'https://ua.scu.edu.cn/captcha'
captcha_break_url = r'http://localhost:19952/captcha/v1'

wfw_save_url = r'https://wfw.scu.edu.cn/ncov/wap/default/save'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}

abs_path = os.path.abspath(__file__)
dir_path = os.path.dirname(abs_path)
captcha_img_200 = r"img_200"
captcha_img_401 = r"img_401"


def extract_cookie_include_history(response):
    cookies = {}
    for key, value in response.cookies.get_dict().items():
        cookies[key] = value
    for history in response.history:
        for key, value in history.cookies.get_dict().items():
            cookies[key] = value
    return cookies


def save_captcha_img(img_response, status_code, predict_captcha):
    filename = predict_captcha + "_" + md5(img_response.content)
    if status_code == requests.codes['ok']:
        path = os.path.join(dir_path, captcha_img_200, filename) + '.png'
    elif status_code == requests.codes['unauthorized']:
        path = os.path.join(dir_path, captcha_img_401, filename) + '.png'
    else:
        return
    with open(path, 'wb') as f:
        f.write(img_response.content)


def md5(b_content):
    hash_md5 = hashlib.md5(b_content)
    return hash_md5.hexdigest()


# def ncov_post_handler(ID, password):
#     pass


class NcovPostHandler:
    def __init__(self, stu_id: str, password: str, cookie: dict = None):
        self.s = requests.Session()
        self.cookie = cookie
        self.stu_id = stu_id
        self.password = password

        # 以下是登录进平台需要的属性
        self.img_response = None
        self.captcha_code = None
        self.login_form = UA_login_form
        self.execution_string = None

        self.wfw_response = None

        # 以下是打卡所需内容
        self.info_to_post = None

    def init_session(self) -> (requests.Response, dict[str, str]):
        try:
            scu_ua_platform_page = self.s.get(UA_front_302, headers=headers)
        except ConnectionError as err:
            logging.warning('访问登录页面失败')
            raise err
        cookie = extract_cookie_include_history(scu_ua_platform_page)
        return scu_ua_platform_page, cookie

    def login_with_password(self) -> bool:
        response_page, self.cookie = self.init_session()
        captcha_id = self.extract_captcha_image_id(response_page.text)
        self.execution_string = self.extract_execution_string(response_page.text)
        self.img_response = self.get_captcha_image_by_id(captcha_id)
        self.captcha_code = self.break_captcha(self.img_response)

        time.sleep(10)

        self.build_login_form()

        if not self.post_login_form():
            # 说明登录失败
            return False
        else:
            # 说明登录成功
            return True

    def login(self):
        if self.cookie is None:
            self.login_with_password()
        else:
            if not self.login_with_cookie():
                self.login_with_password()

    def get_last_data(self):
        return self.build_post_info_from_page()

    def post_data(self):
        return self.post_info_to_server()

    def login_with_cookie(self) -> bool:
        self.wfw_response = self.s.get(UA_front_302,
                                       cookies=self.cookie,
                                       headers=headers
                                       )
        return "ua.scu.edu.cn/login" not in self.wfw_response.url

    def post_info_to_server(self):
        assert self.info_to_post is not None
        res = self.s.post(wfw_save_url,
                           data=self.info_to_post,
                           headers=headers,
                          cookies=self.cookie
                           )
        return res

    def build_post_info_from_page(self) -> dict:
        match = re.search(r"oldInfo: ({.*?})", self.wfw_response.text, flags=re.S)
        old_info = json.loads(match.group(1))
        match1 = re.search(r"var def = ({.*?})", self.wfw_response.text, flags=re.S)
        info_to_send = json.loads(match1.group(1))
        # 将要发送的数据先填上昨天的数据
        for key, value in old_info.items():
            if key not in ["jzxgymrq","jzdezxgymrq","date","created","szsqsfybl","id"]:
                info_to_send[key] = value

        # 这些数据一般都不需要填
        info_to_send["gwszdd"] = ""  # 国外所在地点
        info_to_send["sfyqjzgc"] = ""  # 是否疫情居家观察
        info_to_send["jrsfqzys"] = ""  # 今日是否确诊疑似
        info_to_send["jrsfqzfy"] = ""  # 今日是否确诊发热
        info_to_send["szgjcs"] = ""  # 所在国家城市

        self.info_to_post = info_to_send
        return info_to_send

    @staticmethod
    def extract_captcha_image_id(login_page_text: str) -> str:
        try:
            capture = re.search(r"id: '(\d*)'", login_page_text, flags=re.S)
            captcha_id = capture.group(1)
            # 捕获到的验证码id应该为10位，否则说明捕获错误
            assert len(captcha_id) == 10

        except AssertionError as err:
            logging.critical('验证码id捕获错误，可能是登录页面发生变化')
            raise err

        return captcha_id

    @staticmethod
    def extract_execution_string(login_page_text: str) -> str:
        soup = bs4.BeautifulSoup(login_page_text, 'html.parser')
        execution_string = soup.find('input', {'name': 'execution'})['value']
        return execution_string

    def get_captcha_image_by_id(self, captcha_id: str) -> bytes:
        img_response = self.s.get(UA_captcha_url,
                                  headers=headers,
                                  params={
                                      "captchaId": captcha_id
                                  })
        if img_response.status_code == requests.codes['ok']:
            return img_response.content
        else:
            logging.warning('验证码图片获取失败')

    @staticmethod
    def break_captcha(captcha_img: bytes) -> str:
        captcha_break_response = requests.post(captcha_break_url,
                                               json={
                                                   "image": base64.b64encode(captcha_img).decode('UTF-8')
                                               })
        captcha_code = captcha_break_response.json()['message']
        logging.info(f"识别验证码成功，结果为{captcha_code}")
        return captcha_code

    def build_login_form(self) -> None:
        assert self.stu_id is not None and \
               self.password is not None and \
               self.execution_string is not None and \
               self.captcha_code is not None

        self.login_form['username'] = self.stu_id
        self.login_form['password'] = self.password
        self.login_form['execution'] = self.execution_string
        self.login_form['captcha'] = self.captcha_code

    def post_login_form(self) -> bool:
        self.wfw_response = self.s.post(
            url=UA_login,
            data=UA_login_form
        )
        for key, value in extract_cookie_include_history(self.wfw_response).items():
            self.cookie[key] = value
        return self.wfw_response.status_code == requests.codes["ok"]


# def ncov_post(ID, password):
#     failed_retry = 0
#     while (failed_retry < 5):
#         with requests.Session() as s:
#             page = s.get(UA_front_302, headers=headers)
#             cookie = extract_cookie_include_history(page)
#             soup = bs4.BeautifulSoup(page.text, 'html.parser')
#             script_text = soup.select("script")[3].text
#             captcha_data = re.search(r"id: '(\d*)'", script_text, flags=re.S)
#             captcha_id = captcha_data.group(1)
#             captcha_payload = {
#                 'captchaId': captcha_id
#             }
#
#             img_response = s.get(UA_captcha_url,
#                                  headers=headers,
#                                  params=captcha_payload)
#             if img_response.status_code == requests.codes['ok']:
#                 logging.info(f"成功获取验证码图片\t\t\t\t<httpRespond>[{img_response.status_code}]")
#                 # print("成功获取验证码图片\t\t\t", end='')
#             else:
#                 logging.warning(f"获取图片失败\t\t\t<httpRespond>[{img_response.status_code}]")
#                 # print("获取图片失败\t\t", end='')
#             # print("<httpResponse[%d]>" % img_response.status_code)
#
#             execution_string = soup.find('input', {'name': 'execution'})['value']
#
#             logging.info(f"将图片转发至本地验证码服务器...\t\t{captcha_break_url}")
#             # print("将图片转发至本地验证码服务器...\t\t%s" % captcha_break_url)
#             break_time = time.time()
#             base64EncodedStr = base64.b64encode(img_response.content)
#             captcha_to_break = {
#                 'image': base64EncodedStr.decode('utf-8')
#             }
#             captcha_break_response = requests.post(captcha_break_url, json=captcha_to_break)
#             captcha_break = json.loads(captcha_break_response.text)
#             break_time = time.time() - break_time
#             if captcha_break_response.status_code == requests.codes['ok']:
#                 logging.info(f"获取预测验证码成功\t预测结果为: {captcha_break['message']} \t[{break_time:.3f}s]")
#                 # print("获取预测验证码成功\t", end='')
#             else:
#                 logging.warning(f"获取预测失败")
#                 # print("获取预测失败\t", end='')
#                 continue
#
#             # print("预测结果为: %s \t[%.3fs]" % (captcha_break['message'], break_time))
#
#             UA_login_form['username'] = ID
#             UA_login_form['password'] = password
#             UA_login_form['execution'] = execution_string
#             UA_login_form['captcha'] = captcha_break['message']
#
#             wfw_response = s.post(
#                 url=UA_login,
#                 data=UA_login_form
#             )
#
#             # 根据是否成功登陆微服务决定保存在哪个文件夹中
#             save_captcha_img(img_response, wfw_response.status_code, captcha_break['message'])
#
#             if wfw_response.status_code == requests.codes['ok']:
#                 logging.info(f"验证成功，正在进入填报页面...\t\t<httpResponse[{wfw_response.status_code}]>")
#                 # print("验证成功，正在进入填报页面...\t\t", end='')
#                 # print("<httpResponse[%d]>" % wfw_response.status_code)
#                 break
#             elif wfw_response.status_code == requests.codes['unauthorized']:
#                 logging.info(f"验证失败，正在进行第[{failed_retry + 1}]次重试\t\t<httpResponse[{wfw_response.status_code}]>")
#                 # print("验证失败，正在进行第[%d]次重试\t\t" % failed_retry, end='')
#                 # print("<httpResponse[%d]>" % wfw_response.status_code)
#                 failed_retry += 1
#
#     if failed_retry >= 5:
#         logging.warning("无法登陆统一认证平台，请检查账号密码是否正确")
#         # print("无法登陆统一认证平台，请检查账号密码是否正确")
#         return {'e': 2, 'm': '无法登陆统一认证平台，请检查账号密码是否正确', 'd': {}}, cookie
#
#     soup1 = bs4.BeautifulSoup(wfw_response.text, 'html.parser')
#     info = soup1.select("script", {"type": "text/javascript"})[10].text
#     result = re.findall(r"oldInfo: (.*),", info, flags=re.S & re.M)
#     result_new = re.findall(r'def = (.*?);', info, flags=re.S & re.M)
#     info_new = json.loads(result_new[0])
#     # 按照上一次的接着填报
#     info_old = json.loads(result[0])
#
#     # for key, value in info_new.items():
#     #     try:
#     #         if value != info_old[key]:
#     #             print(key,"\n" , value,"\n", info_old[key])
#     #     except KeyError:
#     #         print(key)
#     #         print(KeyError)
#
#     info_new['address'] = info_old['address']
#     info_new['area'] = info_old['area']
#     info_new['city'] = info_old['city']
#     info_new['ismoved'] = 0
#
#     save_response = s.post(url=wfw_save_url, headers=headers, data=info_new)
#     if save_response.json()['e'] == 0:
#         logging.info(f"打卡成功\t\t\t\t<httpResponse[{save_response.status_code}]>")
#         # print('打卡成功\t\t\t\t', end='')
#         #
#         # print("<httpResponse[%d]>" % save_response.status_code)
#     else:
#         logging.warning(f"打卡失败:{save_response.json()}\t<httpResponse[{save_response.status_code}]>")
#         # print('打卡失败,失败信息:', end='')
#         # print(save_response.json()['m'] + '\t', end='')
#         # print("<httpResponse[%d]>\t" % save_response.status_code, end='')
#         # print("Error code:%d" % save_response.json()['e'])
#     return save_response.json(), cookie


if __name__ == '__main__':
    handler = NcovPostHandler()
    handler.login()
    print(handler.get_last_data())
    print(handler.post_data().text)
