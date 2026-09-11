#!/usr/bin/env python3
"""
${TM_NEW_FILE_BASENAME}.py

Created by ${TM_FULLNAME} on ${TM_DATE}.
Copyright (c) ${TM_YEAR} ${TM_ORGANIZATION_NAME}. All rights reserved.
"""

import argparse
import sys


def parse_arguments(argv):
	parser = argparse.ArgumentParser(description="The help message goes here.")
	parser.add_argument("-o", "--output", help="where to write the result")
	parser.add_argument("-v", "--verbose", action="store_true")
	return parser.parse_args(argv)


def main(argv=None):
	arguments = parse_arguments(argv)
	return 0


if __name__ == "__main__":
	sys.exit(main())
