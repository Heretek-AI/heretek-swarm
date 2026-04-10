@echo off
cd /d "%~dp0"
echo Running DeepSource Anti-Pattern Fixer...
python fix_antipatterns_v2.py > fix_output.txt 2>&1
type fix_output.txt
pause
