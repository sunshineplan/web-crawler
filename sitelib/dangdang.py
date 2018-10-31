#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import build_opener
from time import sleep


class dangdang():
    def __init__(self, keyword):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.page = self.getPage()
        self.opener = build_opener()

    def openUrl(self, url):
        for attempts in range(10):
            try:
                html = self.opener.open(url).read()
                break
            except:
                print('[Error]Encounter error when opening ' + url)
                sleep(30)
        soupContent = BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        return soupContent

    def parse(self, html):
        html = html.find_all('li', class_=re.compile('line'))
        for i in html:
            name = i.find('p', class_='name').a.text
            price = i.find('span', class_='search_now_price').text
            try:
                print(name + price.replace('¥', '$'))
            except:
                pass

    def getPage(self):
        html = self.openUrl('http://search.dangdang.com/?key={0}'.format(self.quoteKeyword))
        if html.find(attrs={'name':'noResult_correct'}) is not None:
            print('抱歉，没有找到商品。')
            sys.exit()
        content = html.find_all(attrs={'name':'bottom-page-turn'})
        pageList = []
        for i in content:
            pageList.append(i.text)
        try:
            page = int(pageList[-2])
        except:
            page = 1
        return page

    def run(self):
        url = 'http://search.dangdang.com/?key={0}&sort_type=sort_pubdate_desc&page_index={1}'
        i = 1
        while i <= self.page:
            self.parse(self.openUrl(url.format(self.quoteKeyword, i)))
            i += 1
            sleep(2)
        print('\n结果总共' + str(page) + '页')


if __name__ == "__main__":
    job = dangdang(sys.argv[1])
    job.run()
