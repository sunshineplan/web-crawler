#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import sys
import ssl
try:
    from bs4 import BeautifulSoup
except ImportError:
    from subprocess import check_call
    check_call([sys.executable, '-m', 'pip', 'install', 'beautifulsoup4'])
    from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import build_opener
from urllib.request import HTTPSHandler
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import thread
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
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s(%(threadName)s) - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

class Taobao():
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.opener = build_opener(HTTPSHandler(context=context))
        self.fieldnames = ['Title', 'Price', 'Sales', 'Location', 'Shop', 'Comments', 'Category', 'URL']
        self.storepath = path
        self.filename = 'TB' + strftime('%Y%m%d') + '-' + self.keyword + '.csv'

    def openUrl(self, url):
        for attempts in range(10):
            try:
                logger.debug('Opening url %s', url)
                html = self.opener.open(url).read()
                break
            except:
                logger.error('Encounter error when opening %s', url)
                sleep(30)
        html = BeautifulSoup(html, 'html.parser')
        g_page_config = html.find('script', text=re.compile('g_page_config'))
        g_page_config = json.loads(re.search(r'g_page_config = (.*?);\n', g_page_config.text).group(1))
        return g_page_config

    def getPage(self):
        g_page_config = self.openUrl('https://s.taobao.com/search?q={0}'.format(self.quoteKeyword))
        page = g_page_config['mods']['sortbar']['data']['pager']['totalPage']
        count = g_page_config['mods']['sortbar']['data']['pager']['totalCount']
        if count == 0:
            logger.info('没有找到与“%s”相关的宝贝', self.keyword)
            raise Warning('No Results Found')
        logger.info('Keyword: %s, Total pages: %s, Total counts: %s', self.keyword, page, count)
        return range(1,int(page)+1)

    def parse(self, page):
        url = 'https://s.taobao.com/search?q={0}&s={1}'
        itemList = self.openUrl(url.format(self.quoteKeyword, page * 44 - 44))['mods']['itemlist']['data']['auctions']
        result = []
        for i in itemList:
            record = {}
            record['Title'] = i.get('raw_title')
            record['Price'] = i.get('view_price')
            record['Sales'] = i.get('view_sales').replace('人付款', '')
            record['Location'] = i.get('item_loc')
            record['Shop'] = i.get('nick')
            record['Comments'] = i.get('comment_count')
            record['Category'] = i.get('category')
            if i.get('detail_url'):
                record['URL'] = 'https:' + i.get('detail_url')
            result.append(record)
        return result

    def run(self):
        beginTime=time()
        for attempts in range(3):
            try:
                page = self.getPage()
                break
            except KeyboardInterrupt:
                logger.info('Job cancelled. Exiting...')
                return
            except Warning:
                return
            except:
                logger.error('Failed to get page number. Please wait to retry...')
                sleep(30)
                page = None
        if not page:
            logger.critical('Failed to get page number. Exiting...')
            return
        result = []
        with ThreadPoolExecutor(10, 'TBT') as executor:
            try:
                return_list = list(executor.map(self.parse, page))
            except KeyboardInterrupt:
                logger.info('Job cancelled. Exiting...')
                executor._threads.clear()
                thread._threads_queues.clear()
                return
            for record in return_list:
                result += record
        try:
            fullpath = saveCSV(self.filename, self.fieldnames, result, self.storepath)
        except FileNotFoundError:
            logger.error('Failed to write output file, no such directory: "%s". Use current directory instead.', self.storepath)
            fullpath = saveCSV(self.filename, self.fieldnames, result)
        except PermissionError:
            logger.error('Failed to write output file, destination file may be locked. Use current directory and temporary filename instead.')
            fullpath = saveCSV('temp'+'{:04}'.format(randint(0, 9999))+'.csv', self.fieldnames, result)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', fullpath)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        job = Taobao(sys.argv[1], sys.argv[2])
        job.run()
    elif len(sys.argv) == 2:
        job = Taobao(sys.argv[1])
        job.run()
    else:
        logger.critical('Wrong number of arguments.')
