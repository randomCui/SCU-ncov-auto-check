import csv
import os
import time

import requests

CAPTCHA_URL = 'https://ua.scu.edu.cn/captcha?captchaId=8595993631'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

abs_path = os.path.abspath(__file__)
dir_path = os.path.dirname(abs_path)
img_path = 'img'

current_milli_time = lambda: str(round(time.time() * 1000))

for i in range(500):
    time.sleep(10)
    with requests.Session() as s:
        img_response = s.get(CAPTCHA_URL,
                             headers=headers)
        current_time = current_milli_time()
        path = os.path.join(dir_path, img_path, current_time) + '.png'
        with open(path, 'wb') as f:
            f.write(img_response.content)
            f.close()
            print("success in saving img", path)
        with open(os.path.join(dir_path, img_path, 'data.csv'), 'a', newline='') as c:
            writer = csv.writer(c)
            writer.writerow([current_time + '.png'])
