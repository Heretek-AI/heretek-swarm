#!/usr/bin/env python3
"""
AST-based Python script to fix PYL-E0602 errors caused by incorrect underscore prefixing of function parameters.

This script analyzes Python source files using the ast module to:
1. Detect constructor parameters assigned to self
2. Detect abstract method parameters
3. Detect parameters used in function body
4. Remove underscore prefix when parameter IS used
5. Keep underscore prefix only for truly unused parameters

The script processes all .py files in src/heretek_swarm/ directory recursively.
"""

import ast
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ParameterFix:
    """Information about a parameter fix."""
    function_name: str
    old_name: str
    new_name: str
    line_number: int
    reason: str


@dataclass
class FileAnalysisResult:
    """Result of analyzing a single file."""
    filepath: Path
    functions_analyzed: int = 0
    parameters_fixed: int = 0
    fixes: List[ParameterFix] = field(default_factory=list)
    error: Optional[str] = None


def get_all_names_in_body(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> Set[str]:
    """Get all Name identifiers used in a function body."""
    names: Set[str] = set()
    
    class NameCollector(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            names.add(node.id)
            self.generic_visit(node)
    
    for stmt in func_node.body:
        NameCollector().visit(stmt)
    
    return names


def is_abstract_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Check if a method has @abstractmethod decorator."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == 'abstractmethod':
            return True
    return False


def analyze_function_for_fixes(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[ParameterFix]:
    """Analyze a function and return list of parameter fixes needed."""
    fixes: List[ParameterFix] = []
    
    func_name = func_node.name
    is_method = len(func_node.args.args) > 0 and func_node.args.args[0].arg in ('self', 'cls')
    is_constructor = func_name == '__init__'
    is_abstract = is_abstract_method(func_node)
    
    # Collect all parameter names
    all_param_names: Set[str] = set()
    
    # Regular args
    for arg in func_node.args.args:
        if arg.arg not in ('self', 'cls'):
            all_param_names.add(arg.arg)
    
    # *args, **kwargs
    if func_node.args.vararg:
        all_param_names.add(func_node.args.vararg.arg)
    if func_node.args.kwarg:
        all_param_names.add(func_node.args.kwarg.arg)
    
    # Keyword-only args
    for arg in func_node.args.kwonlyargs:
        all_param_names.add(arg.arg)
    
    # Check for self.param = param assignments in constructor
    params_assigned_to_self: Set[str] = set()
    if is_constructor:
        for stmt in func_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                        if isinstance(stmt.value, ast.Name) and stmt.value.id in all_param_names:
                            params_assigned_to_self.add(stmt.value.id)
    
    # Get all names used in function body
    used_names = get_all_names_in_body(func_node)
    
    # Check each parameter
    all_args = list(func_node.args.args)
    if func_node.args.vararg:
        all_args.append(func_node.args.vararg)
    if func_node.args.kwarg:
        all_args.append(func_node.args.kwarg)
    all_args.extend(func_node.args.kwonlyargs)
    
    for arg in all_args:
        param_name = arg.arg
        
        # Skip self, cls, *args, **kwargs
        if param_name in ('self', 'cls'):
            continue
        
        # Check if has underscore prefix (but not dunder)
        has_underscore = param_name.startswith('_') and not param_name.startswith('__')
        if not has_underscore:
            continue
        
        # Determine if we should remove the underscore
        should_fix = False
        reason = ""
        
        # Abstract methods: remove underscore from all params
        if is_abstract:
            should_fix = True
            reason = "abstract method parameter"
        # Constructor params assigned to self: remove underscore
        elif param_name in params_assigned_to_self or param_name[1:] in params_assigned_to_self:
            should_fix = True
            reason = "constructor parameter assigned to self"
        # Parameter is used in body (referenced without underscore): remove underscore
        elif param_name[1:] in used_names:
            should_fix = True
            reason = "parameter used in function body (referenced without underscore)"
        
        if should_fix:
            fixes.append(ParameterFix(
                function_name=func_name,
                old_name=param_name,
                new_name=param_name[1:],
                line_number=func_node.lineno,
                reason=reason
            ))
    
    return fixes


def analyze_file(filepath: Path) -> Tuple[ast.AST, List[ParameterFix], Optional[str]]:
    """Analyze a Python file and return AST and fixes needed."""
    try:
        content = filepath.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(filepath))
        
        all_fixes: List[ParameterFix] = []
        function_count = 0
        
        class FunctionVisitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                nonlocal function_count
                function_count += 1
                fixes = analyze_function_for_fixes(node)
                all_fixes.extend(fixes)
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                nonlocal function_count
                function_count += 1
                fixes = analyze_function_for_fixes(node)
                all_fixes.extend(fixes)
                self.generic_visit(node)
        
        FunctionVisitor().visit(tree)
        
        return tree, all_fixes, None
    
    except SyntaxError as e:
        return None, [], f"Syntax error: {e}"
    except Exception as e:
        return None, [], f"Error: {e}"


def fix_file_with_text_replacement(filepath: Path, fixes: List[ParameterFix], create_backup: bool = True) -> FileAnalysisResult:
    """
    Fix underscore prefix issues using text replacement.
    
    This approach is more reliable than ast.unparse() for files that have
    already been corrupted with incorrect underscore prefixes.
    """
    result = FileAnalysisResult(filepath=filepath)
    result.fixes = fixes
    result.parameters_fixed = len(fixes)
    
    if not fixes:
        return result
    
    # Create backup
    if create_backup:
        backup_path = filepath.with_suffix(filepath.suffix + '.bak')
        shutil.copy2(filepath, backup_path)
    
    content = filepath.read_text(encoding='utf-8')
    
    # Group fixes by parameter name to avoid conflicts
    param_fixes: Dict[str, ParameterFix] = {}
    for fix in fixes:
        if fix.old_name not in param_fixes:
            param_fixes[fix.old_name] = fix
    
    # For each fix, we need to:
    # 1. Update the parameter definition
    # 2. Update all references to the new name in the function body
    
    # Build a mapping of function line ranges
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # File already has syntax errors - we need to fix parameter definitions first
        # Then the references will work
        pass
    
    # Process fixes - replace parameter definitions and their usages
    for fix in fixes:
        # Pattern 1: Replace parameter definition in function signature
        # Match: def func(..., _param: Type, ...) or def func(..., _param=default, ...)
        param_pattern = rf'(\bdef\s+\w+\s*\([^)]*){re.escape(fix.old_name)}'
        
        def replace_param_def(match):
            return match.group(1) + fix.new_name
        
        content = re.sub(param_pattern, replace_param_def, content)
        
        # Pattern 2: Replace usages of the parameter in function body
        # We need to be careful to only replace within the function scope
        # For now, we'll replace all bare references (not preceded by underscore)
        # that are not part of another identifier
        usage_pattern = rf'(?<!_)\b{re.escape(fix.new_name)}\b'
        
        # This is tricky - we need to only replace within the function
        # For simplicity, we'll do a global replace of the bare name
        # This works because the old _param is still there for other functions
        content = re.sub(usage_pattern, fix.new_name, content)
    
    # Write the fixed content
    filepath.write_text(content, encoding='utf-8')
    
    return result


def fix_file_proper(filepath: Path, fixes: List[ParameterFix], create_backup: bool = True) -> FileAnalysisResult:
    """
    Fix underscore prefix issues using proper AST-based text manipulation.
    
    This approach:
    1. Finds each function that needs fixes
    2. Replaces parameter definitions
    3. Replaces parameter usages within that function's scope
    """
    result = FileAnalysisResult(filepath=filepath)
    result.fixes = fixes
    result.parameters_fixed = len(fixes)
    
    if not fixes:
        return result
    
    # Create backup
    if create_backup:
        backup_path = filepath.with_suffix(filepath.suffix + '.bak')
        shutil.copy2(filepath, backup_path)
    
    content = filepath.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=True)
    
    # Group fixes by function and line number
    fixes_by_line: Dict[int, List[ParameterFix]] = {}
    for fix in fixes:
        if fix.line_number not in fixes_by_line:
            fixes_by_line[fix.line_number] = []
        fixes_by_line[fix.line_number].append(fix)
    
    # Process each function that needs fixes
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        # File has syntax errors - try to fix parameter definitions at least
        result.error = f"Syntax error in file: {e}"
        # Still try to fix parameter definitions
        for line_num, func_fixes in fixes_by_line.items():
            if line_num <= len(lines):
                line = lines[line_num - 1]
                for fix in func_fixes:
                    # Replace parameter definition
                    pattern = rf'(\bdef\s+\w+\s*\([^)]*){re.escape(fix.old_name)}'
                    new_line = re.sub(pattern, lambda m: m.group(1) + fix.new_name, line)
                    if new_line != line:
                        lines[line_num - 1] = new_line
                        line = new_line
        
        content = ''.join(lines)
        filepath.write_text(content, encoding='utf-8')
        return result
    
    # Build line ranges for each function
    function_ranges: Dict[str, Tuple[int, int]] = {}  # func_name -> (start_line, end_line)
    
    class FunctionRangeVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            function_ranges[node.name] = (node.lineno, node.end_lineno or node.lineno)
            self.generic_visit(node)
        
        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            function_ranges[node.name] = (node.lineno, node.end_lineno or node.lineno)
            self.generic_visit(node)
    
    FunctionRangeVisitor().visit(tree)
    
    # Apply fixes
    modified_lines = set()
    
    for line_num, func_fixes in fixes_by_line.items():
        if line_num <= len(lines):
            line = lines[line_num - 1]
            original_line = line
            
            # Find the function name from the line
            func_match = re.search(r'\bdef\s+(\w+)', line)
            func_name = func_match.group(1) if func_match else None
            
            # Get function end line
            func_end = line_num
            if func_name and func_name in function_ranges:
                func_end = function_ranges[func_name][1]
            
            # Replace parameter definitions in the function signature line
            for fix in func_fixes:
                # Replace parameter definition - handle various formats
                # def func(_param), def func(_param: Type), def func(_param=default)
                patterns = [
                    rf'(\(\s*){re.escape(fix.old_name)}(\s*[:\),=])',  # First param
                    rf'(,\s*){re.escape(fix.old_name)}(\s*[:\),=])',  # Subsequent param
                ]
                
                for pattern in patterns:
                    new_line = re.sub(pattern, lambda m: m.group(1) + fix.new_name + m.group(2), line)
                    if new_line != line:
                        line = new_line
            
            if line != original_line:
                lines[line_num - 1] = line
                modified_lines.add(line_num)
            
            # Now replace parameter usages in the function body
            for fix in func_fixes:
                for body_line_num in range(line_num, min(func_end + 1, len(lines) + 1)):
                    if body_line_num == line_num:
                        continue  # Skip the def line itself
                    if body_line_num in modified_lines and body_line_num == line_num:
                        continue
                    
                    body_line = lines[body_line_num - 1]
                    # Replace bare references to the new name (which was incorrectly used)
                    # The pattern (?<!_) ensures we don't match _param
                    # We're looking for uses of 'param' that should stay as 'param'
                    # after we change '_param' to 'param'
                    
                    # Actually, we need to find where the code uses the NEW name (without underscore)
                    # and those should remain. The issue is the parameter DEFINITION has underscore
                    # but the body uses it without underscore.
                    
                    # After fixing the definition from _param to param, 
                    # the body references to 'param' are now correct.
                    # No further changes needed to the body!
    
    content = ''.join(lines)
    filepath.write_text(content, encoding='utf-8')
    
    return result


def find_python_files(directory: Path, recursive: bool = True) -> List[Path]:
    """Find all Python files in a directory."""
    files = []
    skip_dirs = {'.pytest_cache', 'node_modules', '__pycache__', '.git', '.venv', 'venv', '.actor_states'}
    
    if recursive:
        for path in directory.rglob('*.py'):
            if not any(skip_dir in path.parts for skip_dir in skip_dirs):
                if 'test' not in path.parts:  # Skip test files
                    files.append(path)
    else:
        for path in directory.glob('*.py'):
            if not any(skip_dir in path.parts for skip_dir in skip_dirs):
                files.append(path)
    
    return files


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix PYL-E0602 errors caused by incorrect underscore prefixing of function parameters.'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='src/heretek_swarm',
        help='Directory to process (default: src/heretek_swarm)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Do not create backup files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze only, do not modify files'
    )
    parser.add_argument(
        '--log-file',
        default='underscore_fix_log.txt',
        help='Log file path (default: underscore_fix_log.txt)'
    )
    
    args = parser.parse_args()
    
    src_dir = Path(args.directory)
    if not src_dir.exists():
        print(f"Error: Directory '{src_dir}' does not exist.")
        sys.exit(1)
    
    print(f"Scanning for Python files in {src_dir}...")
    python_files = find_python_files(src_dir)
    print(f"Found {len(python_files)} Python files to process.\n")
    
    # Process files
    total_files = 0
    total_functions = 0
    total_params_fixed = 0
    files_with_fixes = 0
    files_with_errors = 0
    files_skipped_syntax_error = 0
    
    log_lines = [
        "=" * 80,
        "Underscore Prefix Fix Log",
        f"Generated: {datetime.now().isoformat()}",
        f"Target Directory: {src_dir.absolute()}",
        "=" * 80,
        ""
    ]
    
    for filepath in python_files:
        total_files += 1
        
        tree, fixes, error = analyze_file(filepath)
        
        if error:
            files_with_errors += 1
            files_skipped_syntax_error += 1
            log_lines.append(f"\n[ERROR] {filepath}: {error}")
            continue
        
        total_functions += len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
        
        if not fixes:
            continue
        
        # This file has fixes to apply
        files_with_fixes += 1
        total_params_fixed += len(fixes)
        
        if args.dry_run:
            log_lines.append(f"\n[DRY RUN] {filepath}")
            log_lines.append(f"  Parameters to fix: {len(fixes)}")
            for fix in fixes:
                log_lines.append(f"  - {fix.function_name}.{fix.old_name} -> {fix.new_name} ({fix.reason}, line {fix.line_number})")
        else:
            result = fix_file_proper(filepath, fixes, create_backup=not args.no_backup)
            log_lines.append(f"\n[FIXED] {filepath}")
            log_lines.append(f"  Parameters fixed: {result.parameters_fixed}")
            for fix in result.fixes:
                log_lines.append(f"  - {fix.function_name}.{fix.old_name} -> {fix.new_name} ({fix.reason}, line {fix.line_number})")
            if result.error:
                log_lines.append(f"  Warning: {result.error}")
    
    # Write log file
    log_lines.append("\n" + "=" * 80)
    log_lines.append("SUMMARY")
    log_lines.append("=" * 80)
    log_lines.append(f"Files processed: {total_files}")
    log_lines.append(f"Functions analyzed: {total_functions}")
    log_lines.append(f"Files with fixes: {files_with_fixes}")
    log_lines.append(f"Total parameters fixed: {total_params_fixed}")
    log_lines.append(f"Files with errors (skipped): {files_with_errors}")
    log_lines.append(f"Files skipped due to syntax errors: {files_skipped_syntax_error}")
    log_lines.append("=" * 80)
    
    log_content = '\n'.join(log_lines)
    
    with open(args.log_file, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    # Print summary
    print("\n" + "=" * 60)
    print("UNDERSCORE PREFIX FIX SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_files}")
    print(f"Functions analyzed: {total_functions}")
    print(f"Files with fixes: {files_with_fixes}")
    print(f"Total parameters fixed: {total_params_fixed}")
    print(f"Files with errors (skipped): {files_with_errors}")
    print("=" * 60)
    print(f"\nLog file: {args.log_file}")
    
    if args.dry_run:
        print("\n[DRY RUN] No files were modified.")
        print("Run without --dry-run to apply fixes.")


if __name__ == '__main__':
    main()
