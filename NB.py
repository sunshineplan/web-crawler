#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import build_opener
from math import ceil
from time import sleep


class NB():
    def __init__(self):
        self.url = 'NB/'
        self.opener = build_opener()
        self.opener.addheaders.append(('Cookie',self.getCookie()))
        self.opener.open(self.url + 'search.jsp?menuName=%D5%E3%B6%AB%C8%D5%B1%A8&year=1942')

    def getCookie(self):
        request = Request(self.url, method='HEAD')
        for attempts in range(3):
            try:
                headers = urlopen(request)
                break
            except:
                print('[Error]Failed to fetch headers.')
                sleep(60)
        cookie = headers.info().get('Set-Cookie')
        return cookie[:cookie.find(';')]

    def getName(self):
        for attempts in range(3):
            try:
                html = urlopen(self.url + 'searchresultinfo.jsp').read()
                break
            except:
                print('[Error]Failed to fetch name value.')
                sleep(60)
        soupContent = BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        content = soupContent.find('select', attrs={'name':'range'})
        list = content.find_all('option')
        result = []
        for i in list:
            result.append(i.text)
        result.remove('所有报纸')
        print('[Debug]getName: ' + ','.join(result))
        return result

    def getYear(self, name):
        for attempts in range(3):
            try:
                html = urlopen(self.url + 'menu.jsp').read()
                break
            except:
                print('[Error]Failed to fetch year value.')
                sleep(60)
        soupContent = BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        content = soupContent.find_all('a', href=re.compile('=' + name + '&'))
        result = []
        for i in content:
            year = i.text
            result.append(year[0:4])
        print('[Debug]' + name + ' getYear: ' + ','.join(result))
        return result

    def getPage(self, name, year):
        url = self.url + 'search.jsp?menuName={0}&year={1}'
        for attempts in range(3):
            try:
                html = urlopen(url.format(quote(name, encoding='gbk'), year)).read()
                break
            except:
                print('[Error]Failed to fetch page value.')
                sleep(60)
        soupContent = BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        content = soupContent.find('span', class_='pagebanner')
        try:
            record = content.b.text.replace(',','')
        except AttributeError:
            page = 1
        page = ceil((int(record)/20))
        print('[Debug]' + name + ' ' + year + ' getPage: ' + str(page))
        return page

    def openUrl(self, url):
        for attempts in range(10):
            try:
                html = self.opener.open(url).read()
                break
            except:
                print('[Error]Encounter error when opening ' + url)
                sleep(30)
        soupContent = BeautifulSoup(html, 'html.parser', from_encoding='GBK')
        return soupContent

    def parse(self, content):
        content = content.find_all('tr', class_=re.compile('odd|even'))
        for i in content:
            row = i.find_all('td')
            link = self.url + i.find('a')['href']
            result = []
            for i in row:
                result.append(i.text.strip())
            result.append(link)
            print('\t'.join(result))

    def run(self):
        url = self.url + 'search.jsp?menuName={0}&year={1}&d-3995381-p={2}'
        name = self.getName()
        for n in name:
            year = self.getYear(n)
            for y in year:
                page = self.getPage(n,y)
                i = 1
                while i <= page:
                    self.parse(self.openUrl(url.format(quote(n, encoding='gbk'), y, i)))
                    i += 1
                    sleep(1)


if __name__ == "__main__":
    job = NB()
    job.run()
