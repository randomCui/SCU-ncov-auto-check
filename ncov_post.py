import base64
import json
import re
import time

import bs4
import requests

from UA_login_structure import UA_login_form

UA_front = r'https://ua.scu.edu.cn/login?service=https%3A%2F%2Fwfw.scu.edu.cn%2Fa_scu%2Fapi%2Fsso%2Fcas-index%3Fredirect%3Dhttps%253A%252F%252Fwfw.scu.edu.cn%252Fncov%252Fwap%252Fdefault%252Findex'
UA_login = r'https://ua.scu.edu.cn/login'

UA_captcha_url = r'https://ua.scu.edu.cn/captcha'
captcha_break_url = r'http://localhost:19952/captcha/v1'

wfw_save_url = r'https://wfw.scu.edu.cn/ncov/wap/default/save'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}


def ncov_post(ID, password):
    failed_retry = 0
    while (failed_retry < 5):
        with requests.Session() as s:
            page = s.get(UA_front, headers=headers)
            soup = bs4.BeautifulSoup(page.text, 'html.parser')
            script_text = soup.select("script")[3].text
            captcha_data = re.search(r"id: '(\d*)'", script_text, flags=re.S)
            captcha_id = captcha_data.group(1)
            captcha_payload = {
                'captchaId': captcha_id
            }

            img_response = s.get(UA_captcha_url,
                                 headers=headers,
                                 params=captcha_payload)
            if img_response.status_code == requests.codes['ok']:
                print("成功获取验证码图片\t\t\t", end='')
            else:
                print("获取图片失败\t\t", end='')
            print("<httpResponse[%d]>" % img_response.status_code)

            execution_string = soup.find('input', {'name': 'execution'})['value']

            print("将图片转发至本地验证码服务器...\t\t%s" % captcha_break_url)
            break_time = time.time()
            base64EncodedStr = base64.b64encode(img_response.content)
            captcha_to_break = {
                'image': base64EncodedStr.decode('utf-8')
            }
            captcha_break_response = requests.post(captcha_break_url, json=captcha_to_break)
            captcha_break = json.loads(captcha_break_response.text)
            break_time = time.time() - break_time
            if captcha_break_response.status_code == requests.codes['ok']:
                print("获取预测验证码成功\t", end='')
            else:
                print("获取预测失败\t", end='')
                continue

            print("预测结果为: %s \t[%.3fs]" % (captcha_break['message'], break_time))

            UA_login_form['username'] = ID
            UA_login_form['password'] = password
            UA_login_form['execution'] = execution_string
            UA_login_form['captcha'] = captcha_break['message']

            wfw_response = s.post(
                url=UA_login,
                data=UA_login_form
            )
            if wfw_response.status_code == requests.codes['ok']:
                print("验证成功，正在进入填报页面...\t\t", end='')
                print("<httpResponse[%d]>" % wfw_response.status_code)
                break
            elif wfw_response.status_code == requests.codes['unauthorized']:
                print("验证失败，正在进行第[%d]次重试\t\t" % failed_retry, end='')
                print("<httpResponse[%d]>" % wfw_response.status_code)
                failed_retry += 1

    if failed_retry >= 5:
        print("无法登陆统一认证平台，请检查账号密码是否正确")
        return {'e': 2, 'm': '无法登陆统一认证平台，请检查账号密码是否正确', 'd': {}}

    soup1 = bs4.BeautifulSoup(wfw_response.text, 'html.parser')
    info = soup1.select("script", {"type": "text/javascript"})[10].text
    result = re.findall(r"oldInfo: (.*),", info, flags=re.S & re.M)
    # 按照上一次的接着填报
    info_1 = json.loads(result[0])
    info_1["gwszdd"] = ''
    info_1["sfyqjzgc"] = ''
    info_1["jrsfqzys"] = ''
    info_1["jrsfqzfy"] = ''
    info_1["ismoved"] = '0'
    info_1["szgjcs"] = ''

    # info_1_payload = json.dumps(info_1)
    # print(info_1_payload)

    save_response = s.post(url=wfw_save_url, headers=headers, data=info_1)
    if save_response.json()['e'] == 0:
        print('打卡成功\t\t\t\t', end='')
        print("<httpResponse[%d]>" % save_response.status_code)
    else:
        print('打卡失败,失败信息:', end='')
        print(save_response.json()['m'] + '\t', end='')
        print("<httpResponse[%d]>" % save_response.status_code)
    return save_response.json()


if __name__ == '__main__':
    ncov_post('', '')
