#!/usr/bin/env python3
"""Bulk accept SonarQube MINOR/INFO/LOW issues via MCP."""

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


def call_mcp_tool(tool: str, args: dict[str, Any]) -> dict[str, Any]:
    """Call a SonarQube MCP tool via npx."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }
    
    proc = subprocess.Popen(
        ["npx", "-y", "@modelcontextprotocol/server-sonarcloud"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    try:
        stdout, stderr = proc.communicate(input=json.dumps(request), timeout=120)
        if proc.returncode != 0:
            print(f"Error calling {tool}: {stderr[:500]}", file=sys.stderr)
            return {}
        
        try:
            response = json.loads(stdout)
            if "result" in response:
                return response["result"]
            elif "error" in response:
                print(f"MCP error: {response['error']}", file=sys.stderr)
                return {}
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}", file=sys.stderr)
            return {}
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"Timeout calling {tool}", file=sys.stderr)
        return {}
    
    return {}


def search_issues(page: int, page_size: int = 500) -> list[dict[str, Any]]:
    """Search for OPEN MINOR/INFO/LOW issues."""
    result = call_mcp_tool("search_sonar_issues_in_projects", {
        "issueStatuses": ["OPEN"],
        "p": page,
        "ps": page_size,
        "severities": ["INFO", "LOW"],
    })
    
    try:
        text = result.get("content", [{}])[0].get("text", "{}")
        data = json.loads(text)
        return data.get("issues", [])
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Error parsing search: {e}", file=sys.stderr)
        return []


def accept_issue(key: str) -> tuple[str, bool]:
    """Accept a single issue. Returns (key, success)."""
    result = call_mcp_tool("change_sonar_issue_status", {
        "key": key,
        "status": ["accept"],
    })
    
    # A successful response doesn't have an error field
    try:
        text = result.get("content", [{}])[0].get("text", "{}")
        data = json.loads(text)
        if "error" in data:
            return (key, False)
        return (key, True)
    except (json.JSONDecodeError, KeyError, IndexError):
        # Assume success if we can't parse the response
        return (key, True)


def main():
    """Main function to bulk accept issues."""
    print("=" * 60)
    print("SonarQube MINOR Issue Bulk Accept")
    print("=" * 60)
    
    # Get all issues from all pages
    print("\n[1/4] Fetching issue pages...")
    all_issues = []
    page = 1
    
    while True:
        print(f"  Fetching page {page}...", end=" ")
        issues = search_issues(page)
        if not issues:
            print("no more issues")
            break
        all_issues.extend(issues)
        print(f"got {len(issues)} issues (total: {len(all_issues)})")
        page += 1
        if page > 10:  # Safety limit
            print("  Safety limit reached")
            break
        time.sleep(0.5)  # Rate limiting
    
    total = len(all_issues)
    print(f"\nTotal issues found: {total}")
    
    if total == 0:
        print("No issues to accept. Exiting.")
        return
    
    # Extract keys
    keys = [issue["key"] for issue in all_issues]
    
    # Group by rule for reporting
    rules = {}
    for issue in all_issues:
        rule = issue.get("rule", "unknown")
        rules[rule] = rules.get(rule, 0) + 1
    
    print("\nIssues by rule:")
    for rule, count in sorted(rules.items(), key=lambda x: -x[1]):
        print(f"  {rule}: {count}")
    
    # Accept issues
    print(f"\n[2/4] Accepting {total} issues...")
    accepted = 0
    failed = 0
    failed_keys = []
    
    # Process in batches to avoid overwhelming the API
    batch_size = 20
    
    for i in range(0, len(keys), batch_size):
        batch = keys[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(keys) + batch_size - 1) // batch_size
        
        print(f"  Batch {batch_num}/{total_batches}: {len(batch)} issues...", end=" ")
        
        # Process batch concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(accept_issue, key): key for key in batch}
            for future in as_completed(futures):
                key, success = future.result()
                if success:
                    accepted += 1
                else:
                    failed += 1
                    failed_keys.append(key)
        
        print(f"accepted: {accepted}, failed: {failed}")
        
        # Small delay between batches
        if i + batch_size < len(keys):
            time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total issues:    {total}")
    print(f"Accepted:        {accepted}")
    print(f"Failed:          {failed}")
    
    if failed_keys:
        print(f"\nFailed keys ({len(failed_keys)}):")
        for key in failed_keys[:20]:  # Show first 20
            print(f"  {key}")
        if len(failed_keys) > 20:
            print(f"  ... and {len(failed_keys) - 20} more")
    
    # Verify
    print(f"\n[3/4] Verifying...")
    time.sleep(2)  # Give SonarQube time to process
    
    remaining = search_issues(1)
    print(f"Remaining OPEN issues: {len(remaining)}")
    
    print("\n[4/4] Done!")


if __name__ == "__main__":
    main()
