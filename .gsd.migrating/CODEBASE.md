# Codebase Map

Generated: 2026-04-29T14:05:54Z | Files: 500 | Described: 0/500
<!-- gsd:codebase-meta {"generatedAt":"2026-04-29T14:05:54Z","fingerprint":"0e6a5b96a84273e627596de5aca81b53a6aa2503","fileCount":500,"truncated":true} -->
Note: Truncated to first 500 files. Run with higher --max-files to include all.

### (root)/
- *(21 files: 9 .md, 3 .json, 3 (no ext), 2 .0, 1 .example, 1 .yaml, 1 .yml, 1 .toml)*

### .codeboarding/
- `.codeboarding/.codeboardingignore`
- `.codeboarding/analysis_manifest.json`
- `.codeboarding/analysis.json`
- `.codeboarding/codeboarding_version.json`
- `.codeboarding/file_coverage.json`

### .codeboarding/cache/
- `.codeboarding/cache/cluster_analysis_llm.sqlite-shm`
- `.codeboarding/cache/cluster_analysis_llm.sqlite-wal`
- `.codeboarding/cache/final_analysis_llm.sqlite-shm`
- `.codeboarding/cache/final_analysis_llm.sqlite-wal`
- `.codeboarding/cache/meta_agent_llm.sqlite-shm`
- `.codeboarding/cache/meta_agent_llm.sqlite-wal`
- `.codeboarding/cache/static_analysis_results.pkl`

### .codeboarding/health/
- `.codeboarding/health/.healthignore`
- `.codeboarding/health/health_config.json`
- `.codeboarding/health/health_report.json`

### .github/workflows/
- `.github/workflows/ci-cd.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/codeboarding.yml`
- `.github/workflows/load-test.yml`
- `.github/workflows/publish-npm.yml`
- `.github/workflows/publish-python.yml`

### audit/
- `audit/cli.py`

### docs/
- `docs/AGENT_ARCHITECTURE.md`
- `docs/AGENT_REFERENCE.md`
- `docs/AGENTS.md`
- `docs/API_ENDPOINTS.md`
- `docs/API_REFERENCE.md`
- `docs/ARCHITECTURE.md`
- `docs/AUTONOMOUS_WORKFLOW.md`
- `docs/BETA_AGENT_README.md`
- `docs/CODEBASE_AUDIT.md`
- `docs/CORE_ACTORS.md`
- `docs/DEPLOYMENT.md`
- `docs/INDEX.md`
- `docs/MAIN_PROMPT.md`
- `docs/MEMORY_SYSTEM.md`
- `docs/MONITORING.md`
- `docs/PROMETHEUS_METRICS.md`
- `docs/PROTOCOL_SPEC.md`

### docs/architecture/
- `docs/architecture/actors-system.md`
- `docs/architecture/ARCHITECTURE_REALITY.md`
- `docs/architecture/collective-learning.md`
- `docs/architecture/consensus-mechanism.md`
- `docs/architecture/emergent-intelligence.md`
- `docs/architecture/EXTERNAL_PATTERNS_ANALYSIS.md`
- `docs/architecture/memory-system.md`
- `docs/architecture/observability.md`
- `docs/architecture/orchestration-system.md`
- `docs/architecture/plugins.md`
- `docs/architecture/state-management.md`
- `docs/architecture/tools-system.md`

### heretek-swarm/agent_workspace/
- `heretek-swarm/agent_workspace/error.txt`

### heretek-swarm/heretek_swarm/
- `heretek-swarm/heretek_swarm/__init__.py`
- `heretek-swarm/heretek_swarm/__main__.py`
- `heretek-swarm/heretek_swarm/cli.py`

### heretek-swarm/heretek_swarm/actors/
- *(31 files: 31 .py)*

### heretek-swarm/heretek_swarm/actors/arbiter/
- `heretek-swarm/heretek_swarm/actors/arbiter/__init__.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/constants.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/core.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/handlers.py`
- `heretek-swarm/heretek_swarm/actors/arbiter/strategies.py`

### heretek-swarm/heretek_swarm/actors/base/
- `heretek-swarm/heretek_swarm/actors/base/__init__.py`
- `heretek-swarm/heretek_swarm/actors/base/core.py`
- `heretek-swarm/heretek_swarm/actors/base/message_handling.py`
- `heretek-swarm/heretek_swarm/actors/base/state_management.py`

