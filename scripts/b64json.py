#!/usr/bin/python3

"""Base64 and JSON decode data with pretty output."""

import base64
import json
import pprint
import sys

for line in [x for x in sys.stdin]:
    print(line)
    print('--------')
    output = json.loads(base64.b64decode(line).decode('utf-8'))
    print(pprint.pprint(output))
