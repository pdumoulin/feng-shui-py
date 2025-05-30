#!/bin/bash

set -e

ruff check *.py --select I,F,E,W,B
ruff format *.py --diff --no-cache
mypy . --exclude conf
