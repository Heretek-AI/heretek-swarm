import sys
sys.path.insert(0, 'src')

print("Testing imports...")

# Test 1: All 23 agents
from heretek_swarm.actors import *
print("✅ All 23 agents import OK")

# Test 2: Consciousness modules
from heretek_swarm.consciousness import iit_phi, fep_active_inference
print("✅ Consciousness modules OK")

# Test 3: Consensus
from heretek_swarm.consensus import maker
print("✅ Consensus module OK")

# Test 4: Knowledge
from heretek_swarm.knowledge.unified_access import UnifiedKnowledgeAccess
print("✅ Knowledge access OK")

print("\n✅ All critical imports verified!")