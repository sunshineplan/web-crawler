#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from nnilib.LiteratureEntity import LiteratureEntity
from nnilib.LiteratureList import LiteratureList
from nnilib.LiteratureTitle import LiteratureTitle
from nnilib.NNI import logger

def MainParser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-e',
        help='fetching Literature Entity by Literature ID',
        metavar='<Literature ID>',
        dest='lid')
    group.add_argument(
        '-l',
        help='fetching Literature List by Literature Category\nCategory List[1-4]:\n1:Modern Periodical(近代) 2:Contemporary Periodical(现代)\n3:Chinese Newspaper 4:Foreign Newspaper',
        choices=['1', '2', '3', '4'],
        metavar='<Literature Category>',
        dest='category')
    group.add_argument(
        '-t',
        help='fetching Literature Title by Literature ID',
        metavar='<Literature ID>',
        dest='literatureId')
    return parser

def main():
    parse_args = MainParser().parse_args()
    if parse_args.lid is not None:
        logger.info('Operation Mode: LiteratureEntity')
        logger.info('Literature ID: %s', parse_args.lid)
        job = LiteratureEntity(parse_args.lid)
    elif parse_args.category is not None:
        logger.info('Operation Mode: LiteratureList')
        job = LiteratureList(parse_args.category)
    else:
        logger.info('Operation Mode: LiteratureTitle, Literature ID: %s', parse_args.literatureId)
        job = LiteratureTitle(parse_args.literatureId)
    job.run()


if __name__ == '__main__':
    main()
