#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from multiprocessing.pool import ThreadPool
from sitelib.dangdang import dangdang
from sitelib.jingdong import JD
from sitelib.amazon import Amazon

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
    parser = argparse.ArgumentParser(usage='%(prog)s [-h] <content> [<content> ...] -m <mode> [<mode> ...] [-d <dir>]')
    parser.add_argument(
        '-m',
        nargs='+',
        help='choose operation mode (jd/dd/All)',
        choices=['jd', 'dd', 'az', 'all'],
        dest='mode',
        metavar='<mode>',
        type=str.lower,
        required=True)
    parser.add_argument(
        'content',
        nargs='+',
        help='search keyword',
        metavar='<content>')
    parser.add_argument(
        '-d',
        help='output directory',
        default='',
        dest='path',
        metavar='<dir>')
    return parser

def main():
    parse_args = MainParser().parse_args()
    pool = ThreadPool()
    if 'all' in parse_args.mode:
        logger.info('Operation Mode: All')
        for i in parse_args.content:
            pool.apply_async(JD(i, parse_args.path).run)
        for i in parse_args.content:
            pool.apply_async(dangdang(i, parse_args.path).run)
        for i in parse_args.content:
            pool.apply_async(Amazon(i, parse_args.path).run)
    else:
        if 'jd' in parse_args.mode:
            logger.info('Operation Mode: JD.com')
            for i in parse_args.content:
                pool.apply_async(JD(i, parse_args.path).run)
        if 'dd' in parse_args.mode:
            logger.info('Operation Mode: dangdang.com')
            for i in parse_args.content:
                pool.apply_async(dangdang(i, parse_args.path).run)
        if 'az' in parse_args.mode:
            logger.info('Operation Mode: amazon.cn')
            for i in parse_args.content:
                pool.apply_async(Amazon(i, parse_args.path).run)
    pool.close()
    pool.join()

                
if __name__ == '__main__':
    main()
