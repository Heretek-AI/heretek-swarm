import sys
sys.path.insert(0, ".")
import traceback

tests = [
    ("sentinel agent", "from heretek_swarm.actors.sentinel.agent import SentinelAgent"),
    ("sentinel safety", "from heretek_swarm.actors.sentinel.safety import scan_content"),
    ("sentinel anomaly", "from heretek_swarm.actors.sentinel.anomaly import AnomalyMonitor"),
    ("sentinel immune", "from heretek_swarm.actors.sentinel.immune import ImmuneResponseManager"),
    ("api observability router", "from heretek_swarm.api.observability import router"),
    ("cli module", "from heretek_swarm.cli import cli"),
    ("workflow models", "from heretek_swarm.workflow.models import SafeExpressionEvaluator, Workflow, WorkflowEngine"),
    ("workflow engine", "from heretek_swarm.workflow.engine import WorkflowEngine"),
    ("runtime main_loop", "from heretek_swarm.runtime.main_loop import AutonomousSwarm"),
]

passed = 0
failed = 0
for label, code in tests:
    try:
        exec(code)
        print(f"OK: {label}")
        passed += 1
    except Exception as e:
        print(f"FAIL: {label} - {e}")
        traceback.print_exc()
        failed += 1

print(f"\n{passed} passed, {failed} failed")
print(f"Overall: {'PASS' if failed == 0 else 'FAIL'}")
