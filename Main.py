#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from sitelib.dangdang import dangdang
from sitelib.jingdong import JD

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
        help='choose operation mode (jd/dd)',
        choices=['jd', 'dd'],
        dest='mode',
        metavar='<mode>',
        type=str.lower,
        required=True)
    parser.add_argument(
        'content',
        help='search keyword',
        metavar='<content>')
    return parser

def main():
    parse_args = MainParser().parse_args()
    if parse_args.mode == 'jd':
        logger.info('Operation Mode: JD.com')
        logger.info('Keyword: %s', parse_args.content)
        job = JD(parse_args.content)
    elif parse_args.mode == 'dd':
        logger.info('Operation Mode: dangdang.com')
        logger.info('Keyword: %s', parse_args.content)
        job = dangdang(parse_args.content)
    job.run()


if __name__ == '__main__':
    main()
