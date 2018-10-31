#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from bs4 import BeautifulSoup
from json import loads
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import build_opener
from time import sleep
from time import time
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

class LiteratureEntity():
    def __init__(self, LID):
        self.LID = LID
        self.data = {'lid':LID}
        self.url = 'NNI'
        self.agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.9 Safari/537.36'
        self.csrf = self.getCSRF()
        self.opener = build_opener()
        self.opener.addheaders = [('Cookie', 'XSRF-TOKEN={0}'.format(self.csrf))]
        self.opener.addheaders.append(('User-Agent', self.agent))
        self.name, self.yearlist = self.getInfo()
        self.fieldnames = ['Literature Name', 'year', 'title', 'lid', 'entityId']
        self.filename = self.name + '-nav.csv'

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

    def getInfo(self):
        request = Request(self.url + '/literature/literature/' + self.LID, headers={'User-Agent': self.agent})
        for attempts in range(3):
            try:
                html = urlopen(request)
                soupContent = BeautifulSoup(html, 'html.parser')
                name = soupContent.find('div', class_='description_title').text
                year = soupContent.find_all('span', class_='cls_year')
                yearlist = []
                for i in year:
                    yearlist.append(i.text)
                logger.info('Literature Name: %s, Years: %s', name, ','.join(yearlist))
                break
            except:
                name = None
                logger.error('Failed to fetch literature information.')
                sleep(60)
        if not name:
            logger.critical('Failed to get literature information. Exiting...')
            sys.exit()
        return name, yearlist

    def run(self):
        beginTime=time()
        url = self.url + '/literature/literature/loadYearVolume?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        entity = []
        for i in self.yearlist:
            data['year'] = i
            for attempts in range(5):
                try:
                    logger.debug('Fetching year %s', i)
                    response = self.fetch(url, data)
                    for i in response:
                        i['Literature Name'] = self.name
                    entity += response
                    break
                except:
                    response = None
                    logger.error('Encounter error when opening year %s', i)
                    sleep(60)
            if not response:
                logger.critical("Failed to get year %s's contents. Continuing...", i)
            sleep(60)
        saveCSV(self.filename, self.fieldnames, entity)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', self.filename)

if __name__ == '__main__':
    job = LiteratureEntity(sys.argv[1])
    job.run()
