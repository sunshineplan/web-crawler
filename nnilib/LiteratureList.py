#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from math import ceil
from time import sleep
from random import randint
sys.path.append('..')
from lib.output import saveCSV
from nnilib.NNI import NNI
from nnilib.NNI import logger

class LiteratureList(NNI):
    def __init__(self, category):
        NNI.__init__(self)
        self.menu = {'1': 'Modern Periodical(近代)', '2': 'Contemporary Periodical(现代)', '3': 'Chinese Newspaper', '4':'Foreign Newspaper'}
        self.category = self.menu[category]
        self.data = {'categoryId': category, 'showMyResource': 'false', 'showOCR': 'false'}
        self.RecordsPerPage = 1000
        self.fieldnames = ['Title', 'CallNo', 'Cycle', 'DateIssued', 'PublisherUrb', 'Publisher', 'ProductKey', 'Id']
        self.filename = 'LiteratureList-' + self.category + '.csv'

    def getPage(self):
        url = self.url + '/literature/query?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        data['pageCount'] = 1
        for attempts in range(3):
            try:
                response, _ = self.fetch(url, data)
                total = response['totalCount']
                page = ceil(total/self.RecordsPerPage)
                logger.info('Category: %s, Total records: %s, Records per page: %s, Total pages: %s', self.category, total, self.RecordsPerPage, page)
                break
            except:
                page = None
                logger.error('Failed to fetch page value.')
                sleep(randint(30, 60))
        if not page:
            logger.critical('Failed to get page value. Exiting...')
            sys.exit()
        return page

    def run(self):
        url = self.url + '/literature/query?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        data['pageCount'] = self.RecordsPerPage
        page = self.getPage()
        i = 1
        documents = []
        while True:
            data['currentPage'] = i
            for attempts in range(5):
                try:
                    logger.debug('Fetching page %s', i)
                    response, _ = self.fetch(url, data)
                    documents += response['documents']
                    break
                except:
                    response = None
                    logger.error('Encounter error when opening page %s', i)
                    sleep(randint(30, 60))
            if not response:
                logger.critical("Failed to get page %s's contents. Continuing...", i)
            i += 1
            if i > page:
                break
            sleep(randint(5, 30))
        saveCSV(self.filename, self.fieldnames, documents)
        logger.info('Total time: %ss', self.elapsedTime())
        logger.info('Output filename: %s', self.filename)

if __name__ == '__main__':
    job = LiteratureList(sys.argv[1])
    job.run()
