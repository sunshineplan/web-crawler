#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from json import loads
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import build_opener
from math import ceil
from time import sleep
from time import time
from csv import DictWriter

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('NNI.log')
#fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

class LiteratureList():
    def __init__(self, category):
        self.category = category
        self.data = {'categoryId':category,'showMyResource':'false','showOCR':'false'}
        self.url = 'NNI'
        self.agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.9 Safari/537.36'
        self.csrf = self.getCSRF()
        self.RecordsPerPage = 1000
        self.opener = build_opener()
        self.opener.addheaders = [('User-Agent', self.agent)]
        self.opener.addheaders.append(('Cookie', 'XSRF-TOKEN={0}'.format(self.csrf)))
        self.fieldnames = ['Title', 'CallNo', 'Cycle', 'DateIssued', 'PublisherUrb', 'Publisher', 'ProductKey', 'Id']
        self.filename = 'LiteratureList-' + self.category + '.csv'

    def getCSRF(self):
        request = Request(self.url, method='HEAD', headers={'User-Agent': self.agent})
        for attempts in range(3):
            try:
                headers = urlopen(request)
                cookie = headers.info().get('Set-Cookie')
                csrf = cookie[cookie.find('=')+1:cookie.find(';')]
                break
            except:
                csrf = None
                logger.error('Failed to fetch headers.')
                sleep(60)
        if not csrf:
            logger.critical('Failed to get CSRF. Exiting...')
            sys.exit()
        return csrf

    def fetch(self, url, data):
        data = urlencode(data).encode('utf8')
        response = self.opener.open(url, data)
        jsonresponse = loads(response.read().decode('utf8'))
        return jsonresponse

    def getPage(self):
        url = self.url + '/literature/query?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        data['pageCount'] = 1
        for attempts in range(3):
            try:
                response = self.fetch(url, data)
                total = response['totalCount']
                page = ceil(total/self.RecordsPerPage)
                logger.info('Category: %s, Total records: %s, Records per page: %s, Total pages: %s', self.category, total, self.RecordsPerPage, page)
                break
            except:
                page = None
                logger.error('Failed to fetch page value.')
                sleep(60)
        if not page:
            logger.critical('Failed to get page value. Exiting...')
            sys.exit()
        return page

    def run(self):
        beginTime=time()
        url = self.url + '/literature/query?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        data['pageCount'] = self.RecordsPerPage
        page = self.getPage()
        i = 1
        documents = []
        while i <= page:
            data['currentPage'] = i
            for attempts in range(5):
                try:
                    logger.debug('Fetching page %s', i)
                    response = self.fetch(url, data)
                    documents += response['documents']
                    break
                except:
                    response = None
                    logger.error('Encounter error when opening page %s', i)
                    sleep(60)
            if not response:
                logger.critical("Failed to get page %s's contents. Continuing...", i)
            i += 1
            sleep(60)
        with open(self.filename, 'w', encoding='utf8', newline='') as output_file:
            output = DictWriter(output_file, self.fieldnames, extrasaction='ignore')
            output.writeheader()
            output.writerows(documents)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', self.filename)

if __name__ == '__main__':
    job = LiteratureList(sys.argv[1])
    job.run()