### heretek-swarm/heretek_swarm/actors/chronos/
- `heretek-swarm/heretek_swarm/actors/chronos/__init__.py`
- `heretek-swarm/heretek_swarm/actors/chronos/agent.py`
- `heretek-swarm/heretek_swarm/actors/chronos/handlers.py`
- `heretek-swarm/heretek_swarm/actors/chronos/scheduler.py`
- `heretek-swarm/heretek_swarm/actors/chronos/types.py`

### heretek-swarm/heretek_swarm/actors/coordinator/
- `heretek-swarm/heretek_swarm/actors/coordinator/__init__.py`
- `heretek-swarm/heretek_swarm/actors/coordinator/agent.py`
- `heretek-swarm/heretek_swarm/actors/coordinator/strategies.py`
- `heretek-swarm/heretek_swarm/actors/coordinator/types.py`

### heretek-swarm/heretek_swarm/actors/docs/
- `heretek-swarm/heretek_swarm/actors/docs/EXTRACTION_PATTERN.md`

### heretek-swarm/heretek_swarm/actors/dreamer/
- `heretek-swarm/heretek_swarm/actors/dreamer/__init__.py`
- `heretek-swarm/heretek_swarm/actors/dreamer/agent.py`
- `heretek-swarm/heretek_swarm/actors/dreamer/generators.py`
- `heretek-swarm/heretek_swarm/actors/dreamer/types.py`

### heretek-swarm/heretek_swarm/actors/examiner/
- `heretek-swarm/heretek_swarm/actors/examiner/__init__.py`
- `heretek-swarm/heretek_swarm/actors/examiner/agent.py`
- `heretek-swarm/heretek_swarm/actors/examiner/testing.py`
- `heretek-swarm/heretek_swarm/actors/examiner/types.py`

### heretek-swarm/heretek_swarm/actors/explorer/
- `heretek-swarm/heretek_swarm/actors/explorer/__init__.py`
- `heretek-swarm/heretek_swarm/actors/explorer/agent.py`
- `heretek-swarm/heretek_swarm/actors/explorer/pathfinding.py`
- `heretek-swarm/heretek_swarm/actors/explorer/types.py`

### heretek-swarm/heretek_swarm/actors/habit_forge/
- `heretek-swarm/heretek_swarm/actors/habit_forge/__init__.py`
- `heretek-swarm/heretek_swarm/actors/habit_forge/agent.py`
- `heretek-swarm/heretek_swarm/actors/habit_forge/streaks.py`
- `heretek-swarm/heretek_swarm/actors/habit_forge/tracking.py`
- `heretek-swarm/heretek_swarm/actors/habit_forge/types.py`

### heretek-swarm/heretek_swarm/actors/mixins/
- `heretek-swarm/heretek_swarm/actors/mixins/__init__.py`
- `heretek-swarm/heretek_swarm/actors/mixins/audit.py`
- `heretek-swarm/heretek_swarm/actors/mixins/deliberation.py`
- `heretek-swarm/heretek_swarm/actors/mixins/health_reporting.py`
- `heretek-swarm/heretek_swarm/actors/mixins/learning.py`
- `heretek-swarm/heretek_swarm/actors/mixins/memory_access.py`
- `heretek-swarm/heretek_swarm/actors/mixins/memory.py`
- `heretek-swarm/heretek_swarm/actors/mixins/pattern_consumer.py`
- `heretek-swarm/heretek_swarm/actors/mixins/pattern.py`
- `heretek-swarm/heretek_swarm/actors/mixins/tribunal.py`
- `heretek-swarm/heretek_swarm/actors/mixins/validation.py`

### heretek-swarm/heretek_swarm/actors/nexus/
- `heretek-swarm/heretek_swarm/actors/nexus/__init__.py`
- `heretek-swarm/heretek_swarm/actors/nexus/agent.py`
- `heretek-swarm/heretek_swarm/actors/nexus/routing.py`
- `heretek-swarm/heretek_swarm/actors/nexus/types.py`

