import sys, json

data = json.load(sys.stdin)
for i in data['issues']:
    if i['rule'] == 'python:S5655':
        line = i.get('line', '?')
        print(f"{i['component'].split(':')[-1]}:{line}")
