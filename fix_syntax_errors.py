#!/usr/bin/env python3
"""
Syntax Error Fix Script for Heretek Swarm

This script repairs syntax errors introduced by the previous underscore prefix fix.

Priority Order:
1. Fix `_*kwargs` and `_*args` patterns (syntax errors)
2. Fix underscore-prefixed comments (`_#`)
3. Fix underscore-prefixed typing module names

Features:
- Scans all Python files in src/heretek_swarm/
- Uses regex to detect and fix patterns
- Creates backups before modifying
- Logs all changes made
- Validates the fixed file can be parsed by Python
"""

import ast
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Callable, Union


# =============================================================================
# CONFIGURATION
# =============================================================================

SOURCE_DIR = "src/heretek_swarm"
BACKUP_DIR = "syntax_fix_backups"
LOG_FILE = "syntax_fix_log.txt"


# =============================================================================
# PATTERN DEFINITIONS
# =============================================================================

# Pattern 1: Underscore-prefixed comments that break function signatures
# Example: def foo(a, b, _# comment) -> def foo(a, b, # comment)
COMMENT_PATTERN = (r'_#\s*', '# ')

# Pattern 2: Invalid *args and **kwargs patterns
# These are actual Python syntax errors
ARGS_KWARGS_PATTERNS = [
    # _*args -> *args
    (r'\b_\*args\b', '*args'),
    # _**kwargs -> **kwargs  
    (r'\b_\*\*kwargs\b', '**kwargs'),
    # _*something -> *something (any varargs pattern)
    (r'(?<![a-zA-Z0-9_])_\*(\w+)', lambda m: f'*{m.group(1)}'),
    # _**something -> **something (any kwargs pattern)
    (r'(?<![a-zA-Z0-9_])_\*\*(\w+)', lambda m: f'**{m.group(1)}'),
]

# Pattern 3: Underscore-prefixed typing module names
TYPING_FIXES = [
    # Core typing imports - using word boundaries carefully
    (r'\b_Any\b', 'Any'),
    (r'\b_Dict\b', 'Dict'),
    (r'\b_List\b', 'List'),
    (r'\b_Tuple\b', 'Tuple'),
    (r'\b_Set\b', 'Set'),
    (r'\b_Optional\b', 'Optional'),
    (r'\b_Union\b', 'Union'),
    (r'\b_Callable\b', 'Callable'),
    (r'\b_Type\b', 'Type'),
    (r'\b_None\b(?!\w)', 'None'),
    
    # Type aliases - must be careful not to match variable names like _str_value
    (r'(?<![a-zA-Z0-9_])_bool(?![a-zA-Z0-9_])', 'bool'),
    (r'(?<![a-zA-Z0-9_])_str(?![a-zA-Z0-9_])', 'str'),
    (r'(?<![a-zA-Z0-9_])_int(?![a-zA-Z0-9_])', 'int'),
    (r'(?<![a-zA-Z0-9_])_float(?![a-zA-Z0-9_])', 'float'),
    (r'(?<![a-zA-Z0-9_])_bytes(?![a-zA-Z0-9_])', 'bytes'),
    
    # Collections
    (r'\b_Mapping\b', 'Mapping'),
    (r'\b_Sequence\b', 'Sequence'),
    (r'\b_Iterable\b', 'Iterable'),
    (r'\b_Iterator\b', 'Iterator'),
    (r'\b_Generator\b', 'Generator'),
    (r'\b_AsyncGenerator\b', 'AsyncGenerator'),
    (r'\b_Coroutine\b', 'Coroutine'),
    (r'\b_Awaitable\b', 'Awaitable'),
    
    # Advanced typing
    (r'\b_Literal\b', 'Literal'),
    (r'\b_Annotated\b', 'Annotated'),
    (r'\b_Protocol\b', 'Protocol'),
    (r'\b_TypedDict\b', 'TypedDict'),
    (r'\b_NamedTuple\b', 'NamedTuple'),
    (r'\b_Generic\b', 'Generic'),
    (r'\b_TypeVar\b', 'TypeVar'),
    (r'\b_ParamSpec\b', 'ParamSpec'),
    (r'\b_Concatenate\b', 'Concatenate'),
    
    # Decorators
    (r'\b_overload\b', 'overload'),
    (r'\b_final\b', 'final'),
    (r'\b_runtime_checkable\b', 'runtime_checkable'),
    
    # Collections from typing
    (r'\b_AbstractSet\b', 'AbstractSet'),
    (r'\b_Counter\b', 'Counter'),
    (r'\b_DefaultDict\b', 'DefaultDict'),
    (r'\b_Deque\b', 'Deque'),
    (r'\b_FrozenSet\b', 'FrozenSet'),
    (r'\b_ChainMap\b', 'ChainMap'),
    (r'\b_OrderedDict\b', 'OrderedDict'),
    
    # IO types
    (r'\b_Pattern\b', 'Pattern'),
    (r'\b_Match\b', 'Match'),
    (r'\b_BinaryIO\b', 'BinaryIO'),
    (r'\b_TextIO\b', 'TextIO'),
    (r'\b_IO\b', 'IO'),
    
    # Domain-specific
    (r'\b_DomainEvent\b', 'DomainEvent'),
]


