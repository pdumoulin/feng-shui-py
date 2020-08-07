#!/usr/bin/python3

"""Base64 and JSON decode data with pretty output."""

import base64
import json
import pprint
import traceback
import sys

for line in [x for x in sys.stdin]:
    print(line)
    print('--------')
    try:
        output = json.loads(base64.b64decode(line).decode('utf-8'))
        pprint.pprint(output)
    except Exception:
        traceback.print_exc()
    print('')
