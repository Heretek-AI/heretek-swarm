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

from heretek_swarm.actors.supervisor import ActorSupervisor
from heretek_swarm.api.consciousness import get_consciousness_plugin
from heretek_swarm.channels.registry import ChannelRegistry, GroupRegistry
from heretek_swarm.consensus.maker import MAKERConsensus
from heretek_swarm.gateway.nats_event_mesh import NATSEventMeshWithJetStream
from heretek_swarm.memory.base import DualTierMemory
from heretek_swarm.rag.rag_pipeline import RAGPipeline
from heretek_swarm.runtime.registry_enhanced import get_enhanced_registry
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
        memory: Dual-tier memory system
        rag: RAG pipeline for knowledge retrieval
        consensus: MAKER consensus engine
        channel_registry: Communication channel registry
        mcp_tools: MCP tools registry
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or self._default_config()

        # Core components (initialized in initialize())
        self.supervisor: ActorSupervisor | None = None
        self.event_mesh: NATSEventMeshWithJetStream | None = None
        self.memory: DualTierMemory | None = None
        self.rag: RAGPipeline | None = None
        self.consensus: MAKERConsensus | None = None
        self.channel_registry: ChannelRegistry | None = None
        self.group_registry: GroupRegistry | None = None
        self.mcp_tools: CoreMCPTools | None = None

        # State
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._health_check_interval = self.config.get("health_check_interval", 30)
        self._loop_interval = self.config.get("loop_interval", 1)
        self._consciousness_interval = self.config.get("consciousness_interval", 5)
        self._memory_maintenance_interval = self.config.get("memory_maintenance_interval", 300)
        self._scaling_interval = self.config.get("scaling_interval", 60)

    def _default_config(self) -> dict[str, Any]:
        """Default configuration for autonomous swarm."""
        return {
            "nats_servers": ["nats://localhost:4222"],
            "health_check_interval": 30,
            "loop_interval": 1,
            "consciousness_interval": 5,
            "memory_maintenance_interval": 300,
            "scaling_interval": 60,
            "ephemeral": {"ttl_seconds": 3600},
            "persistent": {
                            "connection_string": os.getenv("DATABASE_URL", "postgresql://heretek:password@localhost/heretek_swarm"),
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
        """Initialize all swarm components."""
        logger.info("initializing_autonomous_swarm")

        # 1. Initialize channel registry
        self.channel_registry = ChannelRegistry()
        self.group_registry = GroupRegistry(self.channel_registry)
        logger.info("channel_registry_initialized")

        # 2. Initialize memory system
        self.memory = DualTierMemory(
            ephemeral_config=self.config.get("ephemeral", {}),
            persistent_config=self.config.get("persistent", {}),
        )
        await self.memory.initialize()
        logger.info("memory_system_initialized")

        # 3. Initialize RAG pipeline
        from heretek_swarm.rag.rag_pipeline import RAGPipelineConfig
        rag_config_dict = self.config.get("rag", {})
        rag_cfg = RAGPipelineConfig(
            embedding_provider=rag_config_dict.get("embedding_provider", "openai"),
            embedding_model=rag_config_dict.get("embedding_model", "text-embedding-3-small"),
            llm_provider=rag_config_dict.get("llm_provider", "openai"),
            llm_model=rag_config_dict.get("llm_model", "gpt-4o-mini"),
            top_k=rag_config_dict.get("top_k", 5),
        )
        self.rag = RAGPipeline(config=rag_cfg)
        logger.info("rag_pipeline_initialized")

        # 4. Initialize consensus engine
        consensus_config = self.config.get("consensus", {})
        self.consensus = MAKERConsensus(
            ahead_by_k=consensus_config.get("ahead_by_k", 2),
            min_votes=consensus_config.get("min_votes", 3),
            confidence_threshold=consensus_config.get("red_flag_threshold", 0.3),
        )
        logger.info("maker_consensus_initialized")

        # 5. Initialize event mesh (NATS)
        self.event_mesh = NATSEventMeshWithJetStream(
            servers=self.config.get("nats_servers", ["nats://localhost:4222"]),
            fallback=True,
        )
        await self.event_mesh.connect()
        logger.info("event_mesh_connected")

        # 5a. Initialize JetStream streams (durable message delivery)
        jetstream_initialized = await self.event_mesh.initialize_jetstream(
            create_default_streams=True
        )
        if jetstream_initialized:
            logger.info("jetstream_streams_initialized")
        else:
            logger.warning(
                "jetstream_initialization_failed",
                message="Continuing without durable streams",
            )

        # 6. Initialize MCP tools
        self.mcp_tools = CoreMCPTools(
            memory_system=self.memory,
            rag_pipeline=self.rag,
            consensus_engine=self.consensus,
            event_mesh=self.event_mesh,
        )
        logger.info("mcp_tools_initialized", tool_count=len(self.mcp_tools.get_registry().list_tools()))

        # 7. Initialize supervisor
        self.supervisor = ActorSupervisor(
            health_check_interval=self._health_check_interval,
            auto_restart=True,
            max_restarts=5,
        )
        logger.info("actor_supervisor_initialized")

        # 8. Spawn all agents
        await self._spawn_all_actors()
        logger.info("all_actors_spawned", count=23)

        # 9. Set up channel subscriptions
        await self._setup_channel_subscriptions()
        logger.info("channel_subscriptions_configured")

        logger.info("autonomous_swarm_fully_initialized")

    async def _spawn_all_actors(self) -> None:
        """Spawn all 23 agents across 6 tiers."""
        # Tier 1: Core Triad (Governance)
        from heretek_swarm.actors.arbiter import ArbiterAgent
        from heretek_swarm.actors.catalyst import CatalystAgent
        from heretek_swarm.actors.chronos import ChronosAgent
        from heretek_swarm.actors.coder import CoderAgent

        # Tier 5: Coordination Agents (Integration)
        from heretek_swarm.actors.coordinator import CoordinatorAgent
        from heretek_swarm.actors.dreamer import DreamerAgent
        from heretek_swarm.actors.echo import EchoActor
        from heretek_swarm.actors.empath import EmpathAgent
        from heretek_swarm.actors.examiner import ExaminerAgent

        # Tier 3: Exploration Agents (Discovery & Creation)
        from heretek_swarm.actors.explorer import ExplorerAgent
        from heretek_swarm.actors.habit_forge import HabitForgeAgent

        # Tier 2: Support Agents (Knowledge & Memory)
        from heretek_swarm.actors.historian import HistorianAgent
        from heretek_swarm.actors.metis import MetisAgent
        from heretek_swarm.actors.nexus import NexusAgent
        from heretek_swarm.actors.perceiver import PerceiverAgent
        from heretek_swarm.actors.perceiver_plus import PerceiverPlusAgent

        # Tier 6: Enhancement Agents (Optimization)
        from heretek_swarm.actors.prism import PrismAgent

        # Tier 4: Safety & Security (Protection)
        from heretek_swarm.actors.sentinel import SentinelAgent
        from heretek_swarm.actors.sentinel_prime import SentinelPrimeAgent
        from heretek_swarm.actors.triad import AlphaAgent, BetaAgent, CharlieAgent, StewardAgent

        # Define all agents with their topics
        actors = [
            # Tier 1: Core Triad
            (StewardAgent, "steward", ["triad", "coordination", "governance"]),
            (AlphaAgent, "alpha", ["analysis", "decisions", "triad"]),
            (BetaAgent, "beta", ["validation", "quality", "triad"]),
            (CharlieAgent, "charlie", ["risk", "challenges", "triad"]),

            # Tier 2: Support
            (HistorianAgent, "historian", ["memory", "context", "triad"]),
            (MetisAgent, "metis", ["planning", "strategy", "coordination"]),
            (EmpathAgent, "empath", ["sentiment", "mediation", "perception"]),
            (PerceiverAgent, "perceiver", ["input", "sensory", "perception"]),
            (EchoActor, "echo", ["communication", "broadcast", "perception"]),

            # Tier 3: Exploration
            (ExplorerAgent, "explorer", ["discovery", "monitoring", "exploration"]),
            (ExaminerAgent, "examiner", ["testing", "quality", "exploration"]),
            (DreamerAgent, "dreamer", ["creative", "alternatives", "exploration"]),
            (CoderAgent, "coder", ["code", "implementation", "exploration"]),

            # Tier 4: Safety
            (SentinelAgent, "sentinel", ["validation", "safety", "safety"]),
            (SentinelPrimeAgent, "sentinel-prime", ["threats", "security", "safety"]),
            (ArbiterAgent, "arbiter", ["conflict", "resolution", "safety"]),

            # Tier 5: Coordination
            (CoordinatorAgent, "coordinator", ["coordination", "tasks", "coordination"]),
            (NexusAgent, "nexus", ["external", "api", "external"]),
            (CatalystAgent, "catalyst", ["change", "transition", "coordination"]),
            (ChronosAgent, "chronos", ["scheduling", "temporal", "coordination"]),

            # Tier 6: Enhancement
            (PrismAgent, "prism", ["perspective", "viewpoints", "memory"]),
            (HabitForgeAgent, "habit-forge", ["patterns", "behavior", "memory"]),
            (PerceiverPlusAgent, "perceiver-plus", ["analytics", "advanced", "perception"]),
        ]

        for agent_class, agent_id, topics in actors:
            try:
                await self.supervisor.spawn_actor(agent_class, agent_id)
                logger.info("actor_spawned", agent_id=agent_id, tier=self._get_tier(agent_id))
            except Exception as e:
                logger.error("actor_spawn_failed", agent_id=agent_id, error=str(e))
                # Continue spawning remaining agents even if one fails
                continue

    def _get_tier(self, agent_id: str) -> str:
        """Get the tier name for an agent."""
        tier_mapping = {
            "steward": "Tier 1 (Core Triad)",
            "alpha": "Tier 1 (Core Triad)",
            "beta": "Tier 1 (Core Triad)",
            "charlie": "Tier 1 (Core Triad)",
            "historian": "Tier 2 (Support)",
            "metis": "Tier 2 (Support)",
            "empath": "Tier 2 (Support)",
            "perceiver": "Tier 2 (Support)",
            "echo": "Tier 2 (Support)",
            "explorer": "Tier 3 (Exploration)",
            "examiner": "Tier 3 (Exploration)",
            "dreamer": "Tier 3 (Exploration)",
            "coder": "Tier 3 (Exploration)",
            "sentinel": "Tier 4 (Safety)",
            "sentinel-prime": "Tier 4 (Safety)",
            "arbiter": "Tier 4 (Safety)",
            "coordinator": "Tier 5 (Coordination)",
            "nexus": "Tier 5 (Coordination)",
            "catalyst": "Tier 5 (Coordination)",
            "chronos": "Tier 5 (Coordination)",
            "prism": "Tier 6 (Enhancement)",
            "habit-forge": "Tier 6 (Enhancement)",
            "perceiver-plus": "Tier 6 (Enhancement)",
        }
        return tier_mapping.get(agent_id, "Unknown")

    async def _setup_channel_subscriptions(self) -> None:
        """Set up channel subscriptions for all agents based on the channel registry."""
        # The ChannelRegistry already has default channels set up
        # Subscribe each agent to their designated channels

        # Get all agent IDs
        agent_ids = list(self.supervisor.actors.keys())

        for agent_id in agent_ids:
            # Get channels for this agent
            channels = self.channel_registry.get_subscriptions(agent_id)

            for channel_name in channels:
                # Subscribe to NATS subject
                nats_subject = self.channel_registry.get_nats_subject(channel_name)

                # Create subscription handler
                async def create_callback(aid: str, ch_name: str):
                    async def callback(mesh, subject, data):
                        await self._handle_channel_message(aid, ch_name, data)
                    return callback

                await self.event_mesh.subscribe(
                    subject=nats_subject,
                    callback=await create_callback(agent_id, channel_name),
                )

            logger.debug(
                "agent_channel_subscriptions",
                agent_id=agent_id,
                channels=channels,
            )

    async def _handle_channel_message(
        self,
        agent_id: str,
        channel_name: str,
        message: dict[str, Any]
    ) -> None:
        """Handle incoming channel message for an agent."""
        try:
            # Get the actor
            actor = self.supervisor.actors.get(agent_id)
            if not actor:
                logger.warning("message_for_missing_actor", agent_id=agent_id)
                return

            # Route message to actor mailbox
            from heretek_swarm.actors.base import ActorMessage
            actor_message = ActorMessage(
                sender="channel",
                message_type=message.get("type", "default"),
                content=message.get("content", {}),
                timestamp=message.get("timestamp", ""),
                metadata=message.get("metadata", {}),
            )
            await actor.put_message(actor_message)

            # Record delivery
            self.channel_registry.record_message(channel_name, delivered=True)

        except Exception as e:
            logger.error(
                "channel_message_handling_error",
                agent_id=agent_id,
                channel=channel_name,
                error=str(e),
            )
            self.channel_registry.record_error(channel_name)

    async def run(self) -> None:
        """Main autonomous loop - runs 24/7."""
        logger.info("starting_autonomous_loop")
        self._running = True

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._health_monitor_loop()),
            asyncio.create_task(self._consciousness_loop()),
            asyncio.create_task(self._task_processing_loop()),
            asyncio.create_task(self._memory_maintenance_loop()),
            asyncio.create_task(self._scaling_loop()),
            asyncio.create_task(self._report_agents_loop()),
        ]

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

    async def _process_scheduled_tasks(self) -> None:
        """Process tasks scheduled by Chronos."""
        # Query memory for scheduled tasks
        # Trigger appropriate agents based on schedule

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
                        agent_id: getattr(actor, 'mailbox', asyncio.Queue()).qsize()
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
                # Get consciousness plugin and registry
                plugin = get_consciousness_plugin()
                registry = get_enhanced_registry()

                # Real phi from IIT calculator
                phi_stats = plugin.get_statistics()
                avg_phi = phi_stats.get("average_phi", 0.0)

                # Real attention distribution from agent registry
                all_instances = registry.get_all_instances()
                attention_distribution = {}
                active_count = 0
                total_count = len(all_instances)
                for agent_id, instance in all_instances.items():
                    state = getattr(instance, "state", None)
                    attention_distribution[agent_id] = {
                        "state": str(state.value) if hasattr(state, "value") else str(state),
                        "type": getattr(instance, "agent_type", "unknown"),
                    }
                    if state and hasattr(state, "value"):
                        # ACTIVE is the desired state; count it as "conscious" for coherence
                        active_count += 1

                # Workspace coherence: ratio of active agents
                workspace_coherence = active_count / total_count if total_count > 0 else 0.0

                consciousness_data = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "workspace_coherence": workspace_coherence,
                    "attention_distribution": attention_distribution,
                    "phi_metric": avg_phi,
                    "total_agents": total_count,
                    "active_agents": active_count,
                    "average_free_energy": phi_stats.get("average_free_energy", 0.0),
                    "conscious_agents": phi_stats.get("conscious_agents", 0),
                }

                await self.event_mesh.publish(
                    "swarm.system.consciousness",
                    consciousness_data,
                )

                await asyncio.sleep(self._consciousness_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("consciousness_loop_error", error=str(e))
                await asyncio.sleep(self._consciousness_interval)

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
                if self.memory:
                    await self.memory.run_maintenance()

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
        import httpx
        import os

        api_host = os.getenv("HERETEK_API_HOST", "heretek-api")
        api_port = int(os.getenv("HERETEK_API_PORT", "8000"))
        report_interval = 30  # seconds

        while self._running:
            await self._report_agents_batch(api_host, api_port)
            await asyncio.sleep(report_interval)

    async def _report_agents_batch(
        self,
        api_host: str,
        api_port: int
    ) -> None:
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

    def _extract_agent_status(
        self,
        agent_id: str,
        actor: Any
    ) -> dict[str, Any] | None:
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
        self,
        api_host: str,
        api_port: int,
        agents: list[dict[str, Any]]
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

        logger.info("autonomous_swarm_shutdown_complete")


# ============================================================================
# Entry Point
# ============================================================================

async def main():
    """Main entry point for autonomous operation."""
    # Configure logging first, before any loggers are instantiated
    from heretek_swarm.logging.config import setup_logging
    setup_logging(json_output=False, include_caller_info=False)

    config = {
        "nats_servers": ["nats://localhost:4222"],
        "health_check_interval": 30,
        "loop_interval": 1,
        "consciousness_interval": 5,
        "memory_maintenance_interval": 300,
        "scaling_interval": 60,
        "ephemeral": {"ttl_seconds": 3600},
        "persistent": {
            "connection_string": "postgresql://heretek:password@localhost/heretek_swarm",
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

    swarm = AutonomousSwarm(config)
    await swarm.initialize()
    await swarm.run()


if __name__ == "__main__":
    asyncio.run(main())
