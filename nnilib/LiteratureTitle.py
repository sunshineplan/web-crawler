#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from base64 import b64encode
from hashlib import sha1
from io import BytesIO
from zipfile import ZipFile
from math import ceil
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.request import build_opener
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from datetime import date
from random import randint
sys.path.append('..')
from lib.output import saveCSV
from nnilib.NNI import NNI
from nnilib.NNI import logger

class LiteratureTitle(NNI):
    def __init__(self, LID, download=False):
        NNI.__init__(self)
        self.LID = LID
        self.data = {'typeId': 1, 'start': 1833, 'end': date.today().year, 'literatureId': LID}
        self.RecordsPerPage = 1000
        self.name, self.category, self.page = self.getInfo()
        if self.category == 2:#Contemporary Periodical 现代期刊
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'Title1', 'Author1', 'Author2', 'Author3', 'CopAuthor1', 'Year', 'Volumn', 'Issue', 'Page', 'CLC', 'ProductKey', 'Id', 'Pid']
        elif self.category == 3:#Chinese Newspaper
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'LiteratureCategoryPieceTypeId', 'Title1', 'Title2', 'Author1', 'Author2', 'NewsOccured', 'NewsSource', 'Category', 'Column', 'Year', 'Month', 'Day', 'BC', 'ProductKey', 'Id', 'Pid', 'Piid']
        elif self.category == 4:#Foreign Newspaper
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'LiteratureCategoryPieceTypeId', 'Title1', 'Title1Cn', 'Title2', 'Title2Cn', 'Author1', 'Author2', 'NewsOccured', 'NewsSource', 'Category', 'Column', 'NewsTime', 'Year', 'Month', 'Day', 'BC', 'ProductKey', 'Id', 'Pid', 'Piid']
        elif self.category == 6:#Hong List 07a8b7c27e6188424f460e0839f677ae
            self.fieldnames = ['LiteratureTitle', 'LiteratureCategory', 'LiteratureCategoryPieceTypeId', 'Title1', 'Title1Cn', 'Author1', 'Author2', 'Author3', 'Year', 'Month', 'Page', 'CountryArea', 'FirmAddress', 'Version', 'ProductKey', 'Id', 'Pid', 'Piid']
        elif self.category == 7:#Modern Periodical 近代期刊
            self.fieldnames = ['LiteratureTitle', 'CallNo', 'LiteratureCategory', 'Title1', 'Author1', 'Author2', 'Author3', 'Year', 'Volumn', 'Issue', 'PageVo', 'Page', 'CLC', 'ProductKey', 'Id', 'Pid', 'Piid']
        else:
            logger.critical('Unknow category. Exiting...')
            sys.exit()
        self.filename = self.name + '-title.csv'
        self.DownloadExecutor = ThreadPoolExecutor(1, 'DT')
        self.download = download
        self.download_mode = ''
        self.api = 'NNI'
        self.counter = 0

    def getInfo(self):
        url = self.url + '/search/adQuery?_csrf={0}'.format(self.csrf)
        data = self.data.copy()
        data['pageCount'] = 1
        for attempts in range(3):
            try:
                response, _ = self.fetch(url, data, data_type='json')
                name = response[0]['documents'][0]['LiteratureTitle']
                category = response[0]['documents'][0]['LiteratureCategory']
                total = response[0]['totalCount']
                page = ceil(total/self.RecordsPerPage)
                logger.info('Literature Name: %s, Category: %s, Total records: %s, Records per page: %s, Total pages: %s', name, category, total, self.RecordsPerPage, page)
                break
            except:
                name = None
                logger.error('Failed to fetch literature information.')
                sleep(randint(30, 60))
        if not name:
            logger.critical('Failed to get literature information. Exiting...')
            sys.exit()
        return name, category, page

    def Download(self, record):
        if self.download == False:
            return
        id = record['Id']
        title = record['Title1']
        literature = record['LiteratureTitle']
        category = record['LiteratureCategory']
        year = record['Year']
        filename = title.replace(':', '_').replace('?', '_').replace('"', '_') + '.pdf'
        if category == 3 or category == 4 or category == 6:#This action will be recorded as one download count(browse mode)
            month = record.get('Month')
            path = '{0}/{1}/{2}'.format(literature, year, str(month).zfill(2))
            if category != 6:
                day = record.get('Day')
                path = '{0}/{1}/{2}{3}'.format(literature, year, str(month).zfill(2), str(day).zfill(2))
            url = self.url + '/literature/downloadPiece?pieceId={0}&ltid={1}'.format(id, record['LiteratureCategoryPieceTypeId'])
        elif category == 7:#This action will be recorded as one download count(preview mode)
            issue = record.get('PageVo')
            path = '{0}/{1}/{2}'.format(literature, year, issue)
            url = self.url + '/literature/browsePieceX?pieceId={0}&ltid={1}'.format(id, category)
        else:
            logger.info('This Literature has no download resources.')
            self.download = False
            return
        super_url = self.api + '/common/downloadResource'
        super_key = b64encode(sha1((str(date.today()) + 'NNI').encode()).digest()).decode()
        super_data = urlencode({'key': super_key, 'data': {'index': 0, 'type': 1, 'dataIds': [id]}}).encode()
        super_opener = build_opener()
        super_opener.addheaders = [('User-Agent', self.agent)]
        fullpath = path + '/' + filename
        for attempts in range(3):
            try:
                if self.download_mode != 'normal':
                    try:
                        zip = super_opener.open(super_url, super_data, timeout=5)
                        with ZipFile(BytesIO(zip.read())) as zipfile:
                            member = zipfile.namelist()[0]
                            file = zipfile.read(member)
                        if self.download_mode == '':
                            logger.debug('Super download mode succeed.')
                            self.download_mode = 'super'
                    except:
                        logger.debug('Super download mode failed, change to normal mode.')
                        self.download_mode = 'normal'
                        continue
                else:
                    file = urlopen(url, timeout=60)
                    if not file.info().get('Content-Type'):
                        logger.error('You have no download permission.')
                        self.download = False
                        return
                    file = file.read()
                if not os.path.isdir(path):
                    os.makedirs(path)
                with open(fullpath, 'wb') as download_file:
                    download_file.write(file)
                self.counter += 1
                error = 0
                break
            except:
                sleep(randint(30, 60))
                error = 1
        if error == 1:
            logger.error('%s download failed.(%s)', fullpath, url)
        if self.download_mode == 'normal':
            sleep(randint(50, 60))

    def run(self):
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
                    response, _ = self.fetch(url, data, data_type='json')
                    documents += response[0]['documents']
                    if self.download == True:
                        self.DownloadExecutor.map(self.Download, response[0]['documents'])
                    break
                except:
                    response = None
                    logger.debug('Encounter error when opening page %s', i)
                    sleep(randint(30, 60))
            if not response:
                logger.critical("Failed to get page %s's contents. Continuing...", i)
            i += 1
            if i > self.page:
                break
            sleep(randint(5, 10))
        saveCSV(self.filename, self.fieldnames, documents)
        logger.info('Title info crawling finished. Total time: %ss', self.elapsedTime())
        logger.info('Output filename: %s', self.filename)
        if self.download == True:
            logger.info('Please wait for the download process to complete...')
            self.DownloadExecutor.shutdown()
            if self.download == True:
                logger.info('All done, total time: %ss', self.elapsedTime())
                logger.info('Total downloaded files: %s', self.counter)

if __name__ == '__main__':
    job = LiteratureTitle(sys.argv[1])
    job.run()