### heretek-swarm/heretek_swarm/actors/perceiver_plus/
- `heretek-swarm/heretek_swarm/actors/perceiver_plus/__init__.py`
- `heretek-swarm/heretek_swarm/actors/perceiver_plus/agent.py`
- `heretek-swarm/heretek_swarm/actors/perceiver_plus/analytics.py`
- `heretek-swarm/heretek_swarm/actors/perceiver_plus/types.py`

### heretek-swarm/heretek_swarm/actors/prism/
- `heretek-swarm/heretek_swarm/actors/prism/__init__.py`
- `heretek-swarm/heretek_swarm/actors/prism/agent.py`
- `heretek-swarm/heretek_swarm/actors/prism/transforms.py`
- `heretek-swarm/heretek_swarm/actors/prism/types.py`

### heretek-swarm/heretek_swarm/actors/sentinel/
- `heretek-swarm/heretek_swarm/actors/sentinel/__init__.py`
- `heretek-swarm/heretek_swarm/actors/sentinel/agent.py`
- `heretek-swarm/heretek_swarm/actors/sentinel/helpers.py`
- `heretek-swarm/heretek_swarm/actors/sentinel/types.py`

### heretek-swarm/heretek_swarm/actors/sentinel_prime/
- `heretek-swarm/heretek_swarm/actors/sentinel_prime/__init__.py`
- `heretek-swarm/heretek_swarm/actors/sentinel_prime/agent.py`
- `heretek-swarm/heretek_swarm/actors/sentinel_prime/handlers.py`
- `heretek-swarm/heretek_swarm/actors/sentinel_prime/helpers.py`
- `heretek-swarm/heretek_swarm/actors/sentinel_prime/types.py`

### heretek-swarm/heretek_swarm/actors/triad/
- `heretek-swarm/heretek_swarm/actors/triad/__init__.py`
- `heretek-swarm/heretek_swarm/actors/triad/agent.py`
- `heretek-swarm/heretek_swarm/actors/triad/balancing.py`
- `heretek-swarm/heretek_swarm/actors/triad/types.py`

### heretek-swarm/heretek_swarm/agent_workspace/
- `heretek-swarm/heretek_swarm/agent_workspace/error.txt`

### heretek-swarm/heretek_swarm/agents/
- `heretek-swarm/heretek_swarm/agents/__init__.py`
- `heretek-swarm/heretek_swarm/agents/skills.py`

### heretek-swarm/heretek_swarm/api/
- *(25 files: 25 .py)*

### heretek-swarm/heretek_swarm/api/agents/
- `heretek-swarm/heretek_swarm/api/agents/__init__.py`
- `heretek-swarm/heretek_swarm/api/agents/chat.py`
- `heretek-swarm/heretek_swarm/api/agents/core.py`
- `heretek-swarm/heretek_swarm/api/agents/instances.py`
- `heretek-swarm/heretek_swarm/api/agents/jetstream.py`
- `heretek-swarm/heretek_swarm/api/agents/lifecycle.py`
- `heretek-swarm/heretek_swarm/api/agents/profiling.py`
- `heretek-swarm/heretek_swarm/api/agents/routing_control.py`
- `heretek-swarm/heretek_swarm/api/agents/routing_rules.py`

### heretek-swarm/heretek_swarm/audit/
- `heretek-swarm/heretek_swarm/audit/__init__.py`
- `heretek-swarm/heretek_swarm/audit/cli.py`
- `heretek-swarm/heretek_swarm/audit/report.py`
- `heretek-swarm/heretek_swarm/audit/severity.py`
- `heretek-swarm/heretek_swarm/audit/stub_patterns.py`

### heretek-swarm/heretek_swarm/channels/
- `heretek-swarm/heretek_swarm/channels/__init__.py`
- `heretek-swarm/heretek_swarm/channels/defaults.py`
- `heretek-swarm/heretek_swarm/channels/registry.py`

### heretek-swarm/heretek_swarm/cli/
- `heretek-swarm/heretek_swarm/cli/__init__.py`
- `heretek-swarm/heretek_swarm/cli/config_loader.py`

