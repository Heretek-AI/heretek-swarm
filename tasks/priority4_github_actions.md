# Priority 4: LOW - GitHub Actions Unpinned Dependencies

## Objective
Fix 20+ issues with unpinned GitHub Actions dependencies.

## Files to Fix
- .github/workflows/ci-cd.yml - 12 issues
- .github/workflows/ci.yml - 7 issues

## Rules
githubactions:S7637, githubactions:S7636

## Issues
1. Using tag names instead of full SHA hashes (e.g., `@v3` instead of `@abc123...`)
2. Expanding secrets in run blocks

## Remediation
```yaml
# BEFORE (Vulnerable to tag moving)
uses: actions/checkout@v3

# AFTER (Pinned to SHA)
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1

# BEFORE (Secret in run block)
run: echo "${{ secrets.MY_SECRET }}"

# AFTER (Use env)
env:
  MY_SECRET: ${{ secrets.MY_SECRET }}
run: echo "$MY_SECRET"
```

## Verification
1. All actions pinned to SHA
2. No secrets in run blocks
3. Workflows function correctly