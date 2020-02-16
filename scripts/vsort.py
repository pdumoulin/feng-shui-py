#!/usr/bin/python3

"""Sort version strings, including ends with "rc#."""

import re
import sys


def compare(vone, vtwo):
    """Entrypoint to compare two values."""
    # split on - . and rc
    split_str = '[-.]|rc'
    vone = re.split(split_str, vone)
    vtwo = re.split(split_str, vtwo)

    # remove non-digit values
    vone = [x for x in vone if x.isdigit()]
    vtwo = [x for x in vtwo if x.isdigit()]

    # zero pad all digits to be same length
    max_digit_len = len(max(vone + vtwo, key=len))
    vone = ''.join([str(item).zfill(max_digit_len) for item in vone])
    vtwo = ''.join([str(item).zfill(max_digit_len) for item in vtwo])

    # tie breaker, shorter first
    vone_longer = False
    vtwo_longer = False
    if len(vone) > len(vtwo):
        vone_longer = True
    if len(vtwo) > len(vone):
        vtwo_longer = True

    # auto-fill 9s to shorter versions, shorter first
    while len(vone) > len(vtwo):
        vtwo = vtwo + '9'
    while len(vtwo) > len(vone):
        vone = vone + '9'

    # determine based on basic sort
    if vone > vtwo:
        return 1
    elif vone < vtwo:
        return -1
    else:

        # tie breaker is auto-fills cause identical strings
        if vtwo_longer:
            return 1
        elif vone_longer:
            return -1
    return 0


def cmp_to_key(mycmp):
    """Convert a cmp= function into a key= function.

    https://docs.python.org/3/howto/sorting.html#the-old-way-using-the-cmp-parameter
    """
    class K:

        def __init__(self, obj, *args):
            self.obj = obj

        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0

    return K


max_results = int(sys.argv[1])

versions = []
for line in sys.stdin:
    versions.append(line.replace('\n', ''))

versions = sorted(versions, key=cmp_to_key(compare))
versions = versions[len(versions) - max_results:]
for v in versions:
    print(v)