### heretek-swarm/heretek_swarm/collective/
- `heretek-swarm/heretek_swarm/collective/__init__.py`
- `heretek-swarm/heretek_swarm/collective/adaptive_learning.py`
- `heretek-swarm/heretek_swarm/collective/agency_tracking.py`
- `heretek-swarm/heretek_swarm/collective/agent_adaptation.py`
- `heretek-swarm/heretek_swarm/collective/distributed_learning.py`
- `heretek-swarm/heretek_swarm/collective/emergence_analyzer.py`
- `heretek-swarm/heretek_swarm/collective/emergent_detection_types.py`
- `heretek-swarm/heretek_swarm/collective/emergent_detection_utils.py`
- `heretek-swarm/heretek_swarm/collective/emergent_detection.py`
- `heretek-swarm/heretek_swarm/collective/evolution_engine.py`
- `heretek-swarm/heretek_swarm/collective/knowledge_transform.py`
- `heretek-swarm/heretek_swarm/collective/learning.py`
- `heretek-swarm/heretek_swarm/collective/metrics.py`
- `heretek-swarm/heretek_swarm/collective/pattern_library.py`
- `heretek-swarm/heretek_swarm/collective/pattern_validation.py`
- `heretek-swarm/heretek_swarm/collective/society.py`
- `heretek-swarm/heretek_swarm/collective/swarm_intelligence.py`
- `heretek-swarm/heretek_swarm/collective/swarm_patterns.py`

### heretek-swarm/heretek_swarm/collective/algorithms/
- `heretek-swarm/heretek_swarm/collective/algorithms/__init__.py`
- `heretek-swarm/heretek_swarm/collective/algorithms/abc.py`
- `heretek-swarm/heretek_swarm/collective/algorithms/aco.py`
- `heretek-swarm/heretek_swarm/collective/algorithms/pso.py`

### heretek-swarm/heretek_swarm/config/
- `heretek-swarm/heretek_swarm/config/__init__.py`
- `heretek-swarm/heretek_swarm/config/cache.py`
- `heretek-swarm/heretek_swarm/config/crud.py`
- `heretek-swarm/heretek_swarm/config/db_models.py`
- `heretek-swarm/heretek_swarm/config/encryption.py`
- `heretek-swarm/heretek_swarm/config/loader.py`
- `heretek-swarm/heretek_swarm/config/models.py`
- `heretek-swarm/heretek_swarm/config/service.py`

### heretek-swarm/heretek_swarm/consciousness/
- `heretek-swarm/heretek_swarm/consciousness/__init__.py`
- `heretek-swarm/heretek_swarm/consciousness/agency_metrics.py`
- `heretek-swarm/heretek_swarm/consciousness/ast.py`
- `heretek-swarm/heretek_swarm/consciousness/fep_active_inference.py`
- `heretek-swarm/heretek_swarm/consciousness/fep.py`
- `heretek-swarm/heretek_swarm/consciousness/gwt_deliberation.py`
- `heretek-swarm/heretek_swarm/consciousness/gwt.py`
- `heretek-swarm/heretek_swarm/consciousness/iit_phi.py`
- `heretek-swarm/heretek_swarm/consciousness/iit.py`
- `heretek-swarm/heretek_swarm/consciousness/introspection.py`
- `heretek-swarm/heretek_swarm/consciousness/phi_training.py`
- `heretek-swarm/heretek_swarm/consciousness/self_model.py`

### heretek-swarm/heretek_swarm/consciousness/metrics/
- `heretek-swarm/heretek_swarm/consciousness/metrics/__init__.py`
- `heretek-swarm/heretek_swarm/consciousness/metrics/ast.py`
- `heretek-swarm/heretek_swarm/consciousness/metrics/iit.py`

### heretek-swarm/heretek_swarm/consensus/
- `heretek-swarm/heretek_swarm/consensus/__init__.py`
- `heretek-swarm/heretek_swarm/consensus/audit_models.py`
- `heretek-swarm/heretek_swarm/consensus/audit_query.py`
- `heretek-swarm/heretek_swarm/consensus/audit_trail.py`
- `heretek-swarm/heretek_swarm/consensus/audit.py`
- `heretek-swarm/heretek_swarm/consensus/cons01_dispute_resolution.py`
- `heretek-swarm/heretek_swarm/consensus/deliberation.py`
- `heretek-swarm/heretek_swarm/consensus/expertise.py`
- `heretek-swarm/heretek_swarm/consensus/immune.py`
- `heretek-swarm/heretek_swarm/consensus/maker_enhanced.py`
- `heretek-swarm/heretek_swarm/consensus/maker.py`
- `heretek-swarm/heretek_swarm/consensus/mediation.py`
- `heretek-swarm/heretek_swarm/consensus/raft_election.py`
- `heretek-swarm/heretek_swarm/consensus/swarm_deliberation.py`
- `heretek-swarm/heretek_swarm/consensus/tribunal.py`

