#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import build_opener
from time import sleep

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('web-crawler.log')
#fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

class dangdang():
    def __init__(self, keyword):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.opener = build_opener()
        self.page = self.getPage()

    def openUrl(self, url):
        for attempts in range(10):
            try:
                html = self.opener.open(url).read()
                break
            except:
                logger.error('[Error]Encounter error when opening %s', url)
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
            logger.info('抱歉，没有找到商品。Exiting...')
            sys.exit()
        content = html.find_all(attrs={'name':'bottom-page-turn'})
        pageList = []
        for i in content:
            pageList.append(i.text)
        try:
            page = int(pageList[-2])
        except:
            page = 1
        logger.info('Keyword: %s, Total pages: %s', self.keyword, page)
        return page

    def run(self):
        url = 'http://search.dangdang.com/?key={0}&sort_type=sort_pubdate_desc&page_index={1}'
        i = 1
        while i <= self.page:
            self.parse(self.openUrl(url.format(self.quoteKeyword, i)))
            i += 1
            sleep(2)


if __name__ == "__main__":
    job = dangdang(sys.argv[1])
    job.run()
