import sys, json, re

data = json.load(sys.stdin)
for i in data['issues']:
    if i['rule'] == 'python:S3776':
        line = i.get('line', '?')
        msg = i.get('message', '')
        m = re.search(r'from (\d+) to', msg)
        score = int(m.group(1)) if m else 0
        print(f"{score}:{i['component'].split(':')[-1]}:{line}")
