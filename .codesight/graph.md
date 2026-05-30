# Dependency Graph

## Most Imported Files (change these carefully)

- `swarm-dashboard\src\components\UI\Toast.tsx` — imported by **15** files
- `/base.py` — imported by **13** files
- `swarm-dashboard\src\hooks\useWebSocket.ts` — imported by **11** files
- `/db_models.py` — imported by **10** files
- `swarm-dashboard\src\api\client.ts` — imported by **9** files
- `swarm-dashboard\src\components\UI\StatusBadge.tsx` — imported by **9** files
- `swarm-dashboard\src\components\UI\EmptyState.tsx` — imported by **8** files
- `/learning.py` — imported by **7** files
- `/result_types.py` — imported by **7** files
- `swarm-dashboard\src\components\UI\MetricCard.tsx` — imported by **6** files
- `swarm-dashboard\src\components\UI\LoadingSpinner.tsx` — imported by **6** files
- `swarm-dashboard\src\hooks\useConsciousnessWebSocket.ts` — imported by **6** files
- `swarm-dashboard\src\api\consciousness.ts` — imported by **6** files
- `/models.py` — imported by **5** files
- `swarm-dashboard\src\api\configuration.ts` — imported by **5** files
- `/emergent_detection_types.py` — imported by **4** files
- `swarm-dashboard\src\components\UI\ErrorBoundary.tsx` — imported by **4** files
- `swarm-dashboard\src\components\Agents\AgentCard.tsx` — imported by **4** files
- `swarm-dashboard\src\components\Observability\ExternalCallsPanel.tsx` — imported by **4** files
- `swarm-dashboard\src\components\Settings\DeveloperModeToggle.tsx` — imported by **4** files

## Import Map (who imports what)

- `swarm-dashboard\src\components\UI\Toast.tsx` ← `swarm-dashboard\src\api\client.ts`, `swarm-dashboard\src\App.tsx`, `swarm-dashboard\src\components\Agents\AgentsPage.tsx`, `swarm-dashboard\src\components\Consciousness\ConsciousnessPage.tsx`, `swarm-dashboard\src\components\Deliberation\HistoricalDeliberations.tsx` +10 more
- `/base.py` ← `backend\heretek_swarm\embeddings\providers\factory.py`, `backend\heretek_swarm\embeddings\providers\ollama_provider.py`, `backend\heretek_swarm\embeddings\providers\openai_provider.py`, `backend\heretek_swarm\embeddings\providers\__init__.py`, `backend\heretek_swarm\llm\providers\factory.py` +8 more
- `swarm-dashboard\src\hooks\useWebSocket.ts` ← `swarm-dashboard\src\components\Consciousness\RealTimeAgentPanel.tsx`, `swarm-dashboard\src\components\Logs\LogsPage.tsx`, `swarm-dashboard\src\components\Observability\ExternalCallsPanel.tsx`, `swarm-dashboard\src\hooks\useA2AMessages.ts`, `swarm-dashboard\src\hooks\useConsciousnessWebSocket.ts` +6 more
- `/db_models.py` ← `backend\heretek_swarm\config\crud.py`, `backend\heretek_swarm\config\crud.py`, `backend\heretek_swarm\config\crud.py`, `backend\heretek_swarm\config\crud.py`, `backend\heretek_swarm\config\crud.py` +5 more
- `swarm-dashboard\src\api\client.ts` ← `swarm-dashboard\src\api\configuration.ts`, `swarm-dashboard\src\api\consensus.ts`, `swarm-dashboard\src\api\deliberation.ts`, `swarm-dashboard\src\api\events.ts`, `swarm-dashboard\src\api\mcp.ts` +4 more
- `swarm-dashboard\src\components\UI\StatusBadge.tsx` ← `swarm-dashboard\src\components\Agents\AgentCard.tsx`, `swarm-dashboard\src\components\Agents\AgentControls.tsx`, `swarm-dashboard\src\components\Agents\AgentsPage.tsx`, `swarm-dashboard\src\components\Consciousness\ConsciousnessPage.tsx`, `swarm-dashboard\src\components\Dashboard\Layout.tsx` +4 more
- `swarm-dashboard\src\components\UI\EmptyState.tsx` ← `swarm-dashboard\src\components\Agents\AgentsPage.tsx`, `swarm-dashboard\src\components\Consciousness\ConsciousnessPage.tsx`, `swarm-dashboard\src\components\Deliberation\HistoricalDeliberations.tsx`, `swarm-dashboard\src\components\Deliberation\LiveDeliberationPanel.tsx`, `swarm-dashboard\src\components\Home\HomePage.tsx` +3 more
- `/learning.py` ← `backend\heretek_swarm\actors\mixins\__init__.py`, `backend\heretek_swarm\collective\adaptive_learning.py`, `backend\heretek_swarm\collective\agent_adaptation.py`, `backend\heretek_swarm\collective\distributed_learning.py`, `backend\heretek_swarm\collective\knowledge_transform.py` +2 more
- `/result_types.py` ← `backend\heretek_swarm\security\zero_trust\audit_logger.py`, `backend\heretek_swarm\security\zero_trust\context_validator.py`, `backend\heretek_swarm\security\zero_trust\external_validator.py`, `backend\heretek_swarm\security\zero_trust\input_validator.py`, `backend\heretek_swarm\security\zero_trust\orchestrator.py` +2 more
- `swarm-dashboard\src\components\UI\MetricCard.tsx` ← `swarm-dashboard\src\components\Agents\AgentsPage.tsx`, `swarm-dashboard\src\components\Consciousness\ConsciousnessPage.tsx`, `swarm-dashboard\src\components\Deliberation\LiveDeliberationPanel.tsx`, `swarm-dashboard\src\components\Home\HomePage.tsx`, `swarm-dashboard\src\components\UI\index.ts` +1 more
