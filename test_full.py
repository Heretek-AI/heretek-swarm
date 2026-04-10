#!/usr/bin/env python3
"""Full module verification"""
import sys
sys.path.insert(0, 'src')

results = []

# Test each module
tests = [
    ("Actors", "from heretek_swarm.actors import AgentActor"),
    ("Consciousness IIT", "from heretek_swarm.consciousness.iit_phi import PhiCalculator"),
    ("Consciousness FEP", "from heretek_swarm.consciousness.fep_active_inference import FreeEnergyCalculator"),
    ("Consensus Maker", "from heretek_swarm.consensus.maker import MAKERConsensus"),
    ("Consensus Deliberation", "from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine"),
    ("Knowledge", "from heretek_swarm.knowledge import UnifiedKnowledgeAccess"),
    ("Gateway", "from heretek_swarm.gateway import A2AServer"),
    ("NATS", "from heretek_swarm.gateway.nats_event_mesh import NATSEventMesh"),
    ("Orchestration", "from heretek_swarm.orchestration import HeavySwarmWorkflow"),
    ("Tools", "from heretek_swarm.tools.registry import ToolRegistry"),
    ("Memory", "from heretek_swarm.memory import MemoryManager"),
]

for name, import_stmt in tests:
    try:
        exec(import_stmt)
        results.append((name, "OK"))
    except Exception as e:
        results.append((name, str(e)))

print("=" * 60)
for name, status in results:
    ok = "OK" if status == "OK" else "FAIL"
    print(f"{name}: {ok}")
print("=" * 60)
print(f"Total: {sum(1 for _, s in results if s == 'OK')}/{len(results)}")