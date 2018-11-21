#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import thread
from sitelib.amazon import Amazon
from sitelib.dangdang import dangdang
from sitelib.jingdong import JD
from sitelib.taobao import Taobao

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('web-crawler.log')
#fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s(%(threadName)s) - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

def MainParser():
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] <content> [<content> ...] [-m <mode> [<mode> ...]] [-d <dir>]')
    parser.add_argument(
        '-m',
        nargs='+',
        help='choose operation mode {az|dd|jd|tb|All} (Default: All)',
        choices=['az', 'dd', 'jd', 'tb', 'all'],
        dest='mode',
        metavar='<mode>',
        type=str.lower,
        default=['all'])
    parser.add_argument(
        'content',
        nargs='+',
        help='search keyword',
        metavar='<content>')
    parser.add_argument(
        '-d',
        help='output directory (If not specified, the current directory is used.)',
        default='',
        dest='path',
        metavar='<dir>')
    return parser

def main():
    parse_args = MainParser().parse_args()
    if 'all' in parse_args.mode:
        logger.info('Operation Mode: All')
        selectors = ['Amazon', 'dangdang', 'JD', 'Taobao']
    else:
        selectors = []
        if 'az' in parse_args.mode:
            logger.info('Operation Mode: amazon.cn')
            selectors.append('Amazon')
        if 'dd' in parse_args.mode:
            logger.info('Operation Mode: dangdang.com')
            selectors.append('dangdang')
        if 'jd' in parse_args.mode:
            logger.info('Operation Mode: JD.com')
            selectors.append('JD')
        if 'tb' in parse_args.mode:
            logger.info('Operation Mode: Taobao.com')
            selectors.append('Taobao')
    job = [ eval(selector + "('" + keyword + "', '" + parse_args.path + "')") for keyword in parse_args.content for selector in selectors ]
    try:
        with ThreadPoolExecutor(len(selectors), 'MT') as executor:
            for i in job:
                executor.submit(i.run)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
