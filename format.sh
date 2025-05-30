#!/bin/bash

set -e

ruff check --select I --fix *.py
ruff format *.py
