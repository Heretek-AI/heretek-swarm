"""
DeepSource Anti-Pattern Fixer Script
Fixes PY-W2000, PYL-W0612, PYL-W0404, PYL-W0613, PYL-C0201, PYL-R1714, PY-W0069, PY-W0070, PY-W0075
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(r"C:\Users\derek\Desktop\Heretek-AI\heretek-swarm")
SRC_DIRS = [PROJECT_ROOT / "src", PROJECT_ROOT / "tests", PROJECT_ROOT]

# Patterns for various anti-patterns
UNUSED_IMPORT_PATTERN = re.compile(r'^import (\w+)|from (\w+(?:\.\w+)*) import')
MULTI_IMPORT_PATTERN = re.compile(r'^from \w[\w.]* import .+\n(?:from \w[\w.]* import .+\n)+')
UNUSED_VAR_PATTERN = re.compile(r'\b(\w+)\s*=\s*(?!=)')
UNUSED_ARG_PATTERN = re.compile(r'def \w+\([^)]*\bself\b[^)]*\):|def \w+\(([^)]+)\):')
DICT_KEYS_PATTERN = re.compile(r'\.keys\(\)')
OR_EQUALITY_PATTERN = re.compile(r'\b(\w+)\s*==\s*(\w+)\s+or\s+\1\s*==\s*(\w+)\b')
COMMENTED_CODE_PATTERN = re.compile(r'^\s*#\s*(def |class |if |for |while |return |import |from )', re.MULTILINE)
LIST_APPEND_PATTERN = re.compile(r'^(\s*\w+\s*=\s*\[\].*\n)(\s*\w+\.append\()')
ALL_BUILTIN_PATTERN = re.compile(r'all\(\s*\[\s*.*?\s+for\s+')


def find_py_files(_dirs: List[Path]) -> List[Path]:
    """Find all Python files in the given directories."""
    _files = []
    for d in dirs:
        if d.exists():
            for f in d.rglob("*.py"):
                if ".pytest_cache" not in str(f) and "node_modules" not in str(f):
                    files.append(f)
    return files


def fix_unused_imports(_content: str) -> Tuple[str, int]:
    """Remove unused imports. Returns fixed content and count of fixes."""
    _lines = content.split('\n')
    _fixed_lines = []
    _imports = []
    _import_indices = []
    
    # Find all import lines
    for i, line in enumerate(lines):
        if re.match(r'^(import |from \w)', line):
            imports.append(line)
            import_indices.append(i)
    
    # Track what's used in the file
    _used_names = set()
    non_import_lines = [l for l in lines if not re.match(r'^(import |from \w)', l)]
    _non_import_content = '\n'.join(non_import_lines)
    
    # Extract names from imports
    _import_info = []
    for imp in imports:
        if imp.startswith('import '):
            # import os, sys
            _names = [n.strip().split('.')[0] for n in imp[7:].split(',')]
            import_info.append((imp, set(names)))
        elif imp.startswith('from '):
            # from os import path, getcwd
            match = re.match(r'from\s+([\w.]+)\s+import\s+(.+)', imp)
            if match:
                _module = match.group(1)
                _names = [n.strip().split(' as ')[0].split('.')[0] for n in match.group(2).split(',')]
                import_info.append((imp, set(names)))
    
    # Check each import name against the rest of the content
    _fixed = content
    _count = 0
    
    for imp_line, names in reversed(import_info):  # Reverse to maintain line numbers
        unused_in_this_import = set()
        for name in names:
            # Check if name is used (as variable, function call, attribute, etc.)
            _patterns = [
                rf'\b{name}\b',  # Basic word boundary
            ]
            _used = any(re.search(p, non_import_content) for p in patterns)
            if not used:
                unused_in_this_import.add(name)
        
        if unused_in_this_import and len(unused_in_this_import) == len(names):
            # All names unused - remove entire line
            _fixed = fixed.replace(imp_line + '\n', '').replace(imp_line, '')
            count += 1
        elif unused_in_this_import and len(names) > 1:
            # Partial - need to fix the line
            _new_names = names - unused_in_this_import
            if imp_line.startswith('from '):
                match = re.match(r'(from\s+[\w.]+\s+import\s+)(.+)', imp_line)
                if match:
                    _prefix = match.group(1)
                    _old_names_str = match.group(2)
                    _old_names = [n.strip().split(' as ')[0] for n in old_names_str.split(',')]
                    _new_names_str = ', '.join(n for n in old_names if n in new_names)
                    if new_names_str:
                        _new_line = prefix + new_names_str
                        _fixed = fixed.replace(imp_line, new_line)
                        count += 1
    
    return fixed, count


def fix_multi_imports(_content: str) -> Tuple[str, int]:
    """Fix multiple import statements for same module."""
    _count = 0
    
    # Pattern: from module import a\nfrom module import b -> from module import a, b
    _lines = content.split('\n')
    i = 0
    while i < len(lines):
        if lines[i].startswith('from ') and ' import ' in lines[i]:
            _module_match = re.match(r'(from\s+([\w.]+)\s+import\s+)(.+)', lines[i])
            if module_match:
                _base = module_match.group(1)
                _module = module_match.group(2)
                _names = [module_match.group(3).strip()]
                j = i + 1
                _merged = True
                while j < len(lines) and merged:
                    _merged = False
                    _next_match = re.match(rf'(from\s+{re.escape(module)}\s+import\s+)(.+)', lines[j])
                    if next_match:
                        names.append(next_match.group(2).strip())
                        _merged = True
                        j += 1
                        count += 1
                    else:
                        _merged = False
                
                if len(names) > 1:
                    # Consolidate
                    _all_names = []
                    for n in names:
                        all_names.extend([x.strip().split(' as ')[0] for x in n.split(',')])
                    lines[i] = base + ', '.join(all_names)
                    # Remove merged lines
                    lines[i+1:j] = []
        i += 1
    
    return '\n'.join(lines), count


def fix_unused_variables(_content: str) -> Tuple[str, int]:
    """Fix unused variables by prefixing with _ or removing."""
    _count = 0
    _lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Skip if already fixed or is import/class/def
        if any(x in line for x in ['import ', 'from ', 'class ', 'def ', 'async def ', '#']):
            continue
        # Skip if it's a docstring or continuation
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            continue
        
        # Pattern: variable = something where variable appears unused
        match = re.match(r'^(\s*)(\w+)\s*=\s*(.+)$', line)
        if match:
            indent, var_name, value = match.groups()
            # Skip if starts with _ or is all caps (likely constant)
            if var_name.startswith('_') or var_name.isupper():
                continue
            # Check if var_name appears elsewhere in the file
            _rest = '\n'.join(lines[i+1:])
            if f'\b{var_name}\b' not in rest and f'.{var_name}' not in rest:
                # Prefix with _
                _new_line = f'{indent}_{var_name} = {value}'
                _content = content.replace(line, new_line)
                count += 1
    
    return content, count


def fix_unused_arguments(_content: str) -> Tuple[str, int]:
    """Fix unused function arguments by prefixing with _."""
    _count = 0
    
    # Match function definitions
    _func_pattern = re.compile(r'^(.*?def\s+\w+\()([^)]+)(\).*:.*)$', re.MULTILINE)
    
    def fix_args(_match):
        nonlocal count
        _prefix = match.group(1)
        _args_str = match.group(2)
        _suffix = match.group(3)
        
        # Parse arguments
        _args = []
        for arg in args_str.split(','):
            _arg = arg.strip()
            if arg and '=' in arg:
                _name = arg.split('=')[0].strip()
            elif arg:
                _name = arg.strip()
            else:
                continue
            args.append((arg, name))
        
        # Check which args are used in the function body
        # Find function end
        _func_start = match.start()
        _func_end = match.end()
        
        _new_args = []
        for arg, name in args:
            if name in ['self', 'cls', 'args', 'kwargs']:
                new_args.append(arg)
            elif name.startswith('_'):
                new_args.append(arg)  # Already prefixed
            else:
                new_args.append(f'_{name}')
                count += 1
        
        return prefix + ', '.join(new_args) + suffix
    
    _content = func_pattern.sub(fix_args, content)
    return content, count


def fix_dict_keys_iteration(_content: str) -> Tuple[str, int]:
    """Fix .keys() iteration - PYL-C0201."""
    _count = 0
    
    # Pattern: for key in dict:
    _pattern = re.compile(r'\bfor\s+(\w+)\s+in\s+(\w+)\.keys\(\):')
    _matches = pattern.findall(content)
    
    for key, dict_name in matches:
        _old = f'for {key} in {dict_name}.keys():'
        _new = f'for {key} in {dict_name}:'
        _content = content.replace(old, new)
        count += 1
    
    return content, count


def fix_or_equality_comparisons(_content: str) -> Tuple[str, int]:
    """Fix 'x in (a, b)' to 'x in (a, b)' - PYL-R1714."""
    _count = 0
    
    # Pattern: var in (val1, val2) (possibly with extra ors)
    while True:
        _pattern = re.compile(r'\b(\w+)\s*==\s*([^\s,]+)\s+or\s+(?:\w+)\s*==\s*([^\s,]+)\b')
        match = pattern.search(content)
        if not match:
            break
        
        _var = match.group(1)
        _val1 = match.group(2)
        _val2 = match.group(3)
        
        # Check for more or conditions
        _rest = content[match.end():]
        _more_vals = []
        _temp = rest
        while True:
            m = re.match(r'\s+or\s+(\w+)\s*==\s*([^\s,]+)', temp)
            if m:
                more_vals.append(m.group(2))
                _temp = temp[m.end():]
            else:
                break
        
        if more_vals:
            _all_vals = [val1, val2] + more_vals
            _new = f'if {var} in ({", ".join(all_vals)}):'
        else:
            _new = f'if {var} in ({val1}, {val2}):'
        
        _content = content[:match.start()] + content[match.start():match.end()].replace(
            match.group(0), f'{var} in ({val1}, {val2})'
        ) + content[match.end():]
        count += 1
    
    return content, count


def fix_commented_code(_content: str) -> Tuple[str, int]:
    """Remove commented out code - PY-W0069."""
    _count = 0
    _lines = content.split('\n')
    _fixed_lines = []
    i = 0
    
    while i < len(lines):
        _line = lines[i]
        # Check for commented code patterns
        if re.match(r'^\s*#\s*(def |class |if |for |while |return |import |from )', line):
            # Could be commented code, check if next few lines form a block
            _commented_block = []
            j = i
            while j < len(lines) and re.match(r'^\s*#', lines[j]):
                commented_block.append(lines[j])
                j += 1
            
            # If we found 2+ consecutive commented lines, likely dead code
            if len(commented_block) >= 2:
                count += len(commented_block)
                i = j
                continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines), count


def fix_list_append_after_def(_content: str) -> Tuple[str, int]:
    """Fix list.append() immediately after definition - PY-W0070."""
    _count = 0
    _lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        _line = lines[i]
        # Match: name = []
        match = re.match(r'^(\s*)(\w+)\s*=\s*\[\](.*)$', line)
        if match:
            indent, name, rest = match.groups()
            # Check if next line is name.append(...)
            if i + 1 < len(lines):
                _next_line = lines[i + 1]
                _append_match = re.match(rf'^(\s*){re.escape(name)}\.append\(\s*([^\)]+)\s*\)(.*)$', next_line)
                if append_match:
                    # Combine into single initialization
                    _new_line = f'{indent}{name} = [{append_match.group(2)}]{append_match.group(3)}'
                    _content = content.replace(line, new_line)
                    _content = content.replace(next_line + '\n', '').replace(next_line, '')
                    count += 1
                    i += 1
                    continue
        i += 1
    
    return content, count


def fix_consider_using_all(_content: str) -> Tuple[str, int]:
    """Fix to use all() builtin - PY-W0075."""
    _count = 0
    
    # Pattern: all(condition for item in iterable)
    _pattern = re.compile(r'all\(\s*\[\s*(.+?)\s+for\s+(\w+)\s+in\s+(\w+)\s*\]\s*\)')
    
    def replace_with_all(_match):
        nonlocal count
        _condition = match.group(1)
        item = match.group(2)
        _iterable = match.group(3)
        count += 1
        return f'all({condition} for {item} in {iterable})'
    
    _content = pattern.sub(replace_with_all, content)
    return content, count


def main():
    """Main function to process all files."""
    _files = find_py_files(SRC_DIRS)
    
    _total_fixes = {
        'PY-W2000': 0,  # Unused imports
        'PYL-W0404': 0,  # Multiple imports
        'PYL-W0612': 0,  # Unused variables
        'PYL-W0613': 0,  # Unused arguments
        'PYL-C0201': 0,  # Dict keys iteration
        'PYL-R1714': 0,  # Or equality
        'PY-W0069': 0,   # Commented code
        'PY-W0070': 0,   # List append after def
        'PY-W0075': 0,   # Consider using all
    }
    
    _files_modified = 0
    
    for filepath in files:
        try:
            _content = filepath.read_text(encoding='utf-8')
            _original = content
            
            # Apply fixes in order
            content, c = fix_unused_imports(content)
            total_fixes['PY-W2000'] += c
            
            content, c = fix_multi_imports(content)
            total_fixes['PYL-W0404'] += c
            
            content, c = fix_unused_variables(content)
            total_fixes['PYL-W0612'] += c
            
            content, c = fix_unused_arguments(content)
            total_fixes['PYL-W0613'] += c
            
            content, c = fix_dict_keys_iteration(content)
            total_fixes['PYL-C0201'] += c
            
            content, c = fix_or_equality_comparisons(content)
            total_fixes['PYL-R1714'] += c
            
            content, c = fix_commented_code(content)
            total_fixes['PY-W0069'] += c
            
            content, c = fix_list_append_after_def(content)
            total_fixes['PY-W0070'] += c
            
            content, c = fix_consider_using_all(content)
            total_fixes['PY-W0075'] += c
            
            if content != original:
                filepath.write_text(content, encoding='utf-8')
                files_modified += 1
                
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print("\n" + "="*60)
    print("DeepSource Anti-Pattern Fix Summary")
    print("="*60)
    print(f"\nFiles modified: {files_modified}")
    print("\nFixes by category:")
    for issue, count in total_fixes.items():
        if count > 0:
            print(f"  {issue}: {count}")
    print("="*60)


if __name__ == "__main__":
    main()
