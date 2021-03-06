#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
from concurrent.futures import ThreadPoolExecutor, thread
from random import randint
from time import sleep, strftime, time
from urllib.parse import quote
from urllib.request import build_opener

from bs4 import BeautifulSoup

from crawler.lib.output import saveCSV

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('web-crawler.log')
# fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s(%(threadName)s) - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


class dangdang:
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.opener = build_opener()
        self.fieldnames = ['Name', 'Now Price',
                           'List Price', 'Author', 'Publisher', 'ISBN', 'URL']
        self.storepath = path
        self.filename = 'DD' + strftime('%Y%m%d') + '-' + self.keyword + '.csv'

    def openUrl(self, url):
        for _ in range(3):
            try:
                logger.debug('Opening url %s', url)
                html = self.opener.open(url).read()
                break
            except:
                logger.error('Encounter error when opening %s', url)
                html = None
                sleep(5)
        if html:
            return BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        else:
            raise Exception

    def getPage(self):
        html = self.openUrl(
            f'http://search.dangdang.com/?key={self.quoteKeyword}')
        if html.find(attrs={'name': 'noResult_correct'}):
            logger.info('抱歉，没有找到商品。Exiting...')
            raise Warning('No Results Found')
        content = html.find_all(attrs={'name': 'bottom-page-turn'})
        pageList = []
        for i in content:
            pageList.append(i.text)
        try:
            page = int(pageList[-2])
        except:
            page = 1
        logger.info('Keyword: %s, Total pages: %s', self.keyword, page)
        return range(1, int(page)+1)

    def parse(self, page):
        url = 'http://search.dangdang.com/?key={0}&sort_type=sort_pubdate_desc&page_index={1}'
        try:
            html = self.openUrl(url.format(self.quoteKeyword, page))
        except:
            logger.error('Failed to get page %s content', page)
        html = html.find_all('li', class_=re.compile('line'))
        result = []
        for i in html:
            name = i.find('a', attrs={'name': 'itemlist-title'})
            now_price = i.find('span', class_='search_now_price')
            list_price = i.find('span', class_='search_pre_price')
            author = i.find_all('a', attrs={'name': 'itemlist-author'})
            publisher = i.find('a', attrs={'name': 'P_cbs'})
            url = i.find('a', attrs={'name': 'itemlist-title'})
            record = {}
            try:
                record['Name'] = name.text.strip()
                record['Now Price'] = now_price.text.replace('¥', '').strip()
                if list_price is not None:
                    record['List Price'] = list_price.text.replace(
                        '¥', '').strip()
                if author is not None:
                    author_list = []
                    for i in author:
                        author_list.append(i.text.strip())
                    record['Author'] = ','.join(author_list)
                if publisher is not None:
                    record['Publisher'] = publisher.text.strip()
                if url is not None:
                    record['URL'] = url['href']
                    try:
                        ISBN = self.openUrl(url['href']).find(
                            'li', text=re.compile('国际标准书号ISBN'))
                        if ISBN:
                            record['ISBN'] = ISBN.text.split('：')[-1]
                    except:
                        pass
                result.append(record)
            except:
                logger.warning(
                    'A corrupted record was skipped.(Page: %s)', page)
        sleep(2)
        return result

    def run(self):
        beginTime = time()
        for _ in range(3):
            try:
                page = self.getPage()
                break
            except KeyboardInterrupt:
                logger.info('Job cancelled. Exiting...')
                return
            except Warning:
                return
            except:
                logger.error(
                    'Failed to get page number. Please wait to retry...')
                sleep(30)
                page = None
        if not page:
            logger.critical('Failed to get page number. Exiting...')
            return
        result = []
        with ThreadPoolExecutor(10, 'DDT') as executor:
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
            fullpath = saveCSV(self.filename, self.fieldnames,
                               result, self.storepath)
        except FileNotFoundError:
            logger.error(
                'Failed to write output file, no such directory: "%s". Use current directory instead.', self.storepath)
            fullpath = saveCSV(self.filename, self.fieldnames, result)
        except PermissionError:
            logger.error(
                'Failed to write output file, destination file may be locked. Use current directory and temporary filename instead.')
            fullpath = saveCSV(
                'temp'+'{:04}'.format(randint(0, 9999))+'.csv', self.fieldnames, result)
        timeCost = '%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', fullpath)
