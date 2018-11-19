#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import ssl
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

class JD():
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.opener = build_opener(HTTPSHandler(context=context))
        self.opener.addheaders.append(('Referer','https://search.jd.com/Search?keyword={0}&enc=utf-8'.format(self.quoteKeyword)))
        self.fieldnames = ['Name', 'Price', 'URL']
        self.storepath = path
        self.filename = 'JD' + strftime('%Y%m%d') + '-' + self.keyword + '.csv'

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
        sleep(1.5)
        return soupContent

    def getPage(self):
        html = self.openUrl('https://search.jd.com/Search?keyword={0}&enc=utf-8'.format(self.quoteKeyword))
        if html.find('div', class_='check-error') is not None:
            logger.info('汪~没有找到商品。Exiting...')
            raise Warning('No Results Found')
        page = html.find('span', class_='fp-text').i.text
        logger.info('Keyword: %s, Total pages: %s', self.keyword, page)
        return range(1,int(page)+1)

    def parse(self, page):
        url = 'https://search.jd.com/s_new.php?keyword={0}&enc=utf-8&psort=6&page={1}&s={2}'
        html1 = self.openUrl(url.format(self.quoteKeyword, page * 2 - 1, page * 60 - 59))
        html2 = self.openUrl(url.format(self.quoteKeyword, page * 2, page * 60 - 29) + '&scrolling=y')
        content = html1.find_all('li', class_='gl-item')
        content += html2.find_all('li', class_='gl-item')
        result = []
        for i in content:
            name = i.find('div', class_='p-name')
            price = i.find('div', class_='p-price')
            url = i.find('div', class_='p-name')
            record = {}
            try:
                record['Name'] = name.a.em.text.strip()
                record['Price'] = price.strong.i.text.strip()
                if url is not None:
                    record['URL'] = 'https:' + url.a['href']
                result.append(record)
            except:
                logger.warning('A corrupted record was skipped.(Page: %s)', page)
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
        with ThreadPoolExecutor(10, 'JDT') as executor:
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
        job = JD(sys.argv[1], sys.argv[2])
        job.run()
    elif len(sys.argv) == 2:
        job = JD(sys.argv[1])
        job.run()
    else:
        logger.critical('Wrong number of arguments.')
