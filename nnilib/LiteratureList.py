#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from json import loads
from urllib.parse import urlencode
from urllib.request import build_opener
from math import ceil
from time import sleep
from time import time
sys.path.append('..')
from lib.output import saveCSV
from nnilib.NNI import NNI
from nnilib.NNI import logger

class LiteratureList(NNI):
    def __init__(self, category):
        NNI.__init__(self)
        self.category = category
        self.data = {'categoryId':category,'showMyResource':'false','showOCR':'false'}
        self.RecordsPerPage = 1000
        self.opener = build_opener()
        self.opener.addheaders = [('User-Agent', self.agent)]
        self.opener.addheaders.append(('Cookie', 'XSRF-TOKEN={0}'.format(self.csrf)))
        self.fieldnames = ['Title', 'CallNo', 'Cycle', 'DateIssued', 'PublisherUrb', 'Publisher', 'ProductKey', 'Id']
        self.filename = 'LiteratureList-' + self.category + '.csv'

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
        saveCSV(self.filename, self.fieldnames, documents)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', self.filename)

if __name__ == '__main__':
    job = LiteratureList(sys.argv[1])
    job.run()
