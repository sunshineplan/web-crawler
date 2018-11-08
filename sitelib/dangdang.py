#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import build_opener
from time import sleep
from time import time
from time import strftime
from random import randint
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

class dangdang():
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.opener = build_opener()
        self.page = self.getPage()
        self.fieldnames = ['Name', 'Now Price', 'List Price', 'Author', 'Publisher', 'URL']
        self.storepath = path
        self.filename = 'dangdang' + strftime('%Y%m%d') + '-' + self.keyword + '.csv'

    def openUrl(self, url):
        for attempts in range(10):
            try:
                logger.debug('Opening url %s', url)
                html = self.opener.open(url).read()
                break
            except:
                logger.error('Encounter error when opening %s', url)
                sleep(30)
        soupContent = BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        return soupContent

    def parse(self, html):
        html = html.find_all('li', class_=re.compile('line'))
        result = []
        for i in html:
            name = i.find('a', attrs={'name':'itemlist-title'})
            now_price = i.find('span', class_='search_now_price')
            list_price = i.find('span', class_='search_pre_price')
            author = i.find_all('a', attrs={'name':'itemlist-author'})
            publisher = i.find('a', attrs={'name':'P_cbs'})
            url = i.find('a', attrs={'name':'itemlist-title'})['href']
            record = {}
            if name is not None:
                record['Name'] = name.text.strip()
            if now_price is not None:
                record['Now Price'] = now_price.text.replace('¥', '').strip()
            if list_price is not None:
                record['List Price'] = list_price.text.replace('¥', '').strip()
            if author is not None:
                author_list = []
                for i in author:
                    author_list.append(i.text.strip())
                record['Author'] = ','.join(author_list)
            if publisher is not None:
                record['Publisher'] = publisher.text.strip()
            record['URL'] = url
            result.append(record)
        return result

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
        beginTime=time()
        url = 'http://search.dangdang.com/?key={0}&sort_type=sort_pubdate_desc&page_index={1}'
        i = 1
        result = []
        while i <= self.page:
            result += self.parse(self.openUrl(url.format(self.quoteKeyword, i)))
            i += 1
            sleep(2)
        try:
            fullpath = saveCSV(self.filename, self.fieldnames, result, self.storepath)
        except FileNotFoundError:
            logger.error('No such directory: "%s", use current directory instead.', self.storepath)
            fullpath = saveCSV(self.filename, self.fieldnames, result)
        except PermissionError:
            logger.error('Failed to write output file, use current directory and temporary filename instead.')
            fullpath = saveCSV('temp'+'{:04}'.format(randint(0, 9999))+'.csv', self.fieldnames, result)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', fullpath)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        job = dangdang(sys.argv[1], sys.argv[2])
        job.run()
    elif len(sys.argv) == 2:
        job = dangdang(sys.argv[1])
        job.run()
    else:
        logger.critical('Wrong number of arguments.')
