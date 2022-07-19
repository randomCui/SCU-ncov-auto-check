import hashlib
import csv
import os
from shutil import copy

abs_path = os.path.abspath(__file__)
dir_path = os.path.dirname(abs_path)
img_path = 'img'
data_path = 'data'

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

if __name__ == '__main__':
    with open(os.path.join(dir_path, img_path, 'data_1.csv'), 'r') as c:
        reader = csv.reader(c)
        for line in reader:
            filename = line[0]
            value = line[1]
            if value == '':
                break
            md5hash = md5(os.path.join(dir_path, img_path, filename))
            copy(os.path.join(dir_path, img_path, filename),
                os.path.join(dir_path, data_path, value+'_'+md5hash+'.png')
                )


