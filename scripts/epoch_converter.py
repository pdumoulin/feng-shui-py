#!/usr/bin/python3

"""UNIX Epoch Time Converter."""

import argparse
import datetime
import time

import pytz


# read in arguments
parser = argparse.ArgumentParser()
parser.add_argument('-f', required=False, default='%Y-%m-%d %H:%M:%S %Z',
                    type=str, help='time format to output')
parser.add_argument('-z', required=False, default='America/New_York',
                    type=str, help='timezone to compare with UTC')
parser.add_argument('-m', action='store_true', default=False,
                    required=False, help='read input as milliseconds')
parser.add_argument('timestamp',
                    type=int, help='UNIX timestamp value to examine')
args = parser.parse_args()

time_format = args.f
time_zone = args.z
milliseconds = args.m
timestamp = args.timestamp

local_tz = pytz.timezone(time_zone)
utc_tz = pytz.timezone('UTC')

# print out human readable datetimes
if milliseconds:
    timestamp = timestamp / 1000

# convert to timezone aware datetime objects
datestamp_utc = datetime.datetime.fromtimestamp(timestamp, tz=utc_tz)
datestamp_lcl = datetime.datetime.fromtimestamp(timestamp, tz=local_tz)

# show the user formatted dates
print('UTC: %s' % datestamp_utc.strftime(time_format))
print('LCL: %s' % datestamp_lcl.strftime(time_format))

# show time different from now
now = time.time()
diff = now - timestamp
future = diff < 0
diff = abs(diff)
days = int(diff / 86400)
diff = diff % 86400
hours = int(diff / 3600)
diff = diff % 3600
minutes = int(diff / 60)
diff = diff % 60
seconds = int(diff)

print('Days:    %s' % days)
print('Hours:   %s' % hours)
print('Minutes: %s' % minutes)
print('Seconds: %s' % seconds)
if future:
    print('until')
else:
    print('ago')
print('')
