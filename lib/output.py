#!/usr/bin/python3
# coding:utf-8

from csv import DictWriter

def saveCSV(filename, fieldnames, content, encoding='utf-8'):
    with open(filename, 'w', encoding=encoding, newline='') as output_file:
        output = DictWriter(output_file, fieldnames, extrasaction='ignore')
        output.writeheader()
        output.writerows(content)
