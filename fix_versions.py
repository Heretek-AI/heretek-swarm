#!/usr/bin/env python3
"""Fix __version__ conflicts in heretek_swarm modules."""

import pathlib

files_to_fix = [
    "backend/heretek_swarm/tools/__init__.py",
    "backend/heretek_swarm/mcp/__init__.py",
    "backend/heretek_swarm/integrations/__init__.py",
]

for filepath in files_to_fix:
    p = pathlib.Path(filepath)
    if p.exists():
        content = p.read_text(encoding="utf-8")
        if '__version__ = "0.1.0"' in content:
            content = content.replace('__version__ = "0.1.0"', '__version__ = "0.2.0"')
            p.write_text(content, encoding="utf-8")
            print(f"Fixed: {filepath}")

# Also fix hardcoded "1.0.0" references per plan
import subprocess
result = subprocess.run(
    ["grep", "-r", "1.0.0", "backend/heretek_swarm/"],
    capture_output=True, text=True
)
count = result.stdout.count("0.2.0")
print(f"Verification grep exit code: {result.returncode}")
