"""
Autonomous Main Loop - 24/7 Operation Entry Point for Heretek Swarm

This is the primary entry point for autonomous operation.
Wires together all components into a cohesive autonomous system:
- 23 agents across 6 tiers
- Communication channels via NATS/A2A
- MCP tools registry
- Memory and RAG systems
- MAKER consensus engine
- Health monitoring and auto-recovery

Based on architecture from:
- AUTONOMOUS_WORKFLOW_DESIGN-QWEN.md
- AUTONOMOUS_WORKFLOW_DESIGN-GLM5.md
- AUTONOMOUS_WORKFLOW_DESIGN-MINIMAX.md
"""

import asyncio
import contextlib
import os
from datetime import UTC, datetime
from typing import Any

import structlog

from heretek_swarm.actors.stubs import StubEventMesh
from heretek_swarm.actors.supervisor import ActorSupervisor
from heretek_swarm.api.consciousness import get_consciousness_plugin
from heretek_swarm.channels.registry import ChannelRegistry, GroupRegistry
from heretek_swarm.consensus.consensus_coordinator import ConsensusCoordinator
from heretek_swarm.consensus.domain_selector import DomainSelector
from heretek_swarm.consensus.election_manager import ElectionManager
from heretek_swarm.consensus.maker import MAKERConsensus
from heretek_swarm.gateway.nats_event_mesh import NATSEventMeshWithJetStream
from heretek_swarm.goals.pipeline import run_goal_cycle
from heretek_swarm.goals.store import FileGoalStore
from heretek_swarm.llm.model_garage import ModelGarage
from heretek_swarm.memory.cognee_reader import CogneeMemoryReader
from heretek_swarm.memory.cognee_writer import CogneeMemoryWriter
from heretek_swarm.rag.cognee_rag import CogneeRAGRetriever, get_rag_retriever
from heretek_swarm.routing.model_router import set_global_model_garage
from heretek_swarm.runtime.actor_orchestrator import ActorOrchestrator
from heretek_swarm.runtime.deliberation_orchestrator import DeliberationOrchestrator
from heretek_swarm.runtime.registry_enhanced import get_enhanced_registry
from heretek_swarm.runtime.steward_pulse import run_steward_pulse
from heretek_swarm.tools.mcp_tools import CoreMCPTools

logger = structlog.get_logger(__name__)