# =============================================================================
# LOGGING
# =============================================================================

class FixLogger:
    """Logger for tracking all fixes applied."""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.changes: List[str] = []
        self.stats = {
            'files_scanned': 0,
            'files_modified': 0,
            'files_failed': 0,
            'comment_fixes': 0,
            'args_kwargs_fixes': 0,
            'typing_fixes': 0,
            'total_fixes': 0,
        }
        self.errors: List[str] = []
        self.still_broken: List[str] = []
    
    def log_change(self, message: str):
        self.changes.append(message)
        self.stats['total_fixes'] += 1
    
    def log_error(self, message: str):
        self.errors.append(message)
    
    def log_still_broken(self, filepath: str, reason: str):
        self.still_broken.append(f"{filepath}: {reason}")
    
    def write_log(self):
        """Write the log file."""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("SYNTAX ERROR FIX LOG\n")
            f.write(f"Generated: {timestamp}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Files scanned:       {self.stats['files_scanned']}\n")
            f.write(f"Files modified:      {self.stats['files_modified']}\n")
            f.write(f"Files failed:        {self.stats['files_failed']}\n")
            f.write(f"Comment fixes:       {self.stats['comment_fixes']}\n")
            f.write(f"Args/kwargs fixes:   {self.stats['args_kwargs_fixes']}\n")
            f.write(f"Typing fixes:        {self.stats['typing_fixes']}\n")
            f.write(f"Total fixes:         {self.stats['total_fixes']}\n")
            f.write("\n")
            
            if self.changes:
                f.write("CHANGES APPLIED\n")
                f.write("-" * 40 + "\n")
                for change in self.changes:
                    f.write(f"{change}\n")
                f.write("\n")
            
            if self.errors:
                f.write("ERRORS\n")
                f.write("-" * 40 + "\n")
                for error in self.errors:
                    f.write(f"{error}\n")
                f.write("\n")
            
            if self.still_broken:
                f.write("FILES STILL WITH SYNTAX ERRORS\n")
                f.write("-" * 40 + "\n")
                for broken in self.still_broken:
                    f.write(f"{broken}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF LOG\n")
            f.write("=" * 80 + "\n")


# =============================================================================
# FIX FUNCTIONS
# =============================================================================

def fix_comment_patterns(content: str, logger: FixLogger, filepath: str) -> str:
    """Fix underscore-prefixed comments that break function signatures."""
    original = content
    
    pattern, replacement = COMMENT_PATTERN
    matches = list(re.finditer(pattern, content))
    if matches:
        content = re.sub(pattern, replacement, content)
        logger.stats['comment_fixes'] += len(matches)
        logger.log_change(f"[COMMENT] {filepath}: Fixed {len(matches)} underscore-prefixed comment(s)")
    
    return content


def fix_args_kwargs_patterns(content: str, logger: FixLogger, filepath: str) -> str:
    """Fix invalid _*args and _**kwargs patterns."""
    original = content
    fixes_applied = 0
    
    for pattern, replacement in ARGS_KWARGS_PATTERNS:
        matches = list(re.finditer(pattern, content))
        if matches:
            for match in matches:
                fixes_applied += 1
                logger.stats['args_kwargs_fixes'] += 1
            
            content = re.sub(pattern, replacement, content)
    
    if fixes_applied > 0:
        logger.log_change(f"[ARGS/KWARGS] {filepath}: Fixed {fixes_applied} args/kwargs pattern(s)")
    
    return content


def fix_typing_names(content: str, logger: FixLogger, filepath: str) -> str:
    """Fix underscore-prefixed typing module names."""
    original = content
    fixes_applied = 0
    
    for pattern, replacement in TYPING_FIXES:
        matches = list(re.finditer(pattern, content))
        if matches:
            for match in matches:
                fixes_applied += 1
                logger.stats['typing_fixes'] += 1
            
            content = re.sub(pattern, replacement, content)
    
    if fixes_applied > 0:
        logger.log_change(f"[TYPING] {filepath}: Fixed {fixes_applied} typing reference(s)")
    
    return content


