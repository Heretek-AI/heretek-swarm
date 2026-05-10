# S03: Add mixin __init__.py exports and smoke test for stub injection — UAT

**Milestone:** M003
**Written:** 2026-05-08T01:32:33.726Z

**Manual verification steps:**

1. `python -c "from heretek_swarm.actors.mixins import *; print(len([x for x in dir() if 'Mixin' in x]))"` — should print ≥10
2. `python -c "from heretek_swarm.actors import AlphaAgent; from heretek_swarm.actors.stubs import StubAccessAnalyzer; a = AlphaAgent(access_analyzer=StubAccessAnalyzer()); print('ok')"` — should print 'ok'
3. Run: `python -m pytest tests/test_mixin_integration_s03.py -v` — all 18 pass
