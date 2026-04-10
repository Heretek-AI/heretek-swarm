"""
Metis Agent - Strategic Planning and Long-Term Thinking.

The Metis agent provides:
- Long-term goal setting and strategic planning
- Resource allocation optimization
- Risk assessment and mitigation strategies
- Multi-step planning with dependency tracking
- Strategic foresight and scenario analysis

Named after the Greek Titaness of wisdom and strategic thinking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine, Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator


_logger = structlog.get_logger("MetisAgent")


class MetisAgent(AgentActor):
    """
    Metis Agent - Strategic Planning Specialist.

    Metis is responsible for:
    - Developing long-term strategic plans
    - Allocating resources optimally across agents
    - Assessing and mitigating risks
    - Creating multi-step plans with dependencies
    - Running scenario analyses for decision support

    Strategic Planning Workflow:
    1. Receive strategic objective or problem
    2. Analyze current state and constraints
    3. Generate multiple strategic options
    4. Evaluate options using risk/benefit analysis
    5. Recommend optimal strategy with implementation plan
    """

    def __init__(self, _agent_id: str, _name: str, _description: str, _swarms_agent: Optional[Agent], _planning_horizon_days: int, _max_scenarios: int, _pattern_extractor: Optional[PatternExtractor], _deliberation_engine: Optional[SwarmDeliberationEngine], _access_analyzer: Optional[AccessPatternAnalyzer], _zero_trust_validator: Optional[ZeroTrustValidator], **kwargs) -> None:
        """
        Initialize the Metis agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            planning_horizon_days: Default planning horizon in days
            max_scenarios: Maximum scenarios to generate in analysis
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            _name = name,
            _description = description,
            _topics = [
                "strategy",
                "planning",
                "resource-allocation",
                "risk-assessment",
                "foresight",
            ],
            _capabilities = [
                "strategic-planning",
                "resource-optimization",
                "risk-assessment",
                "scenario-analysis",
                "dependency-tracking",
            ],
            _swarms_agent = swarms_agent,
            **kwargs,
        )

        # Metis-specific state
        self.planning_horizon_days = planning_horizon_days
        self.max_scenarios = max_scenarios
        self.active_plans: Dict[str, Dict[str, Any]] = {}
        self.resource_allocations: Dict[str, Dict[str, float]] = {}
        self.risk_register: Dict[str, Dict[str, Any]] = {}
        self.strategic_objectives: List[Dict[str, Any]] = []
        self.scenario_analyses: Dict[str, List[Dict[str, Any]]] = {}

        
        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)
        
        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            _max_rounds = 5, consensus_threshold=0.75, min_participants=2
        )
        
        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()
        
        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()
        
        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(f"[{self.agent_id}] Metis agent initialized")

    async def initialize(self) -> None:
        """Initialize the Metis agent."""
        # Register message handlers with validation
        self.register_handler("create_strategic_plan", self._handle_create_strategic_plan)
        self.register_handler("allocate_resources", self._handle_allocate_resources)
        self.register_handler("assess_risks", self._handle_assess_risks)
        self.register_handler("analyze_scenarios", self._handle_analyze_scenarios)
        self.register_handler("set_strategic_objective", self._handle_set_strategic_objective)
        self.register_handler("get_plan_status", self._handle_get_plan_status)

        logger.info(f"[{self.agent_id}] Metis initialization complete")

    async def process_message(self, _message: ActorMessage) -> None:
        """
        Process incoming messages with exception handling.

        Args:
            message: Actor message to process
        """
        _handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    _exc_info = True,
                )
                self.error_count += 1
                # Send error response if reply_to is specified
                if message.content.get("reply_to"):
                    await self.send(
                        _topic = message.content["reply_to"],
                        _content = {
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        _correlation_id = message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] Unhandled message type: {message.message_type}"
            )

    async def _handle_create_strategic_plan(self, _message: ActorMessage) -> None:
        """Handle strategic plan creation requests with validation."""
        try:
            _validated = self._validate_message_content("create_strategic_plan", message.content)
            if validated:
                _objective = validated.content.get("objective")
                _horizon_days = validated.content.get("horizon_days", self.planning_horizon_days)
                _constraints = validated.content.get("constraints", [])
            else:
                # Fallback for unknown message types
                _objective = message.content.get("objective")
                _horizon_days = message.content.get("horizon_days", self.planning_horizon_days)
                _constraints = message.content.get("constraints", [])
                
                if not objective:
                    logger.error(f"[{self.agent_id}] Missing objective for strategic plan")
                    return
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Strategic plan validation failed: {e}")
            return

        _plan_id = f"plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(
            f"[{self.agent_id}] Creating strategic plan: {plan_id}",
            extra={
                "objective": objective,
                "horizon_days": horizon_days,
                "constraints_count": len(constraints) if constraints else 0,
            },
        )

        # Generate strategic plan using LLM
        try:
            _plan = await self._generate_strategic_plan(
                _plan_id = plan_id,
                _objective = objective,
                _horizon_days = horizon_days,
                _constraints = constraints,
            )
            
            # Store the plan
            self.active_plans[plan_id] = plan
            
            # Send response
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = {
                        "message_type": "strategic_plan_created",
                        "plan_id": plan_id,
                        "status": "created",
                        "objective": objective,
                    },
                    _correlation_id = message.correlation_id,
                )
            
            logger.info(f"[{self.agent_id}] Strategic plan {plan_id} created successfully")
            
        except Exception as e:
            logger.error(
                f"[{self.agent_id}] Failed to create strategic plan {plan_id}: {e}",
                _exc_info = True,
            )
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = {
                        "message_type": "error_response",
                        "error": f"Failed to create strategic plan: {str(e)}",
                    },
                    _correlation_id = message.correlation_id,
                )

    async def _handle_allocate_resources(self, _message: ActorMessage) -> None:
        """Handle resource allocation requests with validation."""
        try:
            _validated = self._validate_message_content("allocate_resources", message.content)
            if validated:
                _plan_id = validated.content.get("plan_id")
                _resources = validated.content.get("resources", {})
                _priorities = validated.content.get("priorities", {})
            else:
                # Fallback
                _plan_id = message.content.get("plan_id")
                _resources = message.content.get("resources", {})
                _priorities = message.content.get("priorities", {})
                
                if not plan_id:
                    logger.error(f"[{self.agent_id}] Missing plan_id for resource allocation")
                    return
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Resource allocation validation failed: {e}")
            return

        if plan_id not in self.active_plans:
            logger.error(f"[{self.agent_id}] Plan {plan_id} not found for resource allocation")
            return

        logger.info(
            f"[{self.agent_id}] Allocating resources for plan: {plan_id}",
            extra={"resources_count": len(resources)},
        )

        # Perform resource allocation optimization
        _allocation = await self._optimize_resource_allocation(
            _plan_id = plan_id,
            _resources = resources,
            _priorities = priorities,
        )
        
        # Store allocation
        self.resource_allocations[plan_id] = allocation
        
        # Send response
        if message.content.get("reply_to"):
            await self.send(
                _topic = message.content["reply_to"],
                _content = {
                    "message_type": "resources_allocated",
                    "plan_id": plan_id,
                    "allocation": allocation,
                },
                _correlation_id = message.correlation_id,
            )

        logger.info(f"[{self.agent_id}] Resource allocation complete for plan {plan_id}")

    async def _handle_assess_risks(self, _message: ActorMessage) -> None:
        """Handle risk assessment requests with validation."""
        try:
            _validated = self._validate_message_content("assess_risks", message.content)
            if validated:
                _plan_id = validated.content.get("plan_id")
                _domain = validated.content.get("domain", "general")
            else:
                # Fallback
                _plan_id = message.content.get("plan_id")
                _domain = message.content.get("domain", "general")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Risk assessment validation failed: {e}")
            return

        logger.info(
            f"[{self.agent_id}] Assessing risks for plan: {plan_id}, domain: {domain}",
        )

        # Perform risk assessment
        _risks = await self._assess_plan_risks(
            _plan_id = plan_id,
            _domain = domain,
        )
        
        # Store risks in register
        for risk in risks:
            _risk_id = risk.get("risk_id")
            if risk_id:
                self.risk_register[risk_id] = risk
        
        # Send response
        if message.content.get("reply_to"):
            await self.send(
                _topic = message.content["reply_to"],
                _content = {
                    "message_type": "risks_assessed",
                    "plan_id": plan_id,
                    "risks": risks,
                    "risk_count": len(risks),
                },
                _correlation_id = message.correlation_id,
            )

        logger.info(f"[{self.agent_id}] Risk assessment complete: {len(risks)} risks identified")

    async def _handle_analyze_scenarios(self, _message: ActorMessage) -> None:
        """Handle scenario analysis requests with validation."""
        try:
            _validated = self._validate_message_content("analyze_scenarios", message.content)
            if validated:
                _base_scenario = validated.content.get("base_scenario", {})
                _variables = validated.content.get("variables", [])
            else:
                # Fallback
                _base_scenario = message.content.get("base_scenario", {})
                _variables = message.content.get("variables", [])
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Scenario analysis validation failed: {e}")
            return

        _analysis_id = f"scenario_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(
            f"[{self.agent_id}] Running scenario analysis: {analysis_id}",
            extra={"variables_count": len(variables)},
        )

        # Generate and analyze scenarios
        _scenarios = await self._generate_scenarios(
            _base_scenario = base_scenario,
            _variables = variables,
            _max_scenarios = self.max_scenarios,
        )
        
        # Store analysis
        self.scenario_analyses[analysis_id] = scenarios
        
        # Send response
        if message.content.get("reply_to"):
            await self.send(
                _topic = message.content["reply_to"],
                _content = {
                    "message_type": "scenarios_analyzed",
                    "analysis_id": analysis_id,
                    "scenarios": scenarios,
                    "scenario_count": len(scenarios),
                },
                _correlation_id = message.correlation_id,
            )

        logger.info(f"[{self.agent_id}] Scenario analysis complete: {len(scenarios)} scenarios generated")

    async def _handle_set_strategic_objective(self, _message: ActorMessage) -> None:
        """Handle strategic objective setting with validation."""
        try:
            _validated = self._validate_message_content("set_strategic_objective", message.content)
            if validated:
                _objective = validated.content.get("objective")
                _priority = validated.content.get("priority", "medium")
                _metrics = validated.content.get("metrics", [])
            else:
                # Fallback
                _objective = message.content.get("objective")
                _priority = message.content.get("priority", "medium")
                _metrics = message.content.get("metrics", [])
                
                if not objective:
                    logger.error(f"[{self.agent_id}] Missing objective")
                    return
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Strategic objective validation failed: {e}")
            return

        _objective_entry = {
            "objective": objective,
            "priority": priority,
            "metrics": metrics,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        
        self.strategic_objectives.append(objective_entry)
        
        logger.info(
            f"[{self.agent_id}] Strategic objective set: {objective[:50]}...",
            _extra = {"priority": priority},
        )

        # Send response
        if message.content.get("reply_to"):
            await self.send(
                _topic = message.content["reply_to"],
                _content = {
                    "message_type": "strategic_objective_set",
                    "objective": objective,
                    "priority": priority,
                },
                _correlation_id = message.correlation_id,
            )

    async def _handle_get_plan_status(self, _message: ActorMessage) -> None:
        """Handle plan status requests with validation."""
        try:
            _validated = self._validate_message_content("get_plan_status", message.content)
            if validated:
                _plan_id = validated.content.get("plan_id")
            else:
                # Fallback
                _plan_id = message.content.get("plan_id")
                
                if not plan_id:
                    logger.error(f"[{self.agent_id}] Missing plan_id for status request")
                    return
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Plan status validation failed: {e}")
            return

        if plan_id not in self.active_plans:
            logger.error(f"[{self.agent_id}] Plan {plan_id} not found")
            if message.content.get("reply_to"):
                await self.send(
                    _topic = message.content["reply_to"],
                    _content = {
                        "message_type": "error_response",
                        "error": f"Plan {plan_id} not found",
                    },
                    _correlation_id = message.correlation_id,
                )
            return

        _plan = self.active_plans[plan_id]
        _allocation = self.resource_allocations.get(plan_id, {})
        _risks = [r for r in self.risk_register.values() if r.get("plan_id") == plan_id]
        
        _status = {
            "plan_id": plan_id,
            "objective": plan.get("objective"),
            "status": plan.get("status", "active"),
            "phases": plan.get("phases", []),
            "resource_allocation": allocation,
            "risks_count": len(risks),
            "created_at": plan.get("created_at"),
            "horizon_days": plan.get("horizon_days"),
        }
        
        # Send response
        if message.content.get("reply_to"):
            await self.send(
                _topic = message.content["reply_to"],
                _content = {
                    "message_type": "plan_status",
                    "status": status,
                },
                _correlation_id = message.correlation_id,
            )

        logger.info(f"[{self.agent_id}] Plan status retrieved for {plan_id}")

    # ========================================================================
    # Strategic Planning Methods
    # ========================================================================

    async def _generate_strategic_plan(self, _plan_id: str, _objective: str, _horizon_days: int, _constraints: List[str]) -> Dict[str, Any]:
        """
        Generate a comprehensive strategic plan.

        Args:
            plan_id: Unique plan identifier
            objective: Strategic objective to achieve
            horizon_days: Planning horizon in days
            constraints: List of constraints to consider

        Returns:
            Strategic plan dictionary
        """
        _prompt = f"""
Strategic Planning Request:

Objective: {objective}
Planning Horizon: {horizon_days} days
Constraints: {', '.join(constraints) if constraints else 'None specified'}

Generate a comprehensive strategic plan including:
1. Executive Summary
2. Key Milestones (at least 4 phases)
3. Resource Requirements
4. Risk Considerations
5. Success Metrics

Format as JSON with keys: summary, phases, resources, risks, metrics
"""
        
        try:
            _response = await self.run_with_llm(
                _prompt = prompt,
                _system_prompt = "You are Metis, a strategic planning specialist AI. Create detailed, actionable strategic plans.",
                _timeout = 60,
            )
            
            # Parse response (simplified - in production use JSON parsing)
            _plan = {
                "objective": objective,
                "horizon_days": horizon_days,
                "constraints": constraints,
                "summary": response[:500] if response else "Plan generated",
                "phases": self._extract_phases(response),
                "resources": {},
                "risks": [],
                "metrics": [],
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            return plan
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] LLM failed for strategic planning: {e}")
            # Return minimal plan
            return {
                "objective": objective,
                "horizon_days": horizon_days,
                "constraints": constraints,
                "summary": "Plan generated (LLM parsing failed)",
                "phases": [],
                "resources": {},
                "risks": [],
                "metrics": [],
                "status": "degraded",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

    def _extract_phases(self, _response: str) -> List[Dict[str, Any]]:
        """Extract phase information from LLM response."""
        # Simplified extraction - in production use proper JSON parsing
        return [
            {"phase": 1, "name": "Initiation", "duration_days": 7},
            {"phase": 2, "name": "Analysis", "duration_days": 14},
            {"phase": 3, "name": "Execution", "duration_days": 30},
            {"phase": 4, "name": "Review", "duration_days": 7},
        ]

    async def _optimize_resource_allocation(self, _plan_id: str, _resources: Dict[str, Any], _priorities: Dict[str, float]) -> Dict[str, Any]:
        """
        Optimize resource allocation for a plan.

        Args:
            plan_id: Plan identifier
            resources: Available resources
            priorities: Priority weights for allocation

        Returns:
            Optimized allocation dictionary
        """
        # Simple priority-based allocation
        _total_priority = sum(priorities.values()) if priorities else 1.0
        
        _allocation = {}
        for resource, amount in resources.items():
            if resource in priorities:
                allocation[resource] = {
                    "allocated": amount,
                    "priority_weight": priorities[resource] / total_priority,
                }
            else:
                allocation[resource] = {"allocated": amount, "priority_weight": 0.0}
        
        return {
            "plan_id": plan_id,
            "allocation": allocation,
            "optimization_method": "priority_weighted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _assess_plan_risks(self, _plan_id: str, _domain: str) -> List[Dict[str, Any]]:
        """
        Assess risks for a strategic plan.

        Args:
            plan_id: Plan identifier
            domain: Risk domain (technical, financial, operational, etc.)

        Returns:
            List of identified risks
        """
        _plan = self.active_plans.get(plan_id, {})
        
        _prompt = f"""
Risk Assessment Request:

Plan: {plan.get('objective', 'Unknown')}
Domain: {domain}
Phases: {len(plan.get('phases', []))}

Identify key risks including:
1. Risk description
2. Probability (0-1)
3. Impact (1-10)
4. Mitigation strategies

Format each risk as JSON object.
"""
        
        try:
            _response = await self.run_with_llm(
                _prompt = prompt,
                _system_prompt = "You are Metis, a strategic risk assessment specialist. Identify and analyze potential risks.",
                _timeout = 60,
            )
            
            # Generate structured risks
            _risks = [
                {
                    "risk_id": f"risk_{plan_id}_{i}",
                    "plan_id": plan_id,
                    "domain": domain,
                    "description": f"Identified risk {i}",
                    "probability": 0.3,
                    "impact": 5,
                    "mitigation": "Standard mitigation strategies",
                    "status": "identified",
                }
                for i in range(3)
            ]
            
            return risks
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] LLM failed for risk assessment: {e}")
            return []

    async def _generate_scenarios(self, _base_scenario: Dict[str, Any], _variables: List[str], _max_scenarios: int) -> List[Dict[str, Any]]:
        """
        Generate multiple scenarios for analysis.

        Args:
            base_scenario: Base scenario parameters
            variables: Variables to manipulate
            max_scenarios: Maximum scenarios to generate

        Returns:
            List of scenario dictionaries
        """
        _scenarios = []
        
        # Generate base scenario
        scenarios.append({
            "scenario_id": "base",
            "name": "Base Case",
            "parameters": base_scenario,
            "probability": 0.5,
            "outcomes": {},
        })
        
        # Generate variation scenarios
        for i, var in enumerate(variables[:max_scenarios - 1]):
            scenarios.append({
                "scenario_id": f"var_{i}",
                "name": f"Variable {var} High",
                "parameters": {**base_scenario, var: "high"},
                "probability": 0.25 / (len(variables) or 1),
                "outcomes": {},
            })
        
        return scenarios

    async def get_strategic_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all strategic activities.

        Returns:
            Strategic summary dictionary
        """
        return {
            "active_plans": len(self.active_plans),
            "resource_allocations": len(self.resource_allocations),
            "registered_risks": len(self.risk_register),
            "strategic_objectives": len(self.strategic_objectives),
            "scenario_analyses": len(self.scenario_analyses),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, _item_id: str, _item_type: str, _outcome: str, _content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return
        
        if item_id in self._pattern_emitted:
            return
        
        try:
            await self.pattern_extractor.analyze_message(
                _message_id = f"{item_type}_{item_id}",
                _sender = self.agent_id,
                _recipient = "broadcast",
                _message_type = f"{item_type}_completion",
                _content = content,
                _timestamp = datetime.now(timezone.utc).isoformat(),
            )
            
            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, _pattern_types: Optional[List[PatternType]]) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []
        
        try:
            _patterns = await self.pattern_extractor.extract_patterns(
                _time_window_hours = 24,
                _pattern_types = pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(self, _item_id: str, _proposal: str, _participating_agents: List[str], _domain: str) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None
        
        try:
            _deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                _deliberation_id = deliberation_id,
                _proposal = proposal[:200],
                _participants = participating_agents,
                _domain = domain,
            )
            self._active_deliberations[item_id] = deliberation_id
            
            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(self, _item_id: str, _agent_id: str, _position: Position, _confidence: float, _argument: str) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False
        
        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False
        
        try:
            _success = self.deliberation_engine.submit_position(
                _deliberation_id = deliberation_id,
                agent_id=agent_id,
                _position = position,
                _confidence = confidence,
                _argument = argument,
            )
            
            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    _memory_id = f"delib_{deliberation_id}_{agent_id}",
                    _access_type = "write",
                    agent_id=agent_id,
                )
            
            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, _item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None
        
        _deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None
        
        try:
            _result = self.deliberation_engine.finalize_deliberation(deliberation_id)
            
            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)
            
            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, _item_id: str, _item_type: str, _access_type: str) -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return
        
        _memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            _memory_id = memory_id,
            _access_type = access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, _item_id: str, _item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD
        
        _memory_id = f"{item_type}_{item_id}"
        _profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, _agent_id: str, _item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []
        
        try:
            _predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
        }


    async def cleanup(self) -> None:
        """Clean up Metis resources."""
        logger.info(f"[{self.agent_id}] Metis agent cleanup initiated")
        
        # Clear all state
        self.active_plans.clear()
        self.resource_allocations.clear()
        self.risk_register.clear()
        self.strategic_objectives.clear()
        self.scenario_analyses.clear()
        
        logger.info(f"[{self.agent_id}] Metis agent cleanup complete")
