#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from bs4 import BeautifulSoup
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from datetime import date
from random import randint
sys.path.append('..')
from lib.output import saveCSV
from nnilib.NNI import NNI
from nnilib.NNI import logger

class LiteratureEntity(NNI):
    def __init__(self, LID, download=False):
        NNI.__init__(self)
        self.LID = LID
        self.data = {'lid': LID}
        self.name, self.category = self.getCategory()
        if self.category == 2:#Contemporary Periodical 现代期刊
            logger.info('Contemporary Periodical(现代期刊) has no entity infomation.')
            sys.exit()
        self.yearlist = self.getYearlist()
        self.fieldnames = ['Literature Name', 'year', 'title', 'lid', 'entityId']
        self.filename = self.name + '-nav.csv'
        self.DownloadExecutor = ThreadPoolExecutor(1, 'DT')
        self.download = download
        self.counter = 0

    def getCategory(self):
        url = self.url + '/search/adQuery?_csrf={0}'.format(self.csrf)
        data = {'typeId': 1, 'start': 1833, 'end': date.today().year, 'literatureId': self.LID, 'pageCount': 1}
        for attempts in range(3):
            try:
                response, _ = self.fetch(url, data, data_type='json')
                name = response[0]['documents'][0]['LiteratureTitle']
                category = response[0]['documents'][0]['LiteratureCategory']
                logger.info('Name: %s, Category: %s', name, category)
                break
            except:
                category = None
                logger.error('Failed to fetch literature category.')
                sleep(randint(30, 60))
        if not category:
            logger.critical('Failed to get literature category. Exiting...')
            sys.exit()
        return name, category

    def getYearlist(self):
        url = self.url + '/literature/literature/' + self.LID
        for attempts in range(3):
            try:
                html = urlopen(url)
                soupContent = BeautifulSoup(html, 'html.parser')
                year = soupContent.find_all('span', class_='cls_year')
                yearlist = []
                for i in year:
                    yearlist.append(i.text)
                logger.info('Years: %s', ','.join(yearlist))
                break
            except:
                yearlist = None
                logger.error('Failed to fetch literature information.')
                sleep(randint(30, 60))
        if not yearlist:
            logger.critical('Failed to get literature information. Exiting...')
            sys.exit()
        return yearlist

    def getTitle(self, eid):
        url = self.url + '/search/adQuery?_csrf={0}'.format(self.csrf)
        data = {'typeId': 1, 'start': 1833, 'end': date.today().year, 'entityId': eid, 'pageCount': 1}
        try:
            response, _ = self.fetch(url, data, data_type='json')
            month = response[0]['documents'][0]['Month']
            if self.category != 6:#Hong List 07a8b7c27e6188424f460e0839f677ae
                day = response[0]['documents'][0]['Day']
        except:
            logger.debug('Unknow title, eid: %s', eid)
            return 'unknow'
        if self.category == 6:
            return str(month).zfill(2)
        return '{0}{1}'.format(str(month).zfill(2), str(day).zfill(2))

    def getFilenames(self, record):
        eid = record['entityId']
        if self.category == 7:#Never run
            step1 = self.url + '/literature/browseEntity/{0}'.format(eid)
            _, info = self.fetch(step1)
            if info.get('Content-Length') == '0':
                logger.error('You have no download permission.')
                self.download = False
                return None
            step2 = self.url + '/literature/periodicalEntity/{0}'.format(eid)
            respone, _ = self.fetch(step2)
            filenames = respone['Files']
        else:#This action will be recorded as one browse count
            url = self.url + '/literature/newspaperEntity/{0}/0/0/True/True?bcindex=1'.format(eid)
            respone, info = self.fetch(url)
            if info.get('Content-Length') == '0':
                logger.error('You have no download permission.')
                self.download = False
                return None
            bcs = respone['bcs']
            filenames = []
            for i in bcs:
                filenames.append(i['Id'])
        return filenames

    def Download(self, record):
        if self.download == False:
            return
        literature = record['Literature Name']
        eid = record['entityId']
        year = record['year']
        title = record['title']
        path = literature + '/' + year + '/' + title
        if self.category == 7:
            i = 0
            flag = 0
            while True:
                filename = str(i).zfill(4) + '.jpg'
                url = self.url + '/literature/periodImage/{0}/0/0/{1}'.format(eid, filename)
                fullpath = path + '/' + filename
                file = urlopen(url, timeout=60)
                if not file.info().get('Content-Disposition'):
                    if i == 0:
                        flag = 1
                        i += 1
                        continue
                    elif i == 1 and flag == 1:
                        logger.error('Entity:%s download failed, please check the resource.', path)
                    return
                if not os.path.isdir(path):
                    os.makedirs(path)
                with open(fullpath, 'wb') as download_file:
                    download_file.write(file.read())
                i += 1
                self.counter += 1
        else:
            filenames = self.getFilenames(record)
            if not filenames:
                return
            page = 1
            for filename in filenames:
                url = self.url + '/literature/newsThumbImage/{0}/0/0/{1}'.format(eid, filename)
                fullpath = path + '/' + str(page).zfill(4) + '.jpg'
                for attempts in range(3):
                    try:
                        file = urlopen(url, timeout=60)
                        if not os.path.isdir(path):
                            os.makedirs(path)
                        with open(fullpath, 'wb') as download_file:
                            download_file.write(file.read())
                        self.counter += 1
                        page += 1
                        error = 0
                        break
                    except:
                        sleep(randint(30, 60))
                        error = 1
                if error == 1:
                    logger.error('%s download failed.', fullpath)
            sleep(randint(50, 60))

    def run(self):
        url = self.url + '/literature/literature/loadYearVolume?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        entity = []
        i = 0
        while True:
            data['year'] = self.yearlist[i]
            for attempts in range(5):
                try:
                    logger.debug('Fetching year %s', self.yearlist[i])
                    response, _ = self.fetch(url, data)
                    for r in response:
                        r['Literature Name'] = self.name
                        if self.category != 7:
                            r['title'] = self.getTitle(r['entityId'])
                    entity += response
                    if self.download == True:
                        self.DownloadExecutor.map(self.Download, response)
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
        logger.info('Entity info crawling finished. Total time: %ss', self.elapsedTime())
        logger.info('Output filename: %s', self.filename)
        if self.download == True:
            logger.info('Please wait for the download process to complete...')
            self.DownloadExecutor.shutdown()
            if self.download == True:
                logger.info('All done, total time: %ss', self.elapsedTime())
                logger.info('Total downloaded files: %s', self.counter)

if __name__ == '__main__':
    job = LiteratureEntity(sys.argv[1])
    job.run()
