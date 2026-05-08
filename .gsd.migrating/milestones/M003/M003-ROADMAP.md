# M003: Type-seal Mixin contracts and make stub injection first-class

**Vision:** Mixin methods fail fast when their dependencies are missing, and stubs are a first-class constructor argument rather than a monkey-patch escape hatch. Currently mixins like MemoryMixin silently no-op when access_analyzer is None — a runtime footgun. After this milestone, every mixin has mandatory dependency guards and the stub interface is the default testing path.

## Success Criteria

- Every mixin method raises TypeError when its dependency attribute is None
- All agent constructors accept stub overrides as keyword arguments
- Stub overrides work without monkey-patching
- pytest tests/test_auto_routing_integration.py passes with stubbed infra
- actors/mixins/__init__.py exports all mixins

## Slices

- [x] **S01: S01** `risk:low` `depends:[]`
  > After this: Bad()._validate_message({}) raises TypeError

- [x] **S02: S02** `risk:medium` `depends:[]`
  > After this: Agent(llm_provider=stub_llm) uses stub without monkey-patching

- [ ] **S03: S03** `risk:low` `depends:[]`
  > After this: from heretek_swarm.actors.mixins import AuditMixin, DeliberationMixin

## Boundary Map

Not provided.
