import sys, json
from collections import Counter

_REPO_PREFIX = 'heretek-swarm/'

data = json.load(sys.stdin)
issues = data['issues']

# S5655 by file
s5655 = [i for i in issues if i['rule'] == 'python:S5655']
by_file = Counter(i['component'].split(_REPO_PREFIX)[-1] for i in s5655)
print("=== S5655 by File ===")
for f, c in by_file.most_common():
    print(f"{c:3d}  {f}")

# S5655 by function called
print("\n=== S5655 by function called ===")
by_func = Counter()
for i in s5655:
    msg = i['message']
    func = msg.split('Function "')[1].split('"')[0] if 'Function "' in msg else 'unknown'
    by_func[func] += 1
for f, c in by_func.most_common():
    print(f"{c:3d}  {f}")

# S6903 by file
s6903 = [i for i in issues if i['rule'] == 'python:S6903']
by_file2 = Counter(i['component'].split(_REPO_PREFIX)[-1] for i in s6903)
print("\n=== S6903 by File ===")
for f, c in by_file2.most_common():
    print(f"{c:3d}  {f}")

# S5727 by file
s5727 = [i for i in issues if i['rule'] == 'python:S5727']
by_file3 = Counter(i['component'].split(_REPO_PREFIX)[-1] for i in s5727)
print("\n=== S5727 by File ===")
for f, c in by_file3.most_common():
    print(f"{c:3d}  {f}")

# S1192 by file
s1192 = [i for i in issues if i['rule'] == 'python:S1192']
by_file4 = Counter(i['component'].split(_REPO_PREFIX)[-1] for i in s1192)
print("\n=== S1192 by File ===")
for f, c in by_file4.most_common():
    print(f"{c:3d}  {f}")

# S5443 by file
s5443 = [i for i in issues if i['rule'] == 'python:S5443']
by_file5 = Counter(i['component'].split(_REPO_PREFIX)[-1] for i in s5443)
print("\n=== S5443 by File ===")
for f, c in by_file5.most_common():
    print(f"{c:3d}  {f}")

# S1186 by file
s1186 = [i for i in issues if i['rule'] == 'python:S1186']
by_file6 = Counter(i['component'].split(_REPO_PREFIX)[-1] for i in s1186)
print("\n=== S1186 by File ===")
for f, c in by_file6.most_common():
    print(f"{c:3d}  {f}")

# S2638 by file
s2638 = [i for i in issues if i['rule'] == 'python:S2638']
by_file7 = Counter(i['component'].split(_REPO_PREFIX)[-1] for i in s2638)
print("\n=== S2638 by File ===")
for f, c in by_file7.most_common():
    print(f"{c:3d}  {f}")
