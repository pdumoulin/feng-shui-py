#!/usr/bin/python3

"""Add double quotes to list of values from stdin."""

import sys
formatted = ["\n'%s'" % x.rstrip('\n\r')for x in sys.stdin]
print(','.join(formatted))
