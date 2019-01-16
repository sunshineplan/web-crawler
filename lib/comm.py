#!/usr/bin/python3
# coding:utf-8

try:
    from bs4 import BeautifulSoup
except ImportError:
    from sys import executable
    from subprocess import check_call
    check_call([executable, '-m', 'pip', 'install', 'beautifulsoup4'])
    from bs4 import BeautifulSoup
from urllib.request import Request
from urllib.request import urlopen

def getAgent(n=None):
    try:
        url = 'https://techblog.willshouse.com/2012/01/03/most-common-user-agents/'
        request = Request(url, headers = {'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)'})
        html = BeautifulSoup(urlopen(request), 'html.parser')
        agent = html.find('textarea', class_='get-the-list')
        agent = agent.text.splitlines()
        error = 0
    except:
        agent = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36 OPR/56.0.3051.99',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36 Maxthon/5.2.5.3000',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6788.400 QQBrowser/10.3.2714.400',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4094.1 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36 LBBROWSER'
            ]
        error = 1
    if n == 1:
        return agent[0], error
    elif not n:
        return agent, error
    else:
        try:
            return agent[:n], error
        except:
            return agent[:4], error
