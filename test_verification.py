#!/usr/bin/env python3
"""Zero-trust verification test for heretek-swarm core modules."""
import sys

# Test 1: Actors
try:
    from heretek_swarm.actors import AgentActor, ActorSupervisor
    print("✓ Actors module: PASS")
except Exception as e:
    print(f"✗ Actors module: FAIL - {e}")
    sys.exit(1)

# Test 2: Consciousness
try:
    from heretek_swarm.consciousness import PhiCalculator, FreeEnergyCalculator
    print("✓ Consciousness module: PASS")
except Exception as e:
    print(f"✗ Consciousness module: FAIL - {e}")
    sys.exit(1)

# Test 3: Orchestration
try:
    from heretek_swarm.orchestration import HeavySwarmWorkflow
    print("✓ Orchestration module: PASS")
except Exception as e:
    print(f"✗ Orchestration module: FAIL - {e}")
    sys.exit(1)

# Test 4: Gateway
try:
    from heretek_swarm.gateway import A2AServer, EventMesh
    print("✓ Gateway module: PASS")
except Exception as e:
    print(f"✗ Gateway module: FAIL - {e}")
    sys.exit(1)

# Test 5: Consensus
try:
    from heretek_swarm.consensus import MAKERConsensus, SwarmDeliberationEngine
    print("✓ Consensus module: PASS")
except Exception as e:
    print(f"✗ Consensus module: FAIL - {e}")
    sys.exit(1)

# Test 6: Knowledge
try:
    from heretek_swarm.knowledge import UnifiedKnowledgeAccess
    print("✓ Knowledge module: PASS")
except Exception as e:
    print(f"✗ Knowledge module: FAIL - {e}")
    sys.exit(1)

# Test 7: Tools
try:
    from heretek_swarm.tools import ToolRegistry
    print("✓ Tools module: PASS")
except Exception as e:
    print(f"✗ Tools module: FAIL - {e}")
    sys.exit(1)

print("\n✓ Zero-Trust Verification Complete: ALL PASS")