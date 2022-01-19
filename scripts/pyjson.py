#!/usr/bin/python3

"""Python to JSON encode data with pretty output."""

import json
import sys
import traceback

for line in [x for x in sys.stdin]:
    obj_line = eval(line)
    print(type(obj_line))
    print(obj_line)
    print('--------')
    try:
        output = json.dumps(obj_line)
        print(output)
    except Exception:
        print(line)
        traceback.print_exc()
    print('')
