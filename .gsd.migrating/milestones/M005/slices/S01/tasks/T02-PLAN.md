---
estimated_steps: 13
estimated_files: 1
skills_used: []
---

# T02: Create docs/actors/README.md with practical agent creation guide

Create a practical, example-driven guide at docs/actors/README.md that shows a new contributor how to add a custom agent.

Content structure:
1. Overview: explain the two conventions — flat actor files (alpha.py, beta.py, steward.py, etc.) vs subpackaged actors (actors/sentinel/, actors/triad/, etc.)
2. Architecture: how AgentActor (base), the 10 mixins, the ActorSupervisor, and the ActorFactory compose
3. Creating an agent: walkthrough code example showing:
   - Subclassing AgentActor with relevant mixins
   - Adding __init__.py re-exports in actors/__init__.py
   - Registering with ActorFactory
   - A minimal working example (e.g. a CustomQA agent)
4. Quick reference table: all 23 agents with tier, flat/subpackage status, file location, and mixins used
5. How to run agents locally (no-infra mode with `heretek-swarm run --no-infra --prompt "..." --target-agent alpha`)
6. How tests work and how to run them

Note: docs/actors/ directory already exists (contains EXTRACTION_PATTERN.md). Create README.md inside it.

## Inputs

- `heretek-swarm/heretek_swarm/actors/__init__.py`
- `heretek-swarm/heretek_swarm/actors/base/core.py`
- `heretek-swarm/heretek_swarm/actors/supervisor.py`
- `heretek-swarm/heretek_swarm/actors/factory.py`
- `heretek-swarm/heretek_swarm/actors/mixins/__init__.py`
- `heretek-swarm/docs/actors/EXTRACTION_PATTERN.md`
- `README.md`

## Expected Output

- `heretek-swarm/docs/actors/README.md`

## Verification

cd /Derek/Desktop/heretek-swarm && test -f docs/actors/README.md && grep -c '^## ' docs/actors/README.md && grep -q 'AgentActor' docs/actors/README.md && grep -q '__init__' docs/actors/README.md
