#!/bin/bash
# Simple demo for measuring path round-trip
# Uses aggregator/twamp.py for TWAMP-style latency measurement

python aggregator/twamp.py --server &
sleep 1
python aggregator/twamp.py --client --target 127.0.0.1 --port 9000 --samples 200 --outfile twamp_results.csv

