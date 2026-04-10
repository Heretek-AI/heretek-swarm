#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from heretek_swarm.tools.base import ToolMetadata
print("ToolMetadata fields:")
for name, field in ToolMetadata.model_fields.items():
    if 'timeout' in name.lower():
        print(f"  {name}: {field}")

# Test validation
try:
    _tm = ToolMetadata(name="test", timeout_seconds=0.1)
    print(f"❌ 0.1 should fail but created: {tm}")
except Exception as e:
    print(f"✅ 0.1 correctly rejected: {type(e).__name__}")

try:
    _tm = ToolMetadata(name="test", timeout_seconds=1.0)
    print(f"✅ 1.0 accepted: {tm.timeout_seconds}")
except Exception as e:
    print(f"❌ 1.0 rejected: {e}")