### heretek-swarm/heretek_swarm/coordination/
- `heretek-swarm/heretek_swarm/coordination/__init__.py`
- `heretek-swarm/heretek_swarm/coordination/paradigm_detection.py`
- `heretek-swarm/heretek_swarm/coordination/sync.py`
- `heretek-swarm/heretek_swarm/coordination/task_graph.py`
- `heretek-swarm/heretek_swarm/coordination/time_dilation.py`

### heretek-swarm/heretek_swarm/creativity/
- `heretek-swarm/heretek_swarm/creativity/__init__.py`
- `heretek-swarm/heretek_swarm/creativity/novel_connections.py`

### heretek-swarm/heretek_swarm/embeddings/providers/
- `heretek-swarm/heretek_swarm/embeddings/providers/__init__.py`
- `heretek-swarm/heretek_swarm/embeddings/providers/base.py`
- `heretek-swarm/heretek_swarm/embeddings/providers/factory.py`
- `heretek-swarm/heretek_swarm/embeddings/providers/ollama_provider.py`
- `heretek-swarm/heretek_swarm/embeddings/providers/openai_provider.py`

### heretek-swarm/heretek_swarm/evaluation/
- `heretek-swarm/heretek_swarm/evaluation/__init__.py`
- `heretek-swarm/heretek_swarm/evaluation/evaluator.py`

### heretek-swarm/heretek_swarm/gateway/
- `heretek-swarm/heretek_swarm/gateway/__init__.py`
- `heretek-swarm/heretek_swarm/gateway/a2a_protocol.py`
- `heretek-swarm/heretek_swarm/gateway/a2a_server.py`
- `heretek-swarm/heretek_swarm/gateway/auth.py`
- `heretek-swarm/heretek_swarm/gateway/content_router.py`
- `heretek-swarm/heretek_swarm/gateway/event_mesh.py`
- `heretek-swarm/heretek_swarm/gateway/external_api.py`
- `heretek-swarm/heretek_swarm/gateway/jetstream_manager.py`
- `heretek-swarm/heretek_swarm/gateway/message_replay.py`
- `heretek-swarm/heretek_swarm/gateway/nats_event_mesh.py`

### heretek-swarm/heretek_swarm/governance/
- `heretek-swarm/heretek_swarm/governance/__init__.py`
- `heretek-swarm/heretek_swarm/governance/agent_identity.py`
- `heretek-swarm/heretek_swarm/governance/coordinator.py`
- `heretek-swarm/heretek_swarm/governance/protocol.py`

### heretek-swarm/heretek_swarm/governance/integrations/
- `heretek-swarm/heretek_swarm/governance/integrations/__init__.py`
- `heretek-swarm/heretek_swarm/governance/integrations/collective_governance.py`
- `heretek-swarm/heretek_swarm/governance/integrations/consensus_governance.py`

### heretek-swarm/heretek_swarm/infrastructure/
- `heretek-swarm/heretek_swarm/infrastructure/__init__.py`
- `heretek-swarm/heretek_swarm/infrastructure/audit.py`
- `heretek-swarm/heretek_swarm/infrastructure/health.py`
- `heretek-swarm/heretek_swarm/infrastructure/provisioner.py`

### heretek-swarm/heretek_swarm/infrastructure/a2a/
- `heretek-swarm/heretek_swarm/infrastructure/a2a/__init__.py`
- `heretek-swarm/heretek_swarm/infrastructure/a2a/protocol.py`

