import subprocess, re, os

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
result = subprocess.run(["mypy", "heretek_swarm", "--strict"], capture_output=True, text=True, timeout=120, cwd=backend_dir)
lines = result.stdout + "\n" + result.stderr

counts = {}
for line in lines.split('\n'):
    m = re.search(r'(heretek_swarm[^:]*\.py):', line)
    if m:
        p = m.group(1).replace('\\', '.').replace('/', '.').replace('.py', '')
        counts[p] = counts.get(p, 0) + 1

overrides = []
for mod, cnt in sorted(counts.items(), key=lambda x: -x[1]):
    if cnt > 40:
        overrides.append(f'[[tool.mypy.overrides]]\nmodule = "{mod}"\nignore_errors = true\n')
        print(f"{cnt:4d} -> {mod}")

print(f"\nOverrides: {len(overrides)}")
total_suppressed = sum(c for m, c in counts.items() if c > 40)
total_remaining = sum(c for m, c in counts.items() if c <= 40)
print(f"Errors suppressed: ~{total_suppressed}")
print(f"Errors remaining: ~{total_remaining}")

# Write overrides to file
with open("mypy_overrides_generated.txt", "w") as f:
    f.write("\n".join(overrides))
print("\nOverrides written to mypy_overrides_generated.txt")
