"""Fix S1192 string duplication issues."""
import os

_RATE_LIMIT_MSG = "Rate limit exceeded"

fixes = {
    "backend/heretek_swarm/api/observability/events.py": [
        (_RATE_LIMIT_MSG, "_RATE_LIMIT_MSG"),
    ],
    "backend/heretek_swarm/api/observability/external_calls.py": [
        (_RATE_LIMIT_MSG, "_RATE_LIMIT_MSG"),
    ],
    "backend/heretek_swarm/api/observability/swarm.py": [
        (_RATE_LIMIT_MSG, "_RATE_LIMIT_MSG"),
    ],
}

for filepath, replacements in fixes.items():
    full_path = os.path.join(os.getcwd(), filepath)
    if not os.path.exists(full_path):
        print(f"SKIP (not found): {filepath}")
        continue
    content = open(full_path, encoding="utf-8").read()
    for old, new in replacements:
        content = content.replace(f'"{old}"', f'"{new}"')
    # Add constant definition after imports
    lines = content.split("\n")
    # Find the last import line
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_idx = i + 1
    lines.insert(insert_idx + 1, "")
    lines.insert(insert_idx + 1, f'_RATE_LIMIT_MSG = "{_RATE_LIMIT_MSG}"')
    content = "\n".join(lines)
    open(full_path, "w", encoding="utf-8").write(content)
    print(f"OK: {filepath}")
print("Done")