### heretek-swarm/heretek_swarm/infrastructure/nats/
- `heretek-swarm/heretek_swarm/infrastructure/nats/__init__.py`
- `heretek-swarm/heretek_swarm/infrastructure/nats/broadcast.py`
- `heretek-swarm/heretek_swarm/infrastructure/nats/client.py`
- `heretek-swarm/heretek_swarm/infrastructure/nats/consensus.py`
- `heretek-swarm/heretek_swarm/infrastructure/nats/discovery.py`
- `heretek-swarm/heretek_swarm/infrastructure/nats/memory_sync.py`
- `heretek-swarm/heretek_swarm/infrastructure/nats/publisher.py`
- `heretek-swarm/heretek_swarm/infrastructure/nats/subscriber.py`

### heretek-swarm/heretek_swarm/infrastructure/otel/
- `heretek-swarm/heretek_swarm/infrastructure/otel/__init__.py`
- `heretek-swarm/heretek_swarm/infrastructure/otel/logging.py`
- `heretek-swarm/heretek_swarm/infrastructure/otel/metrics.py`
- `heretek-swarm/heretek_swarm/infrastructure/otel/tracing.py`

### heretek-swarm/heretek_swarm/integrations/
- `heretek-swarm/heretek_swarm/integrations/__init__.py`
- `heretek-swarm/heretek_swarm/integrations/anthropic.py`
- `heretek-swarm/heretek_swarm/integrations/autogen.py`
- `heretek-swarm/heretek_swarm/integrations/crewai.py`
- `heretek-swarm/heretek_swarm/integrations/discord_bot.py`
- `heretek-swarm/heretek_swarm/integrations/langgraph.py`
- `heretek-swarm/heretek_swarm/integrations/manager.py`
- `heretek-swarm/heretek_swarm/integrations/openai_assistants.py`
- `heretek-swarm/heretek_swarm/integrations/praison_handoffs.py`
- `heretek-swarm/heretek_swarm/integrations/slack_bot.py`
- `heretek-swarm/heretek_swarm/integrations/telegram_bot.py`

### heretek-swarm/heretek_swarm/interfaces/
- `heretek-swarm/heretek_swarm/interfaces/__init__.py`
- `heretek-swarm/heretek_swarm/interfaces/providers.py`
- `heretek-swarm/heretek_swarm/interfaces/registry.py`

### heretek-swarm/heretek_swarm/knowledge/
- `heretek-swarm/heretek_swarm/knowledge/__init__.py`
- `heretek-swarm/heretek_swarm/knowledge/research.py`
- `heretek-swarm/heretek_swarm/knowledge/unified_access.py`

### heretek-swarm/heretek_swarm/llm/
- `heretek-swarm/heretek_swarm/llm/model_garage.py`

### heretek-swarm/heretek_swarm/llm/providers/
- `heretek-swarm/heretek_swarm/llm/providers/__init__.py`
- `heretek-swarm/heretek_swarm/llm/providers/base.py`
- `heretek-swarm/heretek_swarm/llm/providers/factory.py`
- `heretek-swarm/heretek_swarm/llm/providers/lemonade_provider.py`
- `heretek-swarm/heretek_swarm/llm/providers/llamacpp_provider.py`
- `heretek-swarm/heretek_swarm/llm/providers/minimax_provider.py`
- `heretek-swarm/heretek_swarm/llm/providers/ollama_provider.py`
- `heretek-swarm/heretek_swarm/llm/providers/openai_compatible.py`
- `heretek-swarm/heretek_swarm/llm/providers/openai_provider.py`
- `heretek-swarm/heretek_swarm/llm/providers/zai_provider.py`

### heretek-swarm/heretek_swarm/logging/
- `heretek-swarm/heretek_swarm/logging/__init__.py`
- `heretek-swarm/heretek_swarm/logging/config.py`

### heretek-swarm/heretek_swarm/mcp/
- `heretek-swarm/heretek_swarm/mcp/__init__.py`
- `heretek-swarm/heretek_swarm/mcp/client.py`
- `heretek-swarm/heretek_swarm/mcp/registry.py`
- `heretek-swarm/heretek_swarm/mcp/server.py`

### heretek-swarm/heretek_swarm/memory/
- `heretek-swarm/heretek_swarm/memory/__init__.py`
- `heretek-swarm/heretek_swarm/memory/access_patterns.py`
- `heretek-swarm/heretek_swarm/memory/base.py`
- `heretek-swarm/heretek_swarm/memory/compression.py`
- `heretek-swarm/heretek_swarm/memory/eliza_memory.py`
- `heretek-swarm/heretek_swarm/memory/migration_strategies.py`
- `heretek-swarm/heretek_swarm/memory/persistent.py`
- `heretek-swarm/heretek_swarm/memory/prefetcher.py`
- `heretek-swarm/heretek_swarm/memory/tiering.py`
- `heretek-swarm/heretek_swarm/memory/versioned.py`