def validate_python_syntax(content: str, filepath: str) -> Tuple[bool, Optional[str]]:
    """Validate that the content is valid Python syntax."""
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def create_backup(filepath: str, backup_dir: str) -> str:
    """Create a backup of the file."""
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(filepath)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
    
    shutil.copy2(filepath, backup_path)
    return backup_path


def scan_python_files(source_dir: str) -> List[str]:
    """Recursively scan for all Python files."""
    python_files = []
    
    for root, dirs, files in os.walk(source_dir):
        # Skip hidden directories and common non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return sorted(python_files)


def has_issues(content: str) -> bool:
    """Check if content has any patterns that need fixing."""
    # Check for comment issues
    if re.search(COMMENT_PATTERN[0], content):
        return True
    
    # Check for args/kwargs issues
    for pattern, _ in ARGS_KWARGS_PATTERNS:
        if re.search(pattern, content):
            return True
    
    # Check for typing issues
    for pattern, _ in TYPING_FIXES:
        if re.search(pattern, content):
            return True
    
    return False


def fix_file(filepath: str, logger: FixLogger, backup_dir: str) -> bool:
    """
    Fix a single Python file.
    
    Returns True if the file was successfully fixed, False otherwise.
    """
    try:
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Check if file has any issues first
        if not has_issues(original_content):
            # No issues found, skip this file
            return True
        
        content = original_content
        
        # Apply fixes in priority order
        
        # 1. Fix underscore-prefixed comments (these break function signatures)
        content = fix_comment_patterns(content, logger, filepath)
        
        # 2. Fix args/kwargs patterns (HIGHEST PRIORITY - syntax errors)
        content = fix_args_kwargs_patterns(content, logger, filepath)
        
        # 3. Fix typing names
        content = fix_typing_names(content, logger, filepath)
        
        # Validate the fixed content
        is_valid, error_msg = validate_python_syntax(content, filepath)
        
        if not is_valid:
            # Still has syntax errors
            logger.log_still_broken(filepath, error_msg)
            logger.stats['files_failed'] += 1
            return False
        
        # Content is valid - write it if changed
        if content != original_content:
            # Create backup
            backup_path = create_backup(filepath, backup_dir)
            logger.log_change(f"[BACKUP] {filepath} -> {backup_path}")
            
            # Write fixed content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.stats['files_modified'] += 1
            logger.log_change(f"[FIXED] {filepath}")
        
        return True
        
    except Exception as e:
        logger.log_error(f"[ERROR] {filepath}: {str(e)}")
        logger.stats['files_failed'] += 1
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("HERETEK SWARM SYNTAX ERROR FIXER")
    print("=" * 60)
    print()
    
    # Initialize logger
    logger = FixLogger(LOG_FILE)
    
    # Scan for Python files
    print(f"Scanning {SOURCE_DIR} for Python files...")
    python_files = scan_python_files(SOURCE_DIR)
    logger.stats['files_scanned'] = len(python_files)
    print(f"Found {len(python_files)} Python files")
    print()
    
    # Process each file
    print("Processing files...")
    successful = 0
    failed = 0
    
    for i, filepath in enumerate(python_files, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(python_files)} files...")
        
        if fix_file(filepath, logger, BACKUP_DIR):
            successful += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files scanned:     {logger.stats['files_scanned']}")
    print(f"Files modified:    {logger.stats['files_modified']}")
    print(f"Files successful:  {successful}")
    print(f"Files failed:      {failed}")
    print(f"Comment fixes:     {logger.stats['comment_fixes']}")
    print(f"Args/kwargs fixes: {logger.stats['args_kwargs_fixes']}")
    print(f"Typing fixes:      {logger.stats['typing_fixes']}")
    print(f"Total fixes:       {logger.stats['total_fixes']}")
    print()
    
    # Write log file
    logger.write_log()
    print(f"Log written to: {LOG_FILE}")
    print(f"Backups stored in: {BACKUP_DIR}/")
    print()
    
    if logger.still_broken:
        print("WARNING: The following files still have syntax errors:")
        for broken in logger.still_broken:
            print(f"  - {broken}")
        print()
    
    if logger.errors:
        print("ERRORS encountered:")
        for error in logger.errors:
            print(f"  - {error}")
        print()
    
    print("Done!")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
