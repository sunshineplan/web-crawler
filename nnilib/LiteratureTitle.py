#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from urllib.request import Request
from urllib.request import urlopen
#from urllib.request import build_opener
from math import ceil
from time import sleep
from time import time
sys.path.append('..')
from lib.output import saveCSV
from nnilib.NNI import NNI
from nnilib.NNI import logger

class LiteratureTitle(NNI):
    def __init__(self, LID):
        NNI.__init__(self)
        self.LID = LID
        self.data = {'typeId':1,'start':1833,'end':2018,'literatureId':LID}
        self.RecordsPerPage = 10000
        self.headers = {'Content-Type': 'application/json'}
        self.headers['Cookie'] = 'XSRF-TOKEN={0}'.format(self.csrf)
        self.headers['User-Agent'] = self.agent
        #self.opener = build_opener()
        #self.opener.addheaders = [('Content-Type', 'application/json'), ('Cookie', 'XSRF-TOKEN={0}'.format(self.csrf))]
        #self.opener.addheaders.append(('User-Agent', self.agent))
        self.name, self.category, self.page = self.getInfo()
        if self.category == 2:
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'Title1', 'Author1', 'Author2', 'Author3', 'CopAuthor1', 'Year', 'Volumn', 'Issue', 'Page', 'CLC', 'ProductKey', 'Id', 'Pid']
        elif self.category == 3:
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'Title1', 'Title2', 'Author1', 'Author2', 'NewsOccured', 'NewsSource', 'Category', 'Column', 'Year', 'Month', 'Day', 'BC', 'ProductKey', 'Id', 'Pid', 'Piid']
        elif self.category == 4:
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'Title1', 'Title1Cn', 'Title2', 'Title2Cn', 'Author1', 'Author2', 'NewsOccured', 'NewsSource', 'Category', 'Column', 'NewsTime', 'Year', 'Month', 'Day', 'BC', 'ProductKey', 'Id', 'Pid', 'Piid']
        elif self.category == 6:
            self.fieldnames = ['LiteratureTitle', 'LiteratureCategory', 'Title1', 'Title1Cn', 'Author1', 'Author2', 'Author3', 'Year', 'Month', 'Page', 'CountryArea', 'FirmAddress', 'Version', 'ProductKey', 'Id', 'Pid', 'Piid']
        elif self.category == 7:
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'Title1', 'Author1', 'Author2', 'Author3', 'Year', 'Volumn', 'Issue', 'PageVo', 'Page', 'CLC', 'ProductKey', 'Id', 'Pid', 'Piid']
        else:
            logger.critical('Unknow category. Exiting...')
            sys.exit()
        self.filename = self.name + '-title.csv'

    def fetch(self, url, data):
        data = json.dumps(data).encode('utf8')
        request = Request(url, data, self.headers)
        response = urlopen(request)
        #response = self.opener.open(url, data)
        jsonresponse = json.loads(response.read().decode('utf8'))
        return jsonresponse

    def getInfo(self):
        url = self.url + '/search/adQuery?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        data['pageCount'] = 1
        for attempts in range(3):
            try:
                response = self.fetch(url, data)
                name = response[0]['documents'][0]['LiteratureTitle']
                category = response[0]['documents'][0]['LiteratureCategory']
                total = response[0]['totalCount']
                page = ceil(total/self.RecordsPerPage)
                logger.info('Literature Name: %s, Category: %s, Total records: %s, Records per page: %s, Total pages: %s', name, category, total, self.RecordsPerPage, page)
                break
            except:
                name = None
                logger.error('Failed to fetch literature information.')
                sleep(60)
        if not name:
            logger.critical('Failed to get literature information. Exiting...')
            sys.exit()
        return name, category, page

    def run(self):
        beginTime=time()
        url = self.url + '/search/adQuery?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        data['pageCount'] = self.RecordsPerPage
        i = 1
        documents = []
        while True:
            data['currentPage'] = i
            for attempts in range(5):
                try:
                    logger.debug('Fetching page %s', i)
                    response = self.fetch(url, data)
                    documents += response[0]['documents']
                    break
                except:
                    response = None
                    logger.debug('Encounter error when opening page %s', i)
                    sleep(60)
            if not response:
                logger.critical("Failed to get page %s's contents. Continuing...", i)
            i += 1
            if i > self.page:
                break
            sleep(60)
        saveCSV(self.filename, self.fieldnames, documents)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', self.filename)

if __name__ == '__main__':
    job = LiteratureTitle(sys.argv[1])
    job.run()
