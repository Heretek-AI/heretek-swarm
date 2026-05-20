#!/usr/bin/env python3
"""Read newline-delimited ms values from stdin, compute p50/p95/p99/mean/min/max/count."""
import sys, json

vals = sorted([float(l.strip()) for l in sys.stdin if l.strip()])
count = len(vals)
if count == 0:
    print(json.dumps({'p50': None, 'p95': None, 'p99': None, 'mean': None, 'min': None, 'max': None, 'count': 0}))
    sys.exit(0)

def pct(idx):
    i = int((count * idx + 50) / 100)
    i = max(1, min(i, count))
    return vals[i - 1]

mean = sum(vals) / count
print(json.dumps({
    'p50': pct(50), 'p95': pct(95), 'p99': pct(99),
    'mean': round(mean, 2), 'min': vals[0], 'max': vals[-1], 'count': count
}))
