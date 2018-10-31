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
from time import strftime
from lib.output import saveCSV

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

class LiteratureTitle():
    def __init__(self, LID):
        self.LID = LID
        self.data = {'typeId':1,'start':1833,'end':2018,'literatureId':LID}
        self.url = 'NNI'
        self.agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.9 Safari/537.36'
        self.csrf = self.getCSRF()
        self.RecordsPerPage = 10000
        self.headers = {'Content-Type': 'application/json'}
        self.headers['Cookie'] = 'XSRF-TOKEN={0}'.format(self.csrf)
        self.headers['User-Agent'] = self.agent
        #self.opener = build_opener()
        #self.opener.addheaders = [('Content-Type', 'application/json'), ('Cookie', 'XSRF-TOKEN={0}'.format(self.csrf))]
        #self.opener.addheaders.append(('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.9 Safari/537.36'))
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
        page = self.page
        i = 1
        documents = []
        while i <= page:
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
            sleep(60)
        saveCSV(self.filename, self.fieldnames, documents)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', self.filename)

if __name__ == '__main__':
    job = LiteratureTitle(sys.argv[1])
    job.run()
