#!/usr/bin/python3

"""Add double quotes to list of values from stdin."""

import sys
formatted = [
    "'%s'" % x.rstrip('\n\r')
    for x in sys.stdin
]
print(',\n'.join(formatted))