class AutonomousSwarm:
    """
    Main entry point for autonomous 24/7 swarm operation.

    Coordinates all components into a unified autonomous loop:
    - Initializes all 23 agents
    - Sets up communication channels
    - Starts health monitoring
    - Runs continuous task processing

    Attributes:
        config: Configuration dictionary
        supervisor: Actor supervisor for health monitoring
        event_mesh: NATS event mesh for communication
        _cognee_reader: Cognee read client for graph-augmented retrieval
        _cognee_writer: Cognee write client for knowledge ingestion
        rag: RAG pipeline for knowledge retrieval
        consensus: MAKER consensus engine
        channel_registry: Communication channel registry
        mcp_tools: MCP tools registry
    """

    def __init__(self, config: dict[str, Any] | None = None, no_infra: bool = False):
        self._no_infra = no_infra
        if no_infra:
            self.config = config or {}
        else:
            self.config = config or self._default_config()

        # Core components (initialized in initialize())
        self.supervisor: ActorSupervisor | None = None
        self.event_mesh: NATSEventMeshWithJetStream | None = None
        self._cognee_reader: CogneeMemoryReader | None = None
        self._cognee_writer: CogneeMemoryWriter | None = None
        self.rag: CogneeRAGRetriever | None = None
        self.consensus: MAKERConsensus | None = None
        self.channel_registry: ChannelRegistry | None = None
        self.group_registry: GroupRegistry | None = None
        self.mcp_tools: CoreMCPTools | None = None
        self.model_garage: ModelGarage | None = None

        # State
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._health_check_interval = self.config.get("health_check_interval", 30)
        self._loop_interval = self.config.get("loop_interval", 1)
        self._consciousness_interval = self.config.get("consciousness_interval", 5)
        self._memory_maintenance_interval = self.config.get("memory_maintenance_interval", 300)
        self._scaling_interval = self.config.get("scaling_interval", 60)

        # S04: Periodic analysis cycle counter — triggers Metis/Empath every 30 cycles
        self._analysis_cycle_count = 0

        # S03: RAFT election manager (initialized in initialize() unless --no-infra)
        self._election_manager = None  # ElectionManager | None

        # M011: Goal pipeline store (initialized on first use in --no-infra path)
        self._goal_store: FileGoalStore | None = None

        # Orchestrators — created in __init__, wired during initialize()
        # DeliberationOrchestrator handles triad, MAKER consensus, and routed tasks
        self._deliberation = DeliberationOrchestrator(
            supervisor=self.supervisor,
            consensus=self.consensus,
            config=self.config,
        )
        # ActorOrchestrator handles agent spawning and channel subscriptions
        self._actor_orch = ActorOrchestrator(
            supervisor=self.supervisor,
            mcp_tools=self.mcp_tools,
            channel_registry=self.channel_registry,
            event_mesh=self.event_mesh,
        )

    def _default_config(self) -> dict[str, Any]:
        """Default configuration for autonomous swarm."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL is required. Set it to postgresql://user:pass@host:port/db "
                "or use docker compose."
            )

        nats_url = os.getenv("HERETEK_NATS_URL")
        if not nats_url:
            raise RuntimeError(
                "HERETEK_NATS_URL is required. Set it to nats://host:port "
                "or use docker compose."
            )
        nats_servers = [s.strip() for s in nats_url.split(",")]

        return {
            "nats_servers": nats_servers,
            "health_check_interval": 30,
            "loop_interval": 1,
            "consciousness_interval": 5,
            "memory_maintenance_interval": 300,
            "scaling_interval": 60,
            "ephemeral": {"ttl_seconds": 3600},
            "persistent": {
                "connection_string": database_url,
            },
            "rag": {
                "embedding_provider": "openai",
                "collection_name": "heretek_documents",
            },
            "consensus": {
                "ahead_by_k": 2,
                "min_votes": 3,
                "red_flag_threshold": 0.3,
            },
        }

    async def initialize(self) -> None:
        """Initialize all swarm components.

        Each component is wrapped in an independent try/except so a failure
        in one step (e.g. NATS unavailable) does not crash the entire swarm.
        """
        logger.info("initializing_autonomous_swarm", no_infra=self._no_infra)

        # Auto-enable OTel tracing when OTLP endpoint is configured
        if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            try:
                from heretek_swarm.infrastructure.otel.tracing import (
                    TracingConfig,
                    init_tracing,
                )

                config = TracingConfig(exporter="otlp")
                init_tracing(config)
                logger.info("otel_tracing_auto_enabled")
            except Exception as exc:
                logger.warning("otel_tracing_auto_enable_failed", error=str(exc))

        if self._no_infra:
            await self._initialize_no_infra()
            return

        await self._initialize_channel_registry()
        await self._initialize_memory()
        await self._initialize_rag()
        await self._initialize_consensus()
        await self._initialize_event_mesh()
        await self._initialize_jetstream()
        await self._initialize_mcp_tools()
        await self._initialize_supervisor()
        await self._initialize_model_garage()
        await self._initialize_election_manager()
        self._rewire_orchestrator_refs()
        self._thread_event_mesh_to_supervisor()
        await self._spawn_all_actors()
        await self._create_per_agent_streams()
        await self._setup_channel_subscriptions()

        logger.info("autonomous_swarm_fully_initialized")

    async def _initialize_no_infra(self) -> None:
        """Initialize in-memory components when --no-infra is set."""
        logger.warning("infra_skipped_no_infra_flag")
        self.channel_registry = ChannelRegistry()
        self.group_registry = GroupRegistry(self.channel_registry)
        self.rag = get_rag_retriever()
        consensus_config = self.config.get("consensus", {})
        self.consensus = MAKERConsensus(
            ahead_by_k=consensus_config.get("ahead_by_k", 2),
            min_votes=consensus_config.get("min_votes", 3),
            confidence_threshold=consensus_config.get("red_flag_threshold", 0.3),
        )
        self.mcp_tools = CoreMCPTools(
            cognee_reader=None,
            cognee_writer=None,
            rag_retriever=self.rag,
            consensus_engine=self.consensus,
            event_mesh=None,
        )
        from heretek_swarm.mcp.bridge import sync_mcp_registries
        bridged = sync_mcp_registries(self.mcp_tools)
        logger.info("mcp_bridge_applied", tool_count=bridged)
        self.model_garage = ModelGarage()
        await self.model_garage.initialize()
        set_global_model_garage(self.model_garage)
        logger.info("model_garage_initialized")
        self._election_manager = None
        logger.info("election_manager_skipped_no_infra")
        self.supervisor = ActorSupervisor(
            health_check_interval=self._health_check_interval, auto_restart=True, max_restarts=5
        )
        self.event_mesh = StubEventMesh()
        await self.event_mesh.connect()
        self.supervisor._event_mesh = self.event_mesh
        self._actor_orch._supervisor = self.supervisor
        self._actor_orch._mcp_tools = self.mcp_tools
        self._actor_orch._channel_registry = self.channel_registry
        self._actor_orch._event_mesh = self.event_mesh
        self._deliberation._supervisor = self.supervisor
        self._deliberation._consensus = self.consensus
        await self._actor_orch.spawn_all_actors()
        logger.info("autonomous_swarm_fully_initialized", event_mesh_type="StubEventMesh")

    async def _initialize_channel_registry(self) -> None:
        try:
            self.channel_registry = ChannelRegistry()
            self.group_registry = GroupRegistry(self.channel_registry)
            logger.info("channel_registry_initialized")
        except Exception as exc:
            logger.warning("channel_registry_init_failed", error=str(exc))
            self.channel_registry = None
            self.group_registry = None

    async def _initialize_memory(self) -> None:
        try:
            self._cognee_reader = CogneeMemoryReader()
            self._cognee_writer = CogneeMemoryWriter()
            reader_ok = await self._cognee_reader.health()
            writer_ok = await self._cognee_writer.health()
            logger.info(
                "cognee_memory_initialized",
                reader_ok=reader_ok,
                writer_ok=writer_ok,
            )
        except Exception as exc:
            logger.warning("cognee_memory_init_failed", error=str(exc))
            self._cognee_reader = None
            self._cognee_writer = None

    async def _initialize_rag(self) -> None:
        try:
            self.rag = get_rag_retriever()
            logger.info("cognee_rag_retriever_initialized")
        except Exception as exc:
            logger.warning("rag_init_failed", error=str(exc))
            self.rag = None

    async def _initialize_consensus(self) -> None:
        try:
            consensus_config = self.config.get("consensus", {})
            self.consensus = MAKERConsensus(
                ahead_by_k=consensus_config.get("ahead_by_k", 2),
                min_votes=consensus_config.get("min_votes", 3),
                confidence_threshold=consensus_config.get("red_flag_threshold", 0.3),
            )
            logger.info("maker_consensus_initialized")
        except Exception as exc:
            logger.warning("consensus_init_failed", error=str(exc))
            self.consensus = None

    async def _initialize_event_mesh(self) -> None:
        try:
            servers = self.config.get("nats_servers")
            if not servers:
                nats_url = os.getenv("HERETEK_NATS_URL")
                if not nats_url:
                    raise RuntimeError(
                        "HERETEK_NATS_URL is required. Set it to nats://host:port "
                        "or use docker compose."
                    )
                servers = [s.strip() for s in nats_url.split(",")]
            self.event_mesh = NATSEventMeshWithJetStream(servers=servers, fallback=True)
            await self.event_mesh.connect()
            logger.info("event_mesh_connected")
        except Exception as exc:
            logger.warning("event_mesh_init_failed", error=str(exc))
            self.event_mesh = None

    async def _initialize_jetstream(self) -> None:
        if self.event_mesh is None:
            logger.warning("jetstream_skipped", message="No event mesh available")
            return
        try:
            ok = await self.event_mesh.initialize_jetstream(create_default_streams=True)
            if ok:
                logger.info("jetstream_streams_initialized")
            else:
                logger.warning("jetstream_initialization_failed", message="Continuing without durable streams")
        except Exception as exc:
            logger.warning("jetstream_init_failed", error=str(exc))

    async def _initialize_mcp_tools(self) -> None:
        try:
            self.mcp_tools = CoreMCPTools(
                cognee_reader=self._cognee_reader,
                cognee_writer=self._cognee_writer,
                rag_retriever=self.rag,
                consensus_engine=self.consensus,
                event_mesh=self.event_mesh,
            )
            from heretek_swarm.mcp.bridge import sync_mcp_registries
            bridged = sync_mcp_registries(self.mcp_tools)
            logger.info(
                "mcp_tools_initialized",
                tool_count=len(self.mcp_tools.get_registry().list_tools()),
                bridged_count=bridged,
            )
        except Exception as exc:
            logger.warning("mcp_tools_init_failed", error=str(exc))
            self.mcp_tools = None

    async def _initialize_supervisor(self) -> None:
        try:
            self.supervisor = ActorSupervisor(
                health_check_interval=self._health_check_interval,
                auto_restart=True, max_restarts=5,
            )
            logger.info("actor_supervisor_initialized")
        except Exception as exc:
            logger.warning("supervisor_init_failed", error=str(exc))
            self.supervisor = None

    async def _initialize_model_garage(self) -> None:
        try:
            self.model_garage = ModelGarage()
            await self.model_garage.initialize()
            set_global_model_garage(self.model_garage)
            logger.info("model_garage_initialized")
        except Exception as exc:
            logger.warning("model_garage_init_failed", error=str(exc))
            self.model_garage = None

    async def _initialize_election_manager(self) -> None:
        try:
            self._election_manager = ElectionManager()
            logger.info(
                "election_manager_initialized",
                governance_agents=sorted(self._election_manager._rafts.keys()),
            )
        except Exception as exc:
            logger.warning("election_manager_init_failed", error=str(exc))
            self._election_manager = None

    def _rewire_orchestrator_refs(self) -> None:
        self._actor_orch._supervisor = self.supervisor
        self._actor_orch._mcp_tools = self.mcp_tools
        self._actor_orch._channel_registry = self.channel_registry
        self._actor_orch._event_mesh = self.event_mesh
        self._deliberation._supervisor = self.supervisor
        self._deliberation._consensus = self.consensus

    def _thread_event_mesh_to_supervisor(self) -> None:
        if self.event_mesh is not None:
            if self.event_mesh.is_connected:
                self.supervisor._event_mesh = self.event_mesh
                logger.info("event_mesh_threaded_to_supervisor", mesh_type="NATSEventMeshWithJetStream")
            else:
                logger.warning(
                    "event_mesh_not_connected_at_spawn_time",
                    message="Event mesh exists but is_connected is False — agents will use stubs.",
                )
                self.supervisor._event_mesh = None

    async def _spawn_all_actors(self) -> None:
        try:
            await self._actor_orch.spawn_all_actors()
            logger.info("all_actors_spawned")
            from heretek_swarm.actors.supervisor import get_supervisor
            get_supervisor().actors.update(self.supervisor.actors)
            logger.info("actor_registry_bridged", total_actors=len(self.supervisor.actors))
        except Exception as exc:
            logger.warning("actor_spawn_init_failed", error=str(exc))

    async def _create_per_agent_streams(self) -> None:
        try:
            if self.event_mesh is not None and self.event_mesh.jetstream_enabled:
                agent_ids = list(self.supervisor.actors.keys()) if self.supervisor else []
                stream_result = await self.event_mesh.ensure_agent_streams(agent_ids)
                logger.info(
                    "per_agent_jetstream_streams_created",
                    created=stream_result.get("created", 0),
                    skipped=stream_result.get("skipped", 0),
                )
            else:
                logger.warning(
                    "per_agent_streams_skipped",
                    message="No event mesh or JetStream not enabled",
                )
        except Exception as exc:
            logger.warning("per_agent_streams_init_failed", error=str(exc))

    async def _setup_channel_subscriptions(self) -> None:
        try:
            await self._actor_orch.setup_channel_subscriptions()
            logger.info("channel_subscriptions_configured")
        except Exception as exc:
            logger.warning("channel_subscriptions_init_failed", error=str(exc))

    async def run_deliberation(
        self,
        prompt: str,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Run a triad deliberation — delegates to DeliberationOrchestrator."""
        return await self._deliberation.run_deliberation(prompt, timeout)

    async def run_consensus(
        self,
        question: str,
        timeout: float = 120,
        max_rounds: int = 3,
    ) -> dict[str, Any]:
        """Run MAKER consensus — delegates to DeliberationOrchestrator."""
        return await self._deliberation.run_consensus(question, timeout, max_rounds)

    async def run_routed_task(
        self,
        agent_name: str,
        task_type: str,
        task_data: dict[str, Any],
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Route a task to a specific agent — delegates to DeliberationOrchestrator."""
        return await self._deliberation.run_routed_task(agent_name, task_type, task_data, timeout)

    def get_startup_status(self) -> dict[str, str]:
        """Return startup status of each component for diagnostics."""
        status: dict[str, str] = {}
        self._add_component_status(status, "Channels", self.channel_registry)
        self._add_component_status(status, "Cognee Reader", self._cognee_reader)
        self._add_component_status(status, "Cognee Writer", self._cognee_writer)
        self._add_component_status(status, "RAG", self.rag)
        self._add_component_status(status, "Consensus", self.consensus)
        self._add_component_status(status, "Event Mesh", self.event_mesh, "Connected")
        self._add_component_status(status, "MCP Tools", self.mcp_tools)
        self._add_agent_status(status)
        return status

    @staticmethod
    def _add_component_status(
        status: dict[str, str], name: str, component: object, label: str = "Initialized"
    ) -> None:
        status[name] = f"✓ {label}" if component is not None else "✗ Unavailable"

    def _add_agent_status(self, status: dict[str, str]) -> None:
        if self.supervisor is not None:
            agent_count = len(self.supervisor.actors) if hasattr(self.supervisor, "actors") else 0
            status["Agents"] = f"✓ {agent_count} spawned"
        else:
            status["Agents"] = "✗ Unavailable"

    async def run(self) -> None:
        """Main autonomous loop - runs 24/7."""
        logger.info("starting_autonomous_loop")
        self._running = True

        # Gate consciousness loop behind CONSCIOUSNESS_ENABLED (default: false)
        consciousness_enabled = os.getenv("CONSCIOUSNESS_ENABLED", "false").lower() == "true"

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._health_monitor_loop()),
            asyncio.create_task(self._task_processing_loop()),
            asyncio.create_task(self._memory_maintenance_loop()),
            asyncio.create_task(self._scaling_loop()),
            asyncio.create_task(self._report_agents_loop()),
            asyncio.create_task(self._steward_pulse_loop()),
        ]

        if consciousness_enabled:
            self._tasks.append(asyncio.create_task(self._consciousness_loop()))
            logger.info("consciousness_loop_enabled")
        else:
            logger.info("consciousness_loop_disabled", hint="Set CONSCIOUSNESS_ENABLED=true to enable")

        logger.info("autonomous_loop_started", background_tasks=len(self._tasks))

        # Main loop
        try:
            while self._running:
                try:
                    await self._process_cycle()
                    await asyncio.sleep(self._loop_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("autonomous_loop_error", error=str(e))
                    await asyncio.sleep(5)  # Backoff on error
        finally:
            await self.shutdown()

    async def _process_cycle(self) -> None:
        """Process one cycle of the autonomous loop."""
        # 1. Check for scheduled tasks (Chronos)
        await self._process_scheduled_tasks()

        # 2. Check for external events (Nexus/Echo)
        await self._process_external_events()

        # 3. Process pending workflows
        await self._process_workflows()

        # 4. Run health checks
        await self._run_health_checks()

        # 5. Periodic analysis (Metis/Empath) every 30 cycles
        self._analysis_cycle_count += 1
        if self._analysis_cycle_count >= 30:
            self._analysis_cycle_count = 0
            await self._trigger_periodic_analysis()

        # 6. Log cycle completion to Historian
        historian = self.supervisor.actors.get("historian") if self.supervisor else None
        if historian is not None:
            await historian.log_event("cycle_complete", "main_loop", {})

    async def _process_scheduled_tasks(self) -> None:
        """Process tasks scheduled by Chronos.

        Gets due ticks from the Chronos actor, routes each tick to its
        target agent via ``put_message()``, and logs the cycle event to
        the Historian actor.

        Gracefully handles missing Chronos, Historian, or target agents
        in the supervisor registry — logs a warning and skips each.
        """
        # 1. Get the Chronos actor
        chronos = self.supervisor.actors.get("chronos") if self.supervisor else None
        if chronos is None:
            logger.warning("scheduled_tasks_skipped_no_chronos")
            return

        # 2. Get due ticks
        ticks = await chronos.generate_ticks()

        # 3. Route each tick to its target agent
        for tick in ticks:
            target = self.supervisor.actors.get(tick.agent_id) if self.supervisor else None
            if target is None:
                logger.warning(
                    "scheduled_task_skipped_no_target",
                    tick_id=tick.tick_id,
                    agent_id=tick.agent_id,
                )
                continue

            from heretek_swarm.actors.base import ActorMessage

            msg = ActorMessage(
                sender="chronos",
                message_type=tick.action,
                content=tick.to_dict(),
                timestamp=datetime.now(UTC).isoformat(),
                recipient=tick.agent_id,
            )
            await target.put_message(msg)

        # 4. Log event to Historian
        historian = self.supervisor.actors.get("historian") if self.supervisor else None
        if historian is not None:
            await historian.log_event(
                "cycle_scheduled_tasks",
                "main_loop",
                {"tick_count": len(ticks)},
            )
        else:
            logger.warning("scheduled_tasks_historian_skipped_no_historian")

    async def _trigger_periodic_analysis(self) -> None:
        """Trigger periodic Metis analysis and Empath sentiment analysis.

        Called every 30 cycles from _process_cycle(). Sends on-demand
        analysis/sentiment requests to metis and empath agents via
        put_message().  Uses the None-guard pattern from
        _process_scheduled_tasks(): missing agents are logged with a
        warning and skipped gracefully.
        """
        # Build a shared context string from recent cycle activity
        context = (
            f"Cycle analysis at tick {self._analysis_cycle_count}. "
            "Provide a concise strategic overview of current swarm state."
        )

        # --- Metis analysis ---
        metis = self.supervisor.actors.get("metis") if self.supervisor else None
        if metis is not None:
            from heretek_swarm.actors.base import ActorMessage

            msg = ActorMessage(
                sender="main_loop",
                message_type="on_demand_analysis",
                content={
                    "context": context,
                    "perspective": "neutral",
                    "reply_to": "main_loop_analysis",
                },
                timestamp=datetime.now(UTC).isoformat(),
            )
            await metis.put_message(msg)
            logger.info("periodic_metis_analysis_dispatched")
        else:
            logger.warning("periodic_analysis_skipped_no_metis")

        # --- Empath sentiment ---
        empath = self.supervisor.actors.get("empath") if self.supervisor else None
        if empath is not None:
            from heretek_swarm.actors.base import ActorMessage

            msg = ActorMessage(
                sender="main_loop",
                message_type="on_demand_sentiment",
                content={
                    "text": context,
                    "source_agent": "main_loop",
                    "reply_to": "main_loop_sentiment",
                },
                timestamp=datetime.now(UTC).isoformat(),
            )
            await empath.put_message(msg)
            logger.info("periodic_empath_sentiment_dispatched")
        else:
            logger.warning("periodic_analysis_skipped_no_empath")

        # --- Log to Historian ---
        historian = self.supervisor.actors.get("historian") if self.supervisor else None
        if historian is not None:
            await historian.log_event(
                "periodic_analysis",
                "main_loop",
                {
                    "metis_dispatched": metis is not None,
                    "empath_dispatched": empath is not None,
                },
            )
        else:
            logger.warning("periodic_analysis_historian_skipped_no_historian")

        # --- M011: Autonomous goal pipeline ---
        await self._run_goal_pipeline(metis, historian)

    async def _run_goal_pipeline(self, metis: Any, historian: Any) -> None:
        """Run the goal pipeline: propose, vote, accept/reject goals.

        Uses a lazily-initialised FileGoalStore and builds a
        ConsensusCoordinator from the swarm's MAKER consensus engine
        and the full actor registry.

        Failures are logged at error level and swallowed so the main
        autonomous loop is never crashed by a goal pipeline fault.
        """
        # Lazily initialise the goal store on first use
        if self._goal_store is None:
            self._goal_store = FileGoalStore()

        if self.consensus is None or self.supervisor is None:
            logger.warning(
                "goal_pipeline_skipped",
                reason="consensus_or_supervisor_unavailable",
            )
            return

        try:
            domain_selector = DomainSelector()
            coordinator = ConsensusCoordinator(
                maker=self.consensus,
                domain_selector=domain_selector,
                actors=self.supervisor.actors,
            )

            await run_goal_cycle(
                store=self._goal_store,
                metis=metis,
                coordinator=coordinator,
                actors=self.supervisor.actors,
                historian=historian,
            )
            logger.info("goal_pipeline_cycle_completed")
        except Exception as exc:
            logger.error(
                "goal_pipeline_cycle_failed",
                goal_pipeline_error=str(exc),
            )

    async def _process_external_events(self) -> None:
        """Process external events from Discord, Slack, Telegram, webhooks."""
        # Check event mesh for external messages
        # Route through Steward for triage

    async def _process_workflows(self) -> None:
        """Process pending workflows."""
        # Check for workflows needing execution
        # Execute HeavySwarm workflows as needed

    async def _run_health_checks(self) -> None:
        """Run health checks on all actors."""
        for agent_id, actor in self.supervisor.actors.items():
            status = actor.get_status()
            if status.state.value == "error":
                logger.warning("actor_error", agent_id=agent_id)
                await self.supervisor.restart_actor(agent_id)

    async def _health_monitor_loop(self) -> None:
        """Continuous health monitoring loop."""
        while self._running:
            try:
                # Publish health metrics
                health_data = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "active_actors": len(self.supervisor.actors),
                    "mailbox_sizes": {
                        agent_id: getattr(actor, "mailbox", asyncio.Queue()).qsize()
                        for agent_id, actor in self.supervisor.actors.items()
                    },
                    "system_status": "healthy",
                }

                await self.event_mesh.publish(
                    "swarm.system.health",
                    health_data,
                )

                logger.debug("health_metrics_published", active_actors=health_data["active_actors"])

                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("health_monitor_error", error=str(e))

    async def _consciousness_loop(self) -> None:
        """Consciousness metrics update loop — wires live agent telemetry to NATS."""
        while self._running:
            try:
                plugin = get_consciousness_plugin()
                registry = get_enhanced_registry()
                phi_stats = plugin.get_statistics()
                attention_distribution, active_count, total_count = self._build_attention_distribution(registry)
                workspace_coherence = active_count / total_count if total_count > 0 else 0.0
                consciousness_data = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "workspace_coherence": workspace_coherence,
                    "attention_distribution": attention_distribution,
                    "phi_metric": phi_stats.get("average_phi", 0.0),
                    "total_agents": total_count,
                    "active_agents": active_count,
                    "average_free_energy": phi_stats.get("average_free_energy", 0.0),
                    "conscious_agents": phi_stats.get("conscious_agents", 0),
                }
                await self.event_mesh.publish("swarm.system.consciousness", consciousness_data)
                await asyncio.sleep(self._consciousness_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("consciousness_loop_error", error=str(e))
                await asyncio.sleep(self._consciousness_interval)

    @staticmethod
    def _build_attention_distribution(registry: Any) -> tuple[dict[str, dict[str, str]], int, int]:
        all_instances = registry.get_all_instances()
        attention_distribution: dict[str, dict[str, str]] = {}
        active_count = 0
        for agent_id, instance in all_instances.items():
            state = getattr(instance, "state", None)
            attention_distribution[agent_id] = {
                "state": str(state.value) if hasattr(state, "value") else str(state),
                "type": getattr(instance, "agent_type", "unknown"),
            }
            if state and hasattr(state, "value"):
                active_count += 1
        return attention_distribution, active_count, len(all_instances)

    async def _task_processing_loop(self) -> None:
        """Task processing loop - polls for new tasks."""
        while self._running:
            try:
                # Poll for new tasks from:
                # - External integrations (Discord, Slack, Telegram)
                # - Webhooks
                # - Scheduled tasks (Chronos)
                # - Internal agent requests

                # Route tasks through Steward for triage
                await asyncio.sleep(self._loop_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("task_processing_error", error=str(e))

    async def _memory_maintenance_loop(self) -> None:
        """Memory tier optimization and cleanup loop."""
        while self._running:
            try:
                # Run memory maintenance
                if self._cognee_reader:
                    await self._cognee_reader.health()
                if self._cognee_writer:
                    await self._cognee_writer.health()

                logger.debug("memory_maintenance_completed")

                await asyncio.sleep(self._memory_maintenance_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("memory_maintenance_error", error=str(e))

    async def _scaling_loop(self) -> None:
        """Auto-scaling check loop."""
        while self._running:
            try:
                # Check queue depths
                # Check resource utilization
                # Scale up/down based on load

                await asyncio.sleep(self._scaling_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("scaling_check_error", error=str(e))

    async def _report_agents_loop(self) -> None:
        """Report agent statuses to the API server periodically."""
        import os

        api_host = os.getenv("HERETEK_API_HOST", "heretek-api")
        api_port = int(os.getenv("HERETEK_API_PORT", "8000"))
        report_interval = 30  # seconds

        while self._running:
            await self._report_agents_batch(api_host, api_port)
            await asyncio.sleep(report_interval)

    async def _report_agents_batch(self, api_host: str, api_port: int) -> None:
        """Collect and report agent statuses to the API server.

        Extracts the agent collection and reporting logic to reduce
        cognitive complexity of the parent loop.
        """
        import httpx

        try:
            agents = self._collect_agent_statuses()
            await self._post_agent_report(api_host, api_port, agents)
        except httpx.ConnectError:
            logger.debug("api_not_available")
        except Exception as e:
            logger.warning("agent_report_failed", error=str(e))

    def _collect_agent_statuses(self) -> list[dict[str, Any]]:
        """Collect status information from all active agents."""
        agents = []
        for agent_id, actor in self.supervisor.actors.items():
            status_dict = self._extract_agent_status(agent_id, actor)
            if status_dict:
                agents.append(status_dict)
        return agents

    def _extract_agent_status(self, agent_id: str, actor: Any) -> dict[str, Any] | None:
        """Extract status dictionary for a single agent.

        Returns None if status cannot be extracted (agent not ready).
        """
        try:
            status = actor.get_status()
            return {
                "agent_id": agent_id,
                "agent_type": getattr(actor, "actor_type", "unknown"),
                "state": status.state.value if status else "unknown",
                "message_count": status.message_count if status else 0,
                "error_count": status.error_count if status else 0,
                "mailbox_size": status.mailbox_size if status else 0,
                "last_activity": status.last_activity if status else None,
                "uptime_seconds": status.uptime_seconds if status else 0.0,
            }
        except Exception:
            return None

    async def _post_agent_report(
        self, api_host: str, api_port: int, agents: list[dict[str, Any]]
    ) -> None:
        """Post agent status report to the API server."""
        import httpx

        payload = {
            "runtime_id": "autonomous",
            "agents": agents,
            "total_agents": len(agents),
            "uptime_seconds": 0.0,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"http://{api_host}:{api_port}/autonomous/agents",
                json=payload,
            )
        logger.debug("reported_agents_to_api", count=len(agents))

    async def _steward_pulse_loop(self) -> None:
        """Steward heartbeat pulse loop — delegates to steward_pulse module."""
        await run_steward_pulse(self)

    async def shutdown(self) -> None:
        """Graceful shutdown of the autonomous swarm."""
        logger.info("shutting_down_autonomous_swarm")

        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        # Terminate all actors
        if self.supervisor:
            await self.supervisor.terminate_all()
            logger.info("all_actors_terminated")

        # Disconnect event mesh
        if self.event_mesh:
            await self.event_mesh.disconnect()
            logger.info("event_mesh_disconnected")

        # Shutdown RAG
        if self.rag:
            await self.rag.shutdown()
            logger.info("rag_shutdown_complete")

        # Close Cognee clients
        if self._cognee_reader:
            await self._cognee_reader.close()
            logger.info("cognee_reader_closed")
        if self._cognee_writer:
            await self._cognee_writer.close()
            logger.info("cognee_writer_closed")

        # Close ModelGarage
        if self.model_garage:
            await self.model_garage.close()
            logger.info("model_garage_closed")

        logger.info("autonomous_swarm_shutdown_complete")


# ============================================================================
# Re-exports for backward compatibility
# ============================================================================


def _get_main():
    """Lazy import for backward-compatible ``main`` access."""
    from heretek_swarm.runtime.entrypoint import main as _entrypoint_main

    return _entrypoint_main


# Keep main available via __init__.py for backward compatibility.
# Direct execution moved to runtime/entrypoint.py.

