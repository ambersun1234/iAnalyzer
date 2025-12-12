#!/usr/bin/env python3

import argparse
import sys
from src.core.analyzer import ImageAnalyzer
from src.logger.logger import logger


def main():
    parser = argparse.ArgumentParser(description='Analyze images on a website')
    parser.add_argument('--domain', required=True,
                        help='Domain to analyze (e.g., https://example.com)')
    parser.add_argument('--ignore-prefix', action='append', default=[],
                        help='URL prefix to ignore (can be used multiple times, e.g., --ignore-prefix https://example.com/tags)')
    args = parser.parse_args()

    analyzer = ImageAnalyzer(args.domain, ignore_prefixes=args.ignore_prefix)
    analyzer.analyze()


if __name__ == '__main__':
    main()
