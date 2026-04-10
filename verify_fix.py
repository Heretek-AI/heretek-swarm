#!/usr/bin/env python3
"""Verify all Python files in src/heretek_swarm parse correctly."""

import ast
import os

source_dir = 'src/heretek_swarm'
errors = []
scanned = 0

for root, dirs, files in os.walk(source_dir):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            scanned += 1
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                errors.append((filepath, f'Line {e.lineno}: {e.msg}'))
            except Exception as e:
                errors.append((filepath, str(e)))

print(f'Total Python files scanned: {scanned}')
print(f'Files with syntax errors: {len(errors)}')
if errors:
    print()
    print('Errors:')
    for f, e in errors:
        print(f'  {f}: {e}')
else:
    print('All files parse successfully!')