### heretek-swarm/heretek_swarm/models/
- `heretek-swarm/heretek_swarm/models/__init__.py`
- `heretek-swarm/heretek_swarm/models/external_call_log_encryption.py`
- `heretek-swarm/heretek_swarm/models/external_call_log.py`

### heretek-swarm/heretek_swarm/observability/
- `heretek-swarm/heretek_swarm/observability/__init__.py`
- `heretek-swarm/heretek_swarm/observability/alerting.py`
- `heretek-swarm/heretek_swarm/observability/metrics.py`
- `heretek-swarm/heretek_swarm/observability/prometheus_metrics.py`
- `heretek-swarm/heretek_swarm/observability/tracing.py`

### heretek-swarm/heretek_swarm/orchestration/
- `heretek-swarm/heretek_swarm/orchestration/__init__.py`
- `heretek-swarm/heretek_swarm/orchestration/heavyswarm.py`
- `heretek-swarm/heretek_swarm/orchestration/phase_handlers.py`

### heretek-swarm/heretek_swarm/plugins/
- `heretek-swarm/heretek_swarm/plugins/__init__.py`
- `heretek-swarm/heretek_swarm/plugins/consciousness_enhanced.py`
- `heretek-swarm/heretek_swarm/plugins/consciousness_metrics.py`
- `heretek-swarm/heretek_swarm/plugins/consciousness.py`
- `heretek-swarm/heretek_swarm/plugins/examples.py`
- `heretek-swarm/heretek_swarm/plugins/liberation.py`
- `heretek-swarm/heretek_swarm/plugins/manager.py`

### heretek-swarm/heretek_swarm/rag/
- `heretek-swarm/heretek_swarm/rag/__init__.py`
- `heretek-swarm/heretek_swarm/rag/document_processor.py`
- `heretek-swarm/heretek_swarm/rag/hybrid_retriever.py`
- `heretek-swarm/heretek_swarm/rag/knowledge_graph.py`
- `heretek-swarm/heretek_swarm/rag/rag_pipeline.py`
- `heretek-swarm/heretek_swarm/rag/retriever.py`
- `heretek-swarm/heretek_swarm/rag/strategies.py`

### heretek-swarm/heretek_swarm/routing/
- `heretek-swarm/heretek_swarm/routing/__init__.py`
- `heretek-swarm/heretek_swarm/routing/model_router.py`

### heretek-swarm/heretek_swarm/runtime/
- `heretek-swarm/heretek_swarm/runtime/__init__.py`
- `heretek-swarm/heretek_swarm/runtime/agent_runtime.py`
- `heretek-swarm/heretek_swarm/runtime/autonomous_runtime_config.py`
- `heretek-swarm/heretek_swarm/runtime/autonomous_runtime.py`
- `heretek-swarm/heretek_swarm/runtime/characters.py`
- `heretek-swarm/heretek_swarm/runtime/main_loop.py`
- `heretek-swarm/heretek_swarm/runtime/registry_enhanced.py`
- `heretek-swarm/heretek_swarm/runtime/registry.py`
- `heretek-swarm/heretek_swarm/runtime/scaling.py`
- `heretek-swarm/heretek_swarm/runtime/self_maintenance.py`
- `heretek-swarm/heretek_swarm/runtime/startup_manager.py`
- `heretek-swarm/heretek_swarm/runtime/tools.py`

### heretek-swarm/heretek_swarm/runtime/characters/
- *(22 files: 22 .json)*

### heretek-swarm/heretek_swarm/schemas/
- `heretek-swarm/heretek_swarm/schemas/__init__.py`
- `heretek-swarm/heretek_swarm/schemas/external_call_log.py`

