#!/usr/bin/python3
# coding:utf-8

import os
from csv import DictWriter


def saveCSV(filename, fieldnames, content, path=''):
    path = path.strip('"')
    if path != '':
        if os.name == 'nt':
            path = path + '\\'
        else:
            path = path + '/'
    fullpath = path + filename
    fullpath = os.path.abspath(fullpath)
    with open(fullpath, 'w', encoding='utf-8-sig', newline='') as output_file:
        output = DictWriter(output_file, fieldnames, extrasaction='ignore')
        output.writeheader()
        output.writerows(content)
    return fullpath
