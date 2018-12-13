#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
from csv import DictWriter
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import HTTPErrorProcessor
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import urlretrieve
from urllib.request import build_opener
from urllib.request import install_opener
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import thread
from functools import partial
from math import ceil
from time import sleep
from time import time
from random import *
from lib.comm import getAgent

import logging
logger = logging.getLogger('NB')
dl_logger = logging.getLogger('NB_dl')
logger.setLevel(logging.DEBUG)
dl_logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('NB_crawler.log')
dl_fh = logging.FileHandler('NB_downloader.log')
#fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] (%(threadName)s) - %(message)s')
fh.setFormatter(formatter)
dl_fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
dl_logger.addHandler(dl_fh)
logger.addHandler(ch)

class NB():
    def __init__(self):
        self.beginTime = time()
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
        class NoRedirection(HTTPErrorProcessor):
            def http_response(self, request, response):
                return response
        self.opener = build_opener()
        self.noredirect_opener = build_opener(NoRedirection)
        self.opener.addheaders = self.noredirect_opener.addheaders = [('User-Agent', self.agent), ('Cookie', self.cookie)]
        try:
            self.newspaper = self.getNewspaper()
            shuffle(self.newspaper)
        except:
            logger.critical('Failed to fetch newspaper list. Exiting...')
            sys.exit()
        self.fieldnames = ['Title', 'Author', 'Newspaper', 'Date', 'Page', 'Link']
        self.DownloadExecutor = ThreadPoolExecutor(1, 'DT')
        self.last_download = ''
        self.counter = 0

    def getCookie(self):
        request = Request(self.url, method='HEAD', headers={'User-Agent': self.agent})
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
            year = i.text[0:4]
            if int(year) <= 1960:
                result.append(year)
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
            return [1]
        page = ceil((int(record)/20))
        return range(1,int(page)+1)

    def openUrl(self, url):
        for attempts in range(5):
            try:
                logger.debug('Opening %s', url.replace(self.url, ''))
                html = urlopen(url).read().decode(encoding='gbk')
                break
            except:
                logger.error('Encounter error when opening %s. Waiting for retry...', url.replace(self.url, ''))
                html = None
                sleep(randint(30, 60)+random())
        if not html:
            logger.error('Failed to open %s.', url.replace(self.url, ''))
            return None
        soupContent = BeautifulSoup(html, 'html.parser')
        return soupContent

    def parse(self, page, newspaper, year):
        if page == 2:
            sleep(0.5)
        elif page == 3:
            sleep(1)
        url = self.url + 'search.jsp?menuName={0}&year={1}&d-3995381-p={2}'.format(quote(newspaper, encoding='gbk'), year, page)
        html = self.openUrl(url)
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
                self.DownloadExecutor.submit(self.DownloadPDF, record)
            except:
                logger.error('A corrupted record was skipped.(Please check %s)', url.replace(self.url, ''))
        sleep(0.5)
        return result

    def DownloadPDF(self, record):
        if self.last_download == '':
            dl_logger.info('Start download.')
        link = record['Link']
        id = link.split('?')[-1]
        newspaper = record['Newspaper']
        date = record['Date']
        page = record['Page']
        path = newspaper + '/' + date.split('-')[0] + '/' + ''.join(date.split('-')[1:])
        if page == '未知':
            request = Request(link, method='HEAD')
            headers = self.noredirect_opener.open(request)
            filename = headers.info().get('Location').split(';')[0].split('/')[-1].split('.')[0].lstrip('0').zfill(2) + '.pdf'
            sleep(random())
        else:
            filename = page.replace('、', '_').replace('?', '等') + '.pdf'
        fullpath = path + '/' + filename
        if fullpath == self.last_download:
            return
        if os.path.isfile(fullpath):
            dl_logger.debug('skip %s(%s)', fullpath, id)
            self.last_download = fullpath
        else:
            for attempts in range(3):
                try:
                    dl_logger.info('downloading %s(%s)', fullpath, id)
                    #urlretrieve(link, fullpath)
                    file = urlopen(link, timeout=60)
                    if not file.info().get('Etag'):
                        dl_logger.info('The file could not be found - %s', fullpath)
                        error = 0
                        break
                    if not os.path.isdir(path):
                        os.makedirs(path)
                    with open(fullpath, 'wb') as download_file:
                        download_file.write(file.read())
                    self.counter += 1
                    error = 0
                    break
                except:
                    dl_logger.error('Encounter error when downloading %s. Waiting for retry...', fullpath)
                    sleep(randint(30, 60)+random())
                    error = 1
            if error == 1:
                dl_logger.error('%s download failed.(%s)', fullpath, link)
                return
            self.last_download = fullpath

    def elapsedTime(self):
        return '%.2f' % (time() - self.beginTime)

    def run(self):
        install_opener(self.opener)
        logger.info('Newspaper List: %s', ','.join(self.newspaper))
        with open('NB.csv', 'w', encoding='utf-8-sig', newline='') as output_file:
            output = DictWriter(output_file, self.fieldnames, extrasaction='ignore')
            output.writeheader()
            for n in self.newspaper:
                try:
                    year = self.getYear(n)
                    logger.info('%s Year: %s', n, ','.join(year))
                except:
                    logger.error('Failed to fetch %s year value.', n)
                    continue
                for y in year:
                    try:
                        page = self.getPage(n, y)
                        logger.info('%s %s Page: %s', n, y, page[-1])
                    except:
                        logger.error('Failed to fetch %s %s page value.', n, y)
                        continue
                    with ThreadPoolExecutor(3, 'CT') as executor:
                        try:
                            return_list = list(executor.map(partial(self.parse, newspaper=n, year=y), page))
                        except KeyboardInterrupt:
                            logger.info('Job cancelled. Exiting...')
                            dl_logger.info('Job cancelled. Exiting...')
                            executor._threads.clear()
                            self.DownloadExecutor._threads.clear()
                            thread._threads_queues.clear()
                            self.DownloadExecutor.shutdown()
                            return
                        for record in return_list:
                            output.writerows(record)
                    logger.info('Current downloading process: %s', self.last_download)
                    logger.info('Current downloaded pdf files: %s', self.counter)
                    logger.info('Elapsed Time: %ss', self.elapsedTime())
            logger.info('Newspaper info crawling finished. Total time: %ss', self.elapsedTime())
            logger.info('Please wait for the pdf download process to complete...')
        self.DownloadExecutor.shutdown()
        dl_logger.info('Download complete. Total time: %ss', self.elapsedTime())
        logger.info('All done. Total time: %ss', self.elapsedTime())
        dl_logger.info('Total downloaded files: %s', self.counter)
        logger.info('Total downloaded files: %s', self.counter)


if __name__ == "__main__":
    job = NB()
    job.run()
