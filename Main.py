#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
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
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

def MainParser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-m',
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
    if parse_args.mode == 'jd':
        logger.info('Operation Mode: JD.com')
        for i in parse_args.content:
            job = JD(i, parse_args.path)
            job.run()
    elif parse_args.mode == 'dd':
        logger.info('Operation Mode: dangdang.com')
        for i in parse_args.content:
            job = dangdang(i, parse_args.path)
            job.run()
    elif parse_args.mode == 'az':
        logger.info('Operation Mode: amazon.cn')
        for i in parse_args.content:
            job = Amazon(i, parse_args.path)
            job.run()
    elif parse_args.mode == 'all':
        logger.info('Operation Mode: All')
        for i in parse_args.content:
            job = JD(i, parse_args.path)
            job.run()
        for i in parse_args.content:
            job = dangdang(i, parse_args.path)
            job.run()
        for i in parse_args.content:
            job = Amazon(i, parse_args.path)
            job.run()


if __name__ == '__main__':
    main()
