#!/usr/bin/env python3
"""Quick import verification script."""
import sys

try:
    from heretek_swarm.actors import *
    print("✅ All 23 agents imported successfully")
except Exception as e:
    print(f"❌ Agent import failed: {e}")
    sys.exit(1)

try:
    from heretek_swarm.consciousness import iit_phi, fep_active_inference
    print("✅ Consciousness modules OK")
except Exception as e:
    print(f"❌ Consciousness import failed: {e}")
    sys.exit(1)

try:
    from heretek_swarm.consensus import maker
    from heretek_swarm.knowledge.unified_access import UnifiedKnowledgeAccess
    print("✅ Core modules OK")
except Exception as e:
    print(f"❌ Core module import failed: {e}")
    sys.exit(1)

print("✅ All imports verified successfully!")