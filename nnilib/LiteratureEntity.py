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
from random import randint
sys.path.append('..')
from lib.output import saveCSV
from nnilib.NNI import NNI
from nnilib.NNI import logger

class LiteratureEntity(NNI):
    def __init__(self, LID):
        NNI.__init__(self)
        self.LID = LID
        self.data = {'lid':LID}
        self.opener = build_opener()
        self.opener.addheaders = [('Cookie', 'XSRF-TOKEN={0}'.format(self.csrf))]
        self.opener.addheaders.append(('User-Agent', self.agent))
        self.name, self.yearlist = self.getInfo()
        self.fieldnames = ['Literature Name', 'year', 'title', 'lid', 'entityId']
        self.filename = self.name + '-nav.csv'

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
                sleep(randint(30, 60))
        if not name:
            logger.critical('Failed to get literature information. Exiting...')
            sys.exit()
        return name, yearlist

    def run(self):
        beginTime=time()
        url = self.url + '/literature/literature/loadYearVolume?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        entity = []
        i = 0
        while True:
            data['year'] = self.yearlist[i]
            for attempts in range(5):
                try:
                    logger.debug('Fetching year %s', self.yearlist[i])
                    response = self.fetch(url, data)
                    for r in response:
                        r['Literature Name'] = self.name
                    entity += response
                    break
                except:
                    response = None
                    logger.error('Encounter error when opening year %s', self.yearlist[i])
                    sleep(randint(30, 60))
            if not response:
                logger.critical("Failed to get year %s's contents. Continuing...", self.yearlist[i])
            i += 1
            if i >= len(self.yearlist):
                break
            sleep(randint(5, 30))
        saveCSV(self.filename, self.fieldnames, entity)
        timeCost='%.2f' % (time() - beginTime)
        logger.info('Total time: %ss', timeCost)
        logger.info('Output filename: %s', self.filename)

if __name__ == '__main__':
    job = LiteratureEntity(sys.argv[1])
    job.run()
