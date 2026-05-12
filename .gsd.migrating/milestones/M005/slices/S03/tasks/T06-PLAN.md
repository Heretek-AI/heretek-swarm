---
estimated_steps: 6
estimated_files: 1
skills_used: []
---

# T06: Final verification — full import check + test suite

Run comprehensive verification to confirm all changes work correctly and no regressions were introduced.

1. Import all 24 agents from actors.__init__.py
2. Run the full test suite
3. Verify _HISTORIAN_FILE is still importable from both the flat historian.py and the subpackage
4. Confirm no class definitions remain in any flat file

If tests fail, report the specific failure and suggest a fix but do NOT implement fixes — that belongs in a rework task or follow-up.

## Inputs

- None specified.

## Expected Output

- Update the implementation and proof artifacts needed for this task.

## Verification

python -c "from heretek_swarm.actors import AlphaAgent, BetaAgent, CharlieAgent, StewardAgent, ExplorerAgent, HistorianAgent, MetisAgent, EmpathAgent, EchoAgent, CoderAgent, CatalystAgent, PerceiverAgent, ArbiterAgent, ChronosAgent, CoordinatorAgent, DreamerAgent, ExaminerAgent, HabitForgeAgent, NexusAgent, PerceiverPlusAgent, PrismAgent, SentinelAgent, SentinelPrimeAgent, ActorSupervisor, ActorFactory, AgentActor; print(f'All {len([x for x in dir() if not x.startswith("_")])} agents import OK')" && cd heretek-swarm && python -m pytest tests/ -x -q --tb=short 2>&1 | tail -5
