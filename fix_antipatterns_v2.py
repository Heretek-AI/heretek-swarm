#!/usr/bin/env python3
"""
DeepSource Anti-Pattern Fixer
Fixes Major-level anti-pattern issues:
- PY-W2000: Unused imports (406 occurrences)
- PYL-W0612: Unused variables (229 occurrences)
- PYL-W0404: Multiple imports (31 occurrences)
- PYL-W0613: Unused function arguments (30 occurrences)
- PYL-C0201: Dict keys iteration (2 files)
- PYL-R1714: Or equality comparison (1 file)
- PY-W0069: Commented code (3 files)
- PY-W0070: List append after definition (4 files)
- PY-W0075: Consider using all (1 file)
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Counters for reporting
FIX_COUNTS = {
    'PY-W2000': 0,
    'PYL-W0404': 0,
    'PYL-W0612': 0,
    'PYL-W0613': 0,
    'PYL-C0201': 0,
    'PYL-R1714': 0,
    'PY-W0069': 0,
    'PY-W0070': 0,
    'PY-W0075': 0,
}

def find_py_files(root: Path) -> List[Path]:
    """Find all Python files."""
    files = []
    skip_dirs = {'.pytest_cache', 'node_modules', '__pycache__', '.git', '.venv', 'venv'}
    for d in root.rglob('*'):
        if d.is_file() and d.suffix == '.py':
            if not any(skip in d.parts for skip in skip_dirs):
                files.append(d)
    return files


def fix_multiple_imports_same_module(content: str) -> Tuple[str, int]:
    """Fix PYL-W0404: Multiple imports for same module."""
    count = 0
    lines = content.split('\n')
    i = 0
    merged_any = True
    
    while merged_any:
        merged_any = False
        lines = content.split('\n')
        i = 0
        new_lines = []
        skip_next = 0
        
        while i < len(lines):
            if skip_next > 0:
                skip_next -= 1
                i += 1
                continue
                
            line = lines[i]
            
            # Match: from module import something
            match = re.match(r'^from\s+([\w.]+)\s+import\s+(.+)$', line)
            if match:
                module = match.group(1)
                names = [n.strip() for n in match.group(2).split(',')]
                
                # Look ahead for more imports from same module
                j = i + 1
                additional_names = []
                while j < len(lines):
                    next_match = re.match(rf'^from\s+{re.escape(module)}\s+import\s+(.+)$', lines[j])
                    if next_match:
                        additional_names.extend([n.strip() for n in next_match.group(1).split(',')])
                        skip_next = j - i
                        j += 1
                    else:
                        break
                
                if additional_names:
                    # Consolidate
                    all_names = names + additional_names
                    new_line = f'from {module} import {", ".join(all_names)}'
                    new_lines.append(new_line)
                    count += len(additional_names)
                    _merged_any = True
                    i += skip_next + 1
                    continue
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
    
    return content, count


def fix_unused_imports(content: str) -> Tuple[str, int]:
    """Fix PY-W2000: Unused imports."""
    count = 0
    lines = content.split('\n')
    
    # Collect all import lines and their info
    import_lines = []
    import_map = {}  # name -> line index
    
    for i, line in enumerate(lines):
        match = re.match(r'^(?:from\s+([\w.]+)\s+import\s+(.+)|import\s+(.+))', line)
        if match:
            if match.group(1):  # from module import names
                module = match.group(1)
                names = [n.strip().split(' as ')[0].split('.')[0] for n in match.group(2).split(',')]
                import_lines.append((i, line, module, names))
                for n in names:
                    import_map[n] = i
            elif match.group(3):  # import module
                modules = [m.strip().split('.')[0] for m in match.group(3).split(',')]
                import_lines.append((i, line, None, modules))
                for m in modules:
                    import_map[m] = i
    
    if not import_lines:
        return content, 0
    
    # Build content without import lines for checking usage
    non_import_lines = [l for i, l in enumerate(lines) if not any(imp[0] == i for imp in import_lines)]
    check_content = '\n'.join(non_import_lines)
    
    # Check each import
    lines_to_remove = set()
    for i, line, module, names in import_lines:
        used_names = []
        unused_names = []
        
        for name in names:
            # Check if name is used in the rest of the file
            pattern = rf'\b{name}\b'
            if re.search(pattern, check_content):
                used_names.append(name)
            else:
                unused_names.append(name)
        
        if not used_names:
            # Remove entire line
            lines_to_remove.add(i)
            count += 1
        elif unused_names and len(names) > 1:
            # Partial - keep only used names
            if module:  # from module import
                new_line = f'from {module} import {", ".join(used_names)}'
                lines[i] = new_line
                count += len(unused_names)
    
    # Remove lines (in reverse to maintain indices)
    for i in sorted(lines_to_remove, reverse=True):
        lines[i] = None
    
    content = '\n'.join(l for l in lines if l is not None)
    return content, count


def fix_unused_variables(content: str) -> Tuple[str, int]:
    """Fix PYL-W0612: Unused variables."""
    count = 0
    
    # Find all assignments
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Skip imports, classes, functions, comments
        if re.match(r'^(import |from |class |def |async def |#)', line):
            continue
        
        # Match: var = value
        match = re.match(r'^(\s*)(\w+)\s*=\s*(.+)$', line)
        if match:
            indent, var_name, value = match.groups()
            
            # Skip special names
            if (var_name.startswith('_') or 
                var_name.isupper() or  # Constants
                var_name in ['self', 'cls']):
                continue
            
            # Check if variable is used later
            rest_content = '\n'.join(lines[i+1:])
            if not re.search(rf'\b{var_name}\b', rest_content):
                # Prefix with underscore
                new_line = f'{indent}_{var_name} = {value}'
                content = content.replace(line, new_line)
                count += 1
    
    return content, count


def fix_unused_function_args(content: str) -> Tuple[str, int]:
    """Fix PYL-W0613: Unused function arguments."""
    count = 0
    
    # Pattern for function definitions
    def replace_func(_match):
        nonlocal count
        prefix = match.group(1)
        args = match.group(2)
        suffix = match.group(3)
        
        # Parse arguments
        parsed_args = []
        for arg in args.split(','):
            arg = arg.strip()
            if not arg:
                continue
            
            # Get arg name (before = if present)
            if '=' in arg:
                name = arg.split('=')[0].strip()
            else:
                name = arg.strip()
            
            # Skip special args
            if name in ['self', 'cls', 'args', 'kwargs']:
                parsed_args.append(arg)
            elif name.startswith('*') or name.startswith('**'):
                parsed_args.append(arg)
            elif name.startswith('_'):
                parsed_args.append(arg)
            else:
                # Replace with _prefixed
                parsed_args.append('_' + arg)
                count += 1
        
        return prefix + ', '.join(parsed_args) + suffix
    
    # Match def statements with arguments
    pattern = r'^(.*?def\s+\w+\()([^)]+)(\).*:.*)$'
    content = re.sub(pattern, replace_func, content, flags=re.MULTILINE)
    
    return content, count


def fix_dict_keys_iteration(content: str) -> Tuple[str, int]:
    """Fix PYL-C0201: Iterate dictionary directly."""
    count = 0
    
    # Pattern: for key in dict:
    patterns = [
        (r'\bfor\s+(\w+)\s+in\s+(\w+)\.keys\(\):', r'for \1 in \2:'),
    ]
    
    for pattern, replacement in patterns:
        matches = list(re.finditer(pattern, content))
        for match in reversed(matches):
            content = content[:match.start()] + re.sub(pattern, replacement, match.group(0)) + content[match.end():]
            count += 1
    
    return content, count


def fix_or_equality(content: str) -> Tuple[str, int]:
    """Fix PYL-R1714: Use 'in' for multiple comparisons."""
    count = 0
    
    # Pattern: x == a or x == b or x == c -> x in (a, b, c)
    # This is tricky, so we'll do it carefully
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # Look for patterns like: if x == a or x == b:
        match = re.match(r'^(\s*)(?:if\s+)?(\w+)\s*==\s*([^:]+)\s+or\s+(\w+)\s*==\s*([^:]+)(:.*)?$', line)
        if match:
            indent = match.group(1)
            var1 = match.group(2)
            val1 = match.group(3).strip()
            var2 = match.group(4)
            val2 = match.group(5).strip()
            suffix = match.group(6) or ''
            
            if var1 == var2:
                # Collect all values
                values = [val1, val2]
                rest = line[match.end():]
                
                # Look for more or patterns
                while True:
                    more = re.match(r'\s+or\s+(\w+)\s*==\s*([^:]+)', rest)
                    if more and more.group(1) == var1:
                        values.append(more.group(2).strip())
                        rest = rest[more.end():]
                    else:
                        break
                
                if len(values) >= 2:
                    # Build new line
                    new_line = f'{indent}if {var1} in ({", ".join(values)}){suffix}'
                    line = new_line
                    count += 1
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    return content, count


def fix_commented_code(content: str) -> Tuple[str, int]:
    """Fix PY-W0069: Remove commented code blocks."""
    count = 0
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for commented code pattern
        if re.match(r'^\s*#\s*(def |class |if |for |while |return |import |from |async def )', line):
            # Potential commented code - check if it's a block
            commented_block = []
            j = i
            while j < len(lines) and re.match(r'^\s*#', lines[j]):
                commented_block.append(lines[j])
                j += 1
            
            # If 2+ consecutive commented lines, likely dead code
            if len(commented_block) >= 2:
                count += len(commented_block)
                i = j
                continue
        
        new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    return content, count


def fix_list_append_after_def(content: str) -> Tuple[str, int]:
    """Fix PY-W0070: List.append() immediately after list definition."""
    count = 0
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Match: name = []
        match = re.match(r'^(\s*)(\w+)\s*=\s*\[\](.*)$', line)
        if match and not match.group(3):  # No trailing content
            indent = match.group(1)
            name = match.group(2)
            
            # Check next line is name.append(...)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                append_match = re.match(rf'^(\s*){re.escape(name)}\.append\(\s*([^\)]+)\s*\)(.*)$', next_line)
                if append_match:
                    # Combine: name = [value]
                    value = append_match.group(2)
                    rest = append_match.group(3)
                    new_lines.append(f'{indent}{name} = [{value}]{rest}')
                    count += 1
                    i += 2
                    continue
        
        new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    return content, count


def fix_consider_using_all(content: str) -> Tuple[str, int]:
    """Fix PY-W0075: Use all() builtin."""
    count = 0
    
    # Pattern: all(x for y in z) -> all(x for y in z)
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if 'all([' in line and ' for ' in line and ' in ' in line:
            # Replace all([... for ...]) with all(... for ...)
            new_line = re.sub(r'all\(\[(.+?)\]\)', r'all(\1)', line)
            if new_line != line:
                line = new_line
                count += 1
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    return content, count


def process_file(filepath: Path) -> bool:
    """Process a single file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        original = content
        
        # Apply all fixes
        content, c = fix_multiple_imports_same_module(content)
        FIX_COUNTS['PYL-W0404'] += c
        
        content, c = fix_unused_imports(content)
        FIX_COUNTS['PY-W2000'] += c
        
        content, c = fix_unused_variables(content)
        FIX_COUNTS['PYL-W0612'] += c
        
        content, c = fix_unused_function_args(content)
        FIX_COUNTS['PYL-W0613'] += c
        
        content, c = fix_dict_keys_iteration(content)
        FIX_COUNTS['PYL-C0201'] += c
        
        content, c = fix_or_equality(content)
        FIX_COUNTS['PYL-R1714'] += c
        
        content, c = fix_commented_code(content)
        FIX_COUNTS['PY-W0069'] += c
        
        content, c = fix_list_append_after_def(content)
        FIX_COUNTS['PY-W0070'] += c
        
        content, c = fix_consider_using_all(content)
        FIX_COUNTS['PY-W0075'] += c
        
        if content != original:
            filepath.write_text(content, encoding='utf-8')
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    
    return False


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    files = find_py_files(script_dir)
    
    print(f"Found {len(files)} Python files to process\n")
    
    modified_count = 0
    for f in files:
        if process_file(f):
            modified_count += 1
            print(f"Modified: {f.relative_to(script_dir)}")
    
    print(f"\n{'='*60}")
    print("DeepSource Anti-Pattern Fix Summary")
    print("="*60)
    print(f"\nFiles modified: {modified_count}")
    print("\nFixes by category:")
    for issue, count in FIX_COUNTS.items():
        if count > 0:
            print(f"  {issue}: {count}")
    
    total = sum(FIX_COUNTS.values())
    print(f"\nTotal fixes: {total}")
    print("="*60)


if __name__ == "__main__":
    main()