### heretek-swarm/heretek_swarm/security/
- `heretek-swarm/heretek_swarm/security/__init__.py`
- `heretek-swarm/heretek_swarm/security/adversarial.py`
- `heretek-swarm/heretek_swarm/security/anomaly_detection.py`
- `heretek-swarm/heretek_swarm/security/baseline_update.py`
- `heretek-swarm/heretek_swarm/security/behavioral_baseline.py`
- `heretek-swarm/heretek_swarm/security/ddos_protection.py`
- `heretek-swarm/heretek_swarm/security/guardrails.py`
- `heretek-swarm/heretek_swarm/security/safe01_anomaly_response.py`
- `heretek-swarm/heretek_swarm/security/threat_detection.py`
- `heretek-swarm/heretek_swarm/security/validators.py`
- `heretek-swarm/heretek_swarm/security/zero_trust.py`

### heretek-swarm/heretek_swarm/state/
- `heretek-swarm/heretek_swarm/state/__init__.py`
- `heretek-swarm/heretek_swarm/state/event_store.py`
- `heretek-swarm/heretek_swarm/state/models.py`
- `heretek-swarm/heretek_swarm/state/repository.py`

### heretek-swarm/heretek_swarm/testing/
- `heretek-swarm/heretek_swarm/testing/__init__.py`
- `heretek-swarm/heretek_swarm/testing/stress_testing.py`

### heretek-swarm/heretek_swarm/tools/
- `heretek-swarm/heretek_swarm/tools/__init__.py`
- `heretek-swarm/heretek_swarm/tools/base.py`
- `heretek-swarm/heretek_swarm/tools/examples.py`
- `heretek-swarm/heretek_swarm/tools/mcp_tools.py`
- `heretek-swarm/heretek_swarm/tools/registrars.py`
- `heretek-swarm/heretek_swarm/tools/registry.py`

### heretek-swarm/heretek_swarm/utils/
- `heretek-swarm/heretek_swarm/utils/__init__.py`
- `heretek-swarm/heretek_swarm/utils/lazy_imports.py`

### heretek-swarm/heretek_swarm/validation/
- `heretek-swarm/heretek_swarm/validation/__init__.py`
- `heretek-swarm/heretek_swarm/validation/agent_messages.py`
- `heretek-swarm/heretek_swarm/validation/llm_output.py`

### heretek-swarm/heretek_swarm/workflow/
- `heretek-swarm/heretek_swarm/workflow/__init__.py`
- `heretek-swarm/heretek_swarm/workflow/cycle_detector.py`
- `heretek-swarm/heretek_swarm/workflow/engine.py`
- `heretek-swarm/heretek_swarm/workflow/strategies.py`
- `heretek-swarm/heretek_swarm/workflow/validator.py`

### heretek_swarm/
- `heretek_swarm/Dockerfile`

### migrations/
- `migrations/001_create_swarm_memories.sql`
- `migrations/002_create_agent_states.sql`
- `migrations/003_create_workflow_states.sql`
- `migrations/004_create_consensus_votes.sql`
- `migrations/005_create_collective_learning_tables.sql`
- `migrations/006_create_consensus_enhancement_tables.sql`
- `migrations/007_create_memory_optimization_tables.sql`
- `migrations/008_create_agent_wiring_state_tables.sql`
- `migrations/009_create_configuration_tables.sql`
- `migrations/010_create_external_call_logs.sql`
- `migrations/011_create_infrastructure_config_table.sql`
- `migrations/README.md`

### migrations/rollbacks/
- `migrations/rollbacks/005_rollback_collective_learning.sql`
- `migrations/rollbacks/006_rollback_consensus_enhancement.sql`
- `migrations/rollbacks/007_rollback_memory_optimization.sql`
- `migrations/rollbacks/008_rollback_agent_wiring_state.sql`

### migrations/scripts/
- `migrations/scripts/setup_qdrant_collections.py`

### src/
- `src/__init__.py`
- `src/cli.py`

### src/agent_workspace/
- `src/agent_workspace/error.txt`

### swarm-dashboard/.claude-flow/data/
- `swarm-dashboard/.claude-flow/data/pending-insights.jsonl`

### swarm-dashboard/.claude-flow/sessions/
- `swarm-dashboard/.claude-flow/sessions/current.json`
- `swarm-dashboard/.claude-flow/sessions/session-1776110279640.json`
- `swarm-dashboard/.claude-flow/sessions/session-1776110662041.json`
