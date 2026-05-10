---
estimated_steps: 9
estimated_files: 1
skills_used: []
---

# T01: Add protocol stub classes to stubs.py

Add 6 protocol stub classes to `heretek_swarm/actors/stubs.py` that implement the expected interfaces of the 6 injectable dependencies. Each class should accept and store constructor args but not require real infrastructure. 

Classes to add:
- StubAccessAnalyzer: minimal implementation of AccessPatternAnalyzer interface (record_access, get_profile, predict_agent_access methods)
- StubPatternExtractor: minimal PatternExtractor (analyze_message, extract_patterns methods with async support)
- StubTribunal: minimal Tribunal (create_case, submit_evidence, get_case, issue_ruling, get_precedents, find_similar_precedents)
- StubDeliberationEngine: minimal SwarmDeliberationEngine
- StubLLMProvider: basic LLM provider that returns canned responses
- StubEventMesh: minimal NATSEventMesh stand-in

Use `from __future__ import annotations` for TYPE_CHECKING imports of the real types. Use `# noqa` for unused imports only when justified. Keep stub methods' return values simple — return empty lists, None, or placeholder dicts. Add async versions where the real interface is async.

## Inputs

- `heretek_swarm/actors/stubs.py`

## Expected Output

- `heretek_swarm/actors/stubs.py`

## Verification

python -c "from heretek_swarm.actors.stubs import StubAccessAnalyzer, StubPatternExtractor, StubTribunal, StubDeliberationEngine, StubLLMProvider, StubEventMesh; print('OK')"
