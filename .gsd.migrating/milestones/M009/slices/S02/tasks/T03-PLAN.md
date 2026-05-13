---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T03: Fix SPA catch-all dist path in main.py

Fix SPA catch-all dist path in main.py. Change the default DASHBOARD_DIST_PATH from os.path.join(project_root, 'dashboard', 'frontend', 'dist') to os.path.join(project_root, 'swarm-dashboard', 'dist'). There are 3 occurrences around lines 429, 1249, and 1281.

## Inputs

- `backend/heretek_swarm/api/main.py`

## Expected Output

- `SPA catch-all defaults to swarm-dashboard/dist instead of dashboard/frontend/dist`

## Verification

grep -c 'swarm-dashboard.*dist' backend/heretek_swarm/api/main.py
