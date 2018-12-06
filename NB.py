#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from csv import DictWriter
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import build_opener
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import thread
from functools import partial
from math import ceil
from time import sleep
from time import time
from random import *
from lib.comm import getAgent

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('NB.log')
#fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

class NB():
    def __init__(self):
        self.url = 'NB/'
        self.agent, error = getAgent(1)
        if error == 0:
            logger.debug('Getting user agent successful.')
        else:
            logger.error('Getting user agent failed. Use custom agent instead.')
        try:
            self.cookie = self.getCookie()
        except:
            logger.critical('Failed to get Cookie. Exiting...')
            sys.exit()
        self.opener = build_opener()
        self.opener.addheaders = [('User-Agent', self.agent)]
        self.opener.addheaders.append(('Cookie', self.cookie))
        try:
            self.newspaper = self.getNewspaper()
            shuffle(self.newspaper)
        except:
            logger.critical('Failed to fetch newspaper list. Exiting...')
            sys.exit()
        self.fieldnames = ['Title', 'Author', 'Newspaper', 'Date', 'Page', 'Link']

    def getCookie(self):
        request = Request(self.url, method='HEAD', headers = {'User-Agent': self.agent})
        for attempts in range(3):
            try:
                headers = urlopen(request)
                break
            except:
                headers = None
                logger.error('Failed to fetch headers.')
                sleep(randint(30, 60))
        if not headers:
            raise ValueError('No cookie.')
        cookie = headers.info().get('Set-Cookie')
        return cookie[:cookie.find(';')]

    def getNewspaper(self):
        html = self.openUrl(self.url + 'searchresultinfo.jsp')
        if not html:
            raise ValueError('No newspaper list.')
        content = html.find('select', attrs={'name':'range'})
        list = content.find_all('option')
        result = []
        for i in list:
            result.append(i.text)
        result.remove('所有报纸')
        return result

    def getYear(self, newspaper):
        html = self.openUrl(self.url + 'menu.jsp')
        if not html:
            raise ValueError('No year value.')
        content = html.find_all('a', href=re.compile('=' + newspaper + '&'))
        result = []
        for i in content:
            year = i.text
            result.append(year[0:4])
        logger.info('%s Year: %s', newspaper, ','.join(result))
        return result

    def getPage(self, newspaper, year):
        url = self.url + 'search.jsp?menuName={0}&year={1}'
        html = self.openUrl(url.format(quote(newspaper, encoding='gbk'), year))
        if not html:
            raise ValueError('No page value.')
        content = html.find('span', class_='pagebanner')
        try:
            record = content.b.text.replace(',', '')
        except AttributeError:
            page = 1
        page = ceil((int(record)/20))
        logger.info('%s %s Page: %s', newspaper, year, page)
        return range(1,int(page)+1)

    def openUrl(self, url):
        for attempts in range(5):
            try:
                logger.debug('Opening %s', url.replace(self.url, ''))
                html = self.opener.open(url).read()
                break
            except:
                html = None
                logger.error('Encounter error when opening %s. Waiting for retry...', url.replace(self.url, ''))
        if not html:
            logger.error('Failed to open %s.', url.replace(self.url, ''))
            return None
        soupContent = BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        return soupContent

    def parse(self, page, newspaper, year):
        sleep(randint(1, 2)+random())
        url = self.url + 'search.jsp?menuName={0}&year={1}&d-3995381-p={2}'
        html = self.openUrl(url.format(quote(newspaper, encoding='gbk'), year, page))
        if not html:
            logger.error('Failed to fetch %s %s %s content.', newspaper, year, page)
            return []
        content = html.find_all('tr', class_=re.compile('odd|even'))
        result = []
        for i in content:
            row = i.find_all('td')
            link = self.url + i.find('a')['href']
            record = {}
            try:
                record['Title'] = row[0].text.strip()
                record['Author'] = row[1].text.strip()
                record['Newspaper'] = row[2].text.strip()
                record['Date'] = row[3].text.strip()
                record['Page'] = row[4].text.strip()
                record['Link'] = link
                result.append(record)
            except:
                logger.error('A corrupted record was skipped.(Please check %s)', url.replace(self.url, ''))
        return result

    def run(self):
        beginTime=time()
        logger.info('Newspaper List: %s', ','.join(self.newspaper))
        with open('NB.csv', 'w', encoding='utf-8-sig', newline='') as output_file:
            output = DictWriter(output_file, self.fieldnames, extrasaction='ignore')
            output.writeheader()
            for n in self.newspaper:
                try:
                    year = self.getYear(n)
                except:
                    logger.error('Failed to fetch %s year value.', n)
                    continue
                for y in year:
                    try:
                        page = self.getPage(n, y)
                    except:
                        logger.error('Failed to fetch %s %s page value.', n, y)
                        continue
                    with ThreadPoolExecutor(3) as executor:
                        try:
                            return_list = list(executor.map(partial(self.parse, newspaper=n, year=y), page))
                        except KeyboardInterrupt:
                            logger.info('Job cancelled. Exiting...')
                            executor._threads.clear()
                            thread._threads_queues.clear()
                            return
                        for record in return_list:
                            output.writerows(record)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)


if __name__ == "__main__":
    job = NB()
    job.run()
