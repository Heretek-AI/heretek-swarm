# Apply PYL-E1130 fixes to emergent_intelligence.py

# Read the file
with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\api\emergent_intelligence.py', 'r') as f:
    content = f.read()

# Fix: _siq_history[-history_limit:] -> _siq_history[-limit:]
content = content.replace('metrics._siq_history[-history_limit:]', 'metrics._siq_history[-limit:]')

# Add limit = int(history_limit) before each history list comprehension
content = content.replace(
    'if include_history:\n            result["history"] = [s.to_dict() for s in metrics._siq_history[-limit:]]',
    'if include_history:\n            limit = int(history_limit)\n            result["history"] = [s.to_dict() for s in metrics._siq_history[-limit:]]'
)

content = content.replace(
    'if include_history:\n            result["history"] = [e.to_dict() for e in metrics._efficiency_history[-limit:]]',
    'if include_history:\n            limit = int(history_limit)\n            result["history"] = [e.to_dict() for e in metrics._efficiency_history[-limit:]]'
)

content = content.replace(
    'if include_history:\n            result["history"] = [t.to_dict() for t in metrics._transfer_history[-limit:]]',
    'if include_history:\n            limit = int(history_limit)\n            result["history"] = [t.to_dict() for t in metrics._transfer_history[-limit:]]'
)

content = content.replace(
    'if include_history:\n            result["history"] = [e.to_dict() for e in metrics._emergence_history[-limit:]]',
    'if include_history:\n            limit = int(history_limit)\n            result["history"] = [e.to_dict() for e in metrics._emergence_history[-limit:]]'
)

# Write the file
with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\api\emergent_intelligence.py', 'w') as f:
    f.write(content)

print('PYL-E1130 fixes applied successfully!')
