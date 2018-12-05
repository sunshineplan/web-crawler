#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from urllib.parse import urlencode
from urllib.request import Request
from urllib.request import urlopen
from lib.comm import getAgents

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
        agent, error = getAgents()
        if error == 0:
            logger.debug('Download user agents list successful.')
        else:
            logger.debug('Download user agents list failed. Use custom list instead.')
        self.agent = agent[0]
        self.csrf = self.getCSRF()

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

    def fetch(self, url, data, headers, data_type=''):
        if data_type == 'json':
            data = json.dumps(data).encode('utf8')
        else:
            data = urlencode(data).encode('utf8')
        request = Request(url, data, headers)
        response = urlopen(request)
        #logger.debug(request.header_items())
        jsonresponse = json.loads(response.read().decode('utf8'))
        return jsonresponse
