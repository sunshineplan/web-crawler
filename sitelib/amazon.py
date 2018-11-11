#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import Request
from urllib.request import urlopen
from gzip import decompress
from math import ceil
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

class Amazon():
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.agent = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36 OPR/56.0.3051.99'
            ]
        self.accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        self.acceptEncoding = 'gzip, deflate, br'
        self.acceptLanguage = 'en-US,en;q=0.9'
        self.headers = {'Accept': self.accept, 'Accept-Encoding': self.acceptEncoding, 'Accept-Language': self.acceptLanguage}
        self.fieldnames = ['Name', 'Author', 'Price', 'URL']
        self.storepath = path
        self.filename = 'amazon' + strftime('%Y%m%d') + '-' + self.keyword + '.csv'

    def getHeaders(self):
        for attempts in range(5):
            try:
                url = 'https://www.amazon.cn'
                agent = self.agent[randint(0, 4)]
                logger.debug('User-Agent: %s', agent)
                headers = dict(self.headers, **{'User-Agent': agent})
                request = Request(url, headers=headers)
                html = urlopen(request)
                setCookies = html.info().get_all('Set-Cookie')
                cookies = []
                for i in setCookies:
                    if '=-' in i:
                        continue
                    if 'session-id' in i:
                        cookies.append(i[:i.find(';')])
                        sessionId = i[i.find('=')+1:i.find(';')]
                    else:
                        cookies.append(i[:i.find(';')])
                url = 'https://www.amazon.cn/gp/prime/digital-adoption/navigation-bar/{0}?type=load&isPrime=false'.format(sessionId)
                for repeats in range(2):
                    request = Request(url, headers=dict(headers, **{'Cookie': ';'.join(cookies)}))
                    html = urlopen(request)
                    setCookies = html.info().get_all('Set-Cookie')
                    for i in setCookies:
                        if '=-' in i:
                            continue
                        else:
                            cookies.append(i[:i.find(';')])
                cookies = ';'.join(list(set(cookies)))
                if cookies == []:
                    raise
                break
            except:
                logger.error('Failed to get headers. Please wait to retry...')
                sleep(30)
        logger.debug('Cookies: %s', cookies)
        return {'Cookie':cookies, 'User-Agent': agent}

    def getPage(self, headers):
        url = 'https://www.amazon.cn/s/ref=sr_pg_1?rh=n:658390051,k:{0}'.format(self.quoteKeyword)
        html = self.openUrl(url, headers)
        if html.find('h1', id='noResultsTitle') is not None:
            logger.info('我们找到了与 "%s" 相关的 0 条 结果', self.keyword)
            sys.exit()
        result = html.find('span', id='s-result-count').text
        _, record = result.split('共')
        record = ''.join(i for i in record if i.isdigit())
        page = ceil((int(record)/16))
        if page > 75:
            page = 75
        logger.info('Keyword: %s, Total records: %s, Total pages: %s', self.keyword, record, page)
        return page

    def openUrl(self, url, headers):
        for attempts in range(10):
            try:
                logger.debug('Opening url %s', url)
                request = Request(url, headers=dict(self.headers, **headers))
                html = urlopen(request)
                break
            except:
                logger.error('Encounter error when opening %s', url)
                sleep(30)
        html = BeautifulSoup(decompress(html.read()), 'html.parser')
        return html

    def parse(self, content, headers):
        content = content.find_all('li', id=re.compile('result_'))
        if content == []:
            raise
        bookList = []
        result = []
        for i in content:
            bookList.append(i['data-asin'])
        for id in bookList:
            record, headers = self.parseBook(id, headers)
            result += record
            sleep(4)
        return result, headers

    def parseBook(self, id, headers):
        result = []
        url = 'https://www.amazon.cn/dp/{0}'.format(id)
        for attempts in range(3):
            try:
                html = self.openUrl(url, headers)
                name = html.find('span', id='productTitle')
                if name is None:
                    name = html.find('span', id='ebooksProductTitle')
                author = html.find('span', class_='author')
                price = html.find('span', class_='offer-price')
                if price is None:
                    try:
                        price = html.find('tr', class_='kindle-price')
                        price = price.find('td', class_='a-color-price')
                    except:
                        try:
                            price = html.find('div', id='buybox')
                            price = price.find('span', class_='a-color-price')
                        except:
                            pass
                record = {}
                record['Name'] = name.text.strip()
                if price is not None:
                    record['Price'] = price.text.replace('￥', '').strip()
                if author is not None:
                    record['Author'] = author.a.text.strip()
                record['URL'] = url
                result.append(record)
                break
            except:
                logger.error('Failed to get book info. Please wait to retry...')
                sleep(30)
                headers = self.getHeaders()
        return result, headers

    def run(self):
        beginTime=time()
        url = 'https://www.amazon.cn/s/ref=sr_pg_1?rh=n:658390051,k:{0}&page={1}&sort=date-desc-rank'
        for attempts in range(10):
            try:
                headers = self.getHeaders()
                page = self.getPage(headers)
                break
            except:
                logger.error('Failed to get page number. Please wait to retry...')
                sleep(30)
                page = None
        if not page:
            logger.critical('Failed to get page number. Exiting...')
            sys.exit()
        i = 1
        result = []
        while i <= page:
            for attempts in range(5):
                try:
                    html = self.openUrl(url.format(self.quoteKeyword, i), headers)
                    record, headers = self.parse(html, headers)
                    result += record
                    i += 1
                    error = 0
                    break
                except:
                    logger.error('Failed to parse contents. Please wait to retry...')
                    sleep(30)
                    try:
                        headers = self.getHeaders()
                    except:
                        pass
                    error = 1
        if error == 1:
            logger.error('Job was interrupted, not all results were outputted.')
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
        job = Amazon(sys.argv[1], sys.argv[2])
        job.run()
    elif len(sys.argv) == 2:
        job = Amazon(sys.argv[1])
        job.run()
    else:
        logger.critical('Wrong number of arguments.')
