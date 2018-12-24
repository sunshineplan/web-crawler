#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from time import time
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import build_opener
from urllib.request import install_opener
from random import randint
from lib.comm import getAgent

import logging
logger = logging.getLogger('NNI')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('NNI.log')
#fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

class NNI:
    def __init__(self):
        self.url = 'NNI'
        self.agent, error = getAgent(1)
        if error == 0:
            logger.debug('Getting user agent successful.')
        else:
            logger.error('Getting user agent failed. Use custom agent instead.')
        self.cookies, self.csrf = self.getCookies()
        self.opener = build_opener()
        self.opener.addheaders = [('User-Agent', self.agent), ('Cookie', self.cookies)]
        install_opener(self.opener)
        self.beginTime = time()

    def getCookies(self):
        request = Request(self.url, method='HEAD', headers={'User-Agent': self.agent})
        for attempts in range(3):
            try:
                headers = urlopen(request)
                setCookies = headers.info().get_all('Set-Cookie')
                cookies = []
                for i in setCookies:
                    if 'XSRF-TOKEN' in i:
                        csrf = i[i.find('=')+1:i.find(';')]
                        cookies.append(i[:i.find(';')])
                    elif 'SESSION' in i:
                        cookies.append(i[:i.find(';')])
                break
            except:
                cookies = None
                logger.error('Failed to fetch headers.')
                sleep(randint(30, 60))
        if not cookies:
            logger.critical('Failed to get Cookies. Exiting...')
            sys.exit()
        return ';'.join(cookies), csrf

    def fetch(self, url, data=None, data_type=''):
        header = {}
        if data:
            if data_type == 'json':
                data = json.dumps(data).encode('utf8')
                header = {'Content-Type': 'application/json'}
            else:
                data = urlencode(data).encode('utf8')
        request = Request(url, data, header)
        response = urlopen(request)
        #logger.debug(request.header_items())
        jsonresponse = json.loads(response.read().decode('utf8'))
        return jsonresponse, response.info()

    def elapsedTime(self):
            return '%.2f' % (time() - self.beginTime)
