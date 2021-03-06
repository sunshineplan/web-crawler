#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, thread
from functools import partial
from gzip import decompress
from math import ceil
from queue import SimpleQueue
from random import randint
from time import sleep, strftime, time
from urllib.parse import quote
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from crawler.lib.comm import getAgent
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


class Amazon:
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.agent, error = getAgent(10)
        if error == 0:
            logger.debug('Getting user agents list successful.')
        else:
            logger.error(
                'Getting user agents list failed. Use custom list instead.')
        self.accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        self.acceptEncoding = 'gzip, deflate, br'
        self.acceptLanguage = 'en-US,en;q=0.9'
        self.headers = {'Accept': self.accept, 'Accept-Encoding': self.acceptEncoding,
                        'Accept-Language': self.acceptLanguage}
        self.fieldnames = ['Name', 'Author', 'Price', 'URL']
        self.storepath = path
        self.filename = 'AZ' + strftime('%Y%m%d') + '-' + self.keyword + '.csv'

    def getHeaders(self):
        for _ in range(10):
            try:
                url = 'https://www.amazon.cn'
                agent = self.agent[randint(0, len(self.agent)-1)]
                logger.debug('User-Agent: %s', agent)
                headers = dict(self.headers, **{'User-Agent': agent})
                request = Request(url, headers=headers)
                logger.debug('Getting Headers: Step 1')
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
                url = 'https://www.amazon.cn/gp/prime/digital-adoption/navigation-bar/{0}?type=load&isPrime=false'.format(
                    sessionId)
                step = 2
                for _ in range(2):
                    sleep(randint(2, 5))
                    request = Request(url, headers=dict(
                        headers, **{'Cookie': ';'.join(cookies)}))
                    logger.debug('Getting Headers: Step %s', step)
                    html = urlopen(request)
                    setCookies = html.info().get_all('Set-Cookie')
                    for i in setCookies:
                        if '=-' in i:
                            continue
                        else:
                            cookies.append(i[:i.find(';')])
                    step += 1
                cookies = ';'.join(list(set(cookies)))
                if cookies == []:
                    logger.debug('Getting Headers: Step Extra')
                    raise ValueError('Empty cookies.')
                break
            except BaseException:
                logger.error('Failed to get headers. Please wait to retry...')
                #logger.debug('Exception in getting headers:', exc_info=True)
                sleep(randint(750, 1000))
        logger.debug('Getting headers successful.')
        #logger.debug('Cookies: %s', cookies)
        return {'Cookie': cookies, 'User-Agent': agent}

    def getPage(self, headers):
        url = 'https://www.amazon.cn/s/ref=sr_pg_1?rh=n:658390051,k:{0}'.format(
            self.quoteKeyword)
        html = self.openUrl(url, headers)
        result = html.find('script', text=re.compile('totalResultCount'))
        json_result = json.loads(result.text)
        record = json_result['totalResultCount']
        if record == 0:
            logger.info('图书中没有"%s"的搜索结果。Exiting...', self.keyword)
            raise Warning('No Results Found')
        page = ceil(record/16)
        if page > 75:
            page = 75
        logger.info('Keyword: %s, Total records: %s, Total pages: %s',
                    self.keyword, record, page)
        return page

    def openUrl(self, url, headers):
        for _ in range(3):
            try:
                logger.debug('Opening url %s', url)
                request = Request(url, headers=dict(self.headers, **headers))
                html = urlopen(request)
                break
            except:
                logger.error('Encounter error when opening %s', url)
                sleep(randint(30, 60))
        html = BeautifulSoup(decompress(html.read()), 'html.parser')
        return html

    def parse(self, content, headers, executor):
        s_result_item = content.find_all('div', class_='s-result-item')
        if s_result_item == []:
            raise ValueError('Empty content.')
        AdHolder = content.find_all('div', class_='AdHolder')
        content = set(s_result_item) - set(AdHolder)
        bookList = []
        result = []
        for i in content:
            bookList.append(i['data-asin'])
        while True:
            try:
                return_list = list(executor.map(
                    partial(self.parseBook, headers=headers), bookList))
                for record in return_list:
                    result += record
                break
            except KeyboardInterrupt:
                executor._threads.clear()
                thread._threads_queues.clear()
                raise KeyboardInterrupt
            except:
                executor._work_queue = SimpleQueue()
                executor._threads.clear()
                thread._threads_queues.clear()
                sleep(randint(300, 600))
                headers = self.getHeaders()
        return result, headers

    def parseBook(self, id, headers):
        result = []
        url = 'https://www.amazon.cn/dp/{0}'.format(id)
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
        except:
            logger.error(
                'Failed to get book info(id: %s). Please wait to retry...', id)
            raise RuntimeError('Can not get book info.')
        sleep(randint(3, 5))
        return result

    def run(self):
        beginTime = time()
        url = 'https://www.amazon.cn/s/ref=sr_pg_1?rh=n:658390051,k:{0}&page={1}&sort=date-desc-rank'
        for _ in range(5):
            try:
                headers = self.getHeaders()
                page = self.getPage(headers)
                sleep(randint(2, 5))
                break
            except KeyboardInterrupt:
                logger.info('Job cancelled. Exiting...')
                return
            except Warning:
                return
            except:
                logger.error(
                    'Failed to get page number. Please wait to retry...')
                sleep(randint(30, 60))
                page = None
        if not page:
            logger.critical('Failed to get page number. Exiting...')
            return
        i = 1
        result = []
        with ThreadPoolExecutor(4, 'AZT') as executor:
            while i <= page:
                for _ in range(5):
                    try:
                        html = self.openUrl(url.format(
                            self.quoteKeyword, i), headers)
                        record, headers = self.parse(html, headers, executor)
                        result += record
                        i += 1
                        error = 0
                        break
                    except KeyboardInterrupt:
                        logger.info('Job cancelled. Exiting...')
                        executor._threads.clear()
                        thread._threads_queues.clear()
                        error = 1
                        break
                    except:
                        logger.error(
                            'Failed to parse contents(Page: %s). Please wait to retry...', i)
                        sleep(randint(30, 60))
                        try:
                            headers = self.getHeaders()
                        except KeyboardInterrupt:
                            logger.info('Job cancelled. Exiting...')
                            executor._threads.clear()
                            thread._threads_queues.clear()
                            error = 1
                            break
                        except:
                            pass
                if error == 1:
                    break
        if error == 1:
            logger.error(
                'Job was interrupted, not all results were outputted.')
            self.filename = 'temp.csv'
        try:
            fullpath = saveCSV(self.filename, self.fieldnames,
                               result, self.storepath)
        except FileNotFoundError:
            logger.error(
                'Failed to write output file, no such directory: "%s". Use current directory instead.', self.storepath)
            fullpath = saveCSV(self.filename, self.fieldnames, result)
        except PermissionError:
            logger.error(
                'Failed to write output file(filename: %s), destination file may be locked. Use current directory and temporary filename instead.', self.filename)
            fullpath = saveCSV(
                'temp'+'{:04}'.format(randint(0, 9999))+'.csv', self.fieldnames, result)
        timeCost = '%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', fullpath)
