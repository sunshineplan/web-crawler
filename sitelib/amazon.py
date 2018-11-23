#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import Request
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import thread
from functools import partial
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
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s(%(threadName)s) - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

class Amazon():
    def __init__(self, keyword, path=''):
        self.keyword = keyword
        self.quoteKeyword = quote(keyword)
        self.agent = self.getAgents()
        self.accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        self.acceptEncoding = 'gzip, deflate, br'
        self.acceptLanguage = 'en-US,en;q=0.9'
        self.headers = {'Accept': self.accept, 'Accept-Encoding': self.acceptEncoding, 'Accept-Language': self.acceptLanguage}
        self.fieldnames = ['Name', 'Author', 'Price', 'URL']
        self.storepath = path
        self.filename = 'AZ' + strftime('%Y%m%d') + '-' + self.keyword + '.csv'

    def getAgents(self):
        try:
            url = 'https://techblog.willshouse.com/2012/01/03/most-common-user-agents/'
            request = Request(url, headers = {'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)'})
            html = BeautifulSoup(urlopen(request), 'html.parser')
            agent = html.find('textarea', class_='get-the-list')
            agent = agent.text.splitlines()[:10]
            logger.debug('Download user agents list successful.')
        except:
            agent = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
                'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
                'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36 OPR/56.0.3051.99',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36 Maxthon/5.2.5.3000',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6788.400 QQBrowser/10.3.2714.400',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4094.1 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36 LBBROWSER'
                ]
            logger.debug('Download user agents list failed. Use custom list instead.')
        return agent

    def getHeaders(self):
        for attempts in range(10):
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
                url = 'https://www.amazon.cn/gp/prime/digital-adoption/navigation-bar/{0}?type=load&isPrime=false'.format(sessionId)
                step = 2
                for repeats in range(2):
                    sleep(randint(2, 5))
                    request = Request(url, headers=dict(headers, **{'Cookie': ';'.join(cookies)}))
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
            except:
                logger.error('Failed to get headers. Please wait to retry...')
                sleep(randint(500, 600))
        #logger.debug('Cookies: %s', cookies)
        return {'Cookie':cookies, 'User-Agent': agent}

    def getPage(self, headers):
        url = 'https://www.amazon.cn/s/ref=sr_pg_1?rh=n:658390051,k:{0}'.format(self.quoteKeyword)
        html = self.openUrl(url, headers)
        if html.find('h1', id='noResultsTitle') is not None:
            logger.info('我们找到了与 "%s" 相关的 0 条 结果。Exiting...', self.keyword)
            raise Warning('No Results Found')
        result = html.find('span', id='s-result-count').text
        _, record = result.split('共')
        record = ''.join(i for i in record if i.isdigit())
        page = ceil((int(record)/16))
        if page > 75:
            page = 75
        logger.info('Keyword: %s, Total records: %s, Total pages: %s', self.keyword, record, page)
        return page

    def openUrl(self, url, headers):
        for attempts in range(3):
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
        content = content.find_all('li', id=re.compile('result_'))
        if content == []:
            raise ValueError('Empty content.')
        bookList = []
        result = []
        for i in content:
            bookList.append(i['data-asin'])
        while True:
            try:
                return_list = list(executor.map(partial(self.parseBook, headers=headers), bookList))
                for record in return_list:
                    result += record
                break
            except KeyboardInterrupt:
                executor._threads.clear()
                thread._threads_queues.clear()
                raise KeyboardInterrupt
            except:
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
            logger.error('Failed to get book info(id: %s). Please wait to retry...', id)
            raise RuntimeError('Can not get book info.')
        sleep(randint(3, 5))
        return result

    def run(self):
        beginTime=time()
        url = 'https://www.amazon.cn/s/ref=sr_pg_1?rh=n:658390051,k:{0}&page={1}&sort=date-desc-rank'
        for attempts in range(5):
            try:
                headers = self.getHeaders()
                page = self.getPage(headers)
                break
            except KeyboardInterrupt:
                logger.info('Job cancelled. Exiting...')
                return
            except Warning:
                return
            except:
                logger.error('Failed to get page number. Please wait to retry...')
                sleep(randint(30, 60))
                page = None
        if not page:
            logger.critical('Failed to get page number. Exiting...')
            return
        i = 1
        result = []
        with ThreadPoolExecutor(4, 'AZT') as executor:
            while i <= page:
                for attempts in range(5):
                    try:
                        html = self.openUrl(url.format(self.quoteKeyword, i), headers)
                        record, headers = self.parse(html, headers, executor)
                        result += record
                        i += 1
                        error = 0
                        break
                    except KeyboardInterrupt:
                        logger.info('Job cancelled. Exiting...')
                        executor._threads.clear()
                        thread._threads_queues.clear()
                        return                            
                    except:
                        logger.error('Failed to parse contents(Page: %s). Please wait to retry...', i)
                        sleep(randint(30, 60))
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
        job = Amazon(sys.argv[1], sys.argv[2])
        job.run()
    elif len(sys.argv) == 2:
        job = Amazon(sys.argv[1])
        job.run()
    else:
        logger.critical('Wrong number of arguments.')
