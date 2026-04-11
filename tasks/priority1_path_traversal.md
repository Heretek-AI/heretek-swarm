# Priority 1: CRITICAL - Path Traversal Vulnerability

## Objective
Fix the path traversal vulnerability in src/rag/document_processor.py:340

## Issue Details
- **Rule:** pythonsecurity:S2083
- **Issue:** Constructing file paths from user-controlled data allows directory traversal attacks

## Remediation
Implement a safe path validation function:

```python
from pathlib import Path
import os

def safe_path(base_dir: Path, user_input: str) -> Path:
    resolved_base = base_dir.resolve()
    requested_path = (base_dir / user_input).resolve()
    if not str(requested_path).startswith(str(resolved_base)):
        raise ValueError("Path traversal detected")
    return requested_path
```

## Verification
1. Test with malicious input like `../../etc/passwd`
2. Ensure the function raises ValueError for traversal attempts
3. Confirm legitimate paths still work correctly