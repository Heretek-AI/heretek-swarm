#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
print("Testing imports...")

try:
    from heretek_swarm.actors import *
    print("✅ Agents import OK")
except Exception as e:
    print(f"❌ Agents import FAILED: {e}")

try:
    from heretek_swarm.consciousness import iit_phi, fep_active_inference
    print("✅ Consciousness import OK")
except Exception as e:
    print(f"❌ Consciousness import FAILED: {e}")

try:
    from heretek_swarm.consensus import maker
    print("✅ MAKER consensus import OK")
except Exception as e:
    print(f"❌ MAKER import FAILED: {e}")

print("Done!")