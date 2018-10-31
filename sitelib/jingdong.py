#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
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

class JD():
    def __init__(self, keyword):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.opener = build_opener()
        self.opener.addheaders.append(('Referer','https://search.jd.com/Search?keyword={0}&enc=utf-8'.format(self.quoteKeyword)))
        self.page = self.getPage()

    def openUrl(self, url):
        for attempts in range(10):
            try:
                html = self.opener.open(url).read()
                break
            except:
                logger.error('[Error]Encounter error when opening %s', url)
                sleep(30)
        soupContent = BeautifulSoup(html, 'html.parser')
        return soupContent

    def parse(self, content):
        content = content.find_all('li', class_='gl-item')
        for i in content:
            name = i.find('div', class_='p-name').a.em.text
            price = i.find('div', class_='p-price').strong.i.text
            try:
                print(name + '$' + price)
            except:
                pass

    def getPage(self):
        html = self.openUrl('https://search.jd.com/Search?keyword={0}&enc=utf-8'.format(self.quoteKeyword))
        if html.find('div', class_='check-error') is not None:
            logger.info('汪~没有找到商品。Exiting...')
            sys.exit()
        page = html.find('span', class_='fp-text').i.text
        logger.info('Keyword: %s, Total pages: %s', self.keyword, page)
        return page

    def run(self):
        url = 'https://search.jd.com/s_new.php?keyword={0}&enc=utf-8&psort=6&page={1}&s={2}'
        page = int(self.page)
        i = 1
        while i < page * 2 + 1:
            self.parse(self.openUrl(url.format(self.quoteKeyword, i, (i - 1) * 30 + 1)))
            i += 1
            sleep(1.5)
            self.parse(self.openUrl(url.format(self.quoteKeyword, i, (i - 1) * 30 + 1) + '&scrolling=y'))
            i += 1
            sleep(1.5)


if __name__ == "__main__":
    job = JD(sys.argv[1])
    job.run()
