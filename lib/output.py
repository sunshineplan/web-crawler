#!/usr/bin/python3
# coding:utf-8

from csv import DictWriter

def saveCSV(filename, fieldnames, content):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as output_file:
        output = DictWriter(output_file, fieldnames, extrasaction='ignore')
        output.writeheader()
        output.writerows(content)
