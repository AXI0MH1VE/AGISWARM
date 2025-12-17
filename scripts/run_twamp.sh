#!/bin/bash
# Simple demo for measuring path round-trip
# Requires Python twamp.py (not included in above, mock below)

python twamp.py server &
sleep 1
python twamp.py client --target 127.0.0.1 --port 9000 --samples 200 > twamp_results.csv

