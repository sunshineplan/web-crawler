#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import build_opener
from time import sleep
from time import time
from time import strftime
sys.path.append("..")
from lib.output import saveCSV

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
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.path = path
        self.opener = build_opener()
        self.opener.addheaders.append(('Referer','https://search.jd.com/Search?keyword={0}&enc=utf-8'.format(self.quoteKeyword)))
        self.page = self.getPage()
        self.fieldnames = ['Name', 'Price', 'URL']
        self.filename = 'jingdong' + strftime('%Y%m%d') + '.csv'

    def openUrl(self, url):
        for attempts in range(10):
            try:
                logger.debug('Opening url %s', url)
                html = self.opener.open(url).read()
                break
            except:
                logger.error('Encounter error when opening %s', url)
                sleep(30)
        soupContent = BeautifulSoup(html, 'html.parser')
        return soupContent

    def parse(self, content):
        content = content.find_all('li', class_='gl-item')
        result = []
        for i in content:
            name = i.find('div', class_='p-name').a.em
            price = i.find('div', class_='p-price').strong.i
            url = 'https:' + i.find('div', class_='p-name').a['href']
            record = {}
            if name is not None:
                record['Name'] = name.text.strip()
            if price is not None:
                record['Price'] = price.text.strip()
            record['URL'] = url
            result.append(record)
        return result

    def getPage(self):
        html = self.openUrl('https://search.jd.com/Search?keyword={0}&enc=utf-8'.format(self.quoteKeyword))
        if html.find('div', class_='check-error') is not None:
            logger.info('汪~没有找到商品。Exiting...')
            sys.exit()
        page = html.find('span', class_='fp-text').i.text
        logger.info('Keyword: %s, Total pages: %s', self.keyword, page)
        return page

    def run(self):
        beginTime=time()
        url = 'https://search.jd.com/s_new.php?keyword={0}&enc=utf-8&psort=6&page={1}&s={2}'
        page = int(self.page)
        i = 1
        result = []
        while i < page * 2 + 1:
            result += self.parse(self.openUrl(url.format(self.quoteKeyword, i, (i - 1) * 30 + 1)))
            i += 1
            sleep(1.5)
            result += self.parse(self.openUrl(url.format(self.quoteKeyword, i, (i - 1) * 30 + 1) + '&scrolling=y'))
            i += 1
            sleep(1.5)
        try:
            fullpath = saveCSV(self.filename, self.fieldnames, result, self.path)
        except FileNotFoundError:
            logger.error('No such directory: "%s", use currect directory instead.', self.path)
            fullpath = saveCSV(self.filename, self.fieldnames, result)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', fullpath)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        job = JD(sys.argv[1], sys.argv[2])
        job.run()
    elif len(sys.argv) == 2:
        job = JD(sys.argv[1])
        job.run()
    else:
        logger.critical('Wrong number of arguments.')
