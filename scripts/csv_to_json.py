"""Convert csv to json to pipe into jq."""

# python csv_to_json.py filename.csv | jq .rows[0]

import csv
import json
import sys

filename = sys.argv[1]
with open(filename, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    rows = [x for x in reader]
    print(json.dumps({'rows': rows}))
