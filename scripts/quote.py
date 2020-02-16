#!/usr/bin/python3

"""Add double quotes to list of values from stdin."""

import sys
formatted = ["\n'%s'" % x.replace('\n', '') for x in sys.stdin]
print(','.join(formatted))
