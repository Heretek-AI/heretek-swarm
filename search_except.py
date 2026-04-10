#!/usr/bin/env python3
"""Search for exception patterns in Python files."""

import os
import sys

def search_file(_filepath):
    """Search for except patterns in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []
    
    matches = []
    for i, line in enumerate(lines, 1):
        if 'except' in line.lower():
            matches.append((i, line.rstrip()))
    return matches

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_except.py <file_path>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)
    
    print(f"Searching for 'except' in: {filepath}")
    print("-" * 60)
    
    matches = search_file(filepath)
    if matches:
        for line_num, line in matches:
            print(f"{line_num}: {line}")
    else:
        print("No 'except' statements found.")

if __name__ == "__main__":
    main()
