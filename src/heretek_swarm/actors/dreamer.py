"""
Dreamer Agent - Creative Solution Generation & Divergent Thinking.

The Dreamer provides:
- Novel solution generation through divergent thinking
- Creative problem-solving and ideation
- Alternative perspective exploration
- Innovation and breakthrough ideas
- Scenario imagination and visualization
- Pattern breaking and lateral thinking

Dreamer is the "creative engine" of the Collective, generating novel
solutions that other agents might not consider through conventional analysis.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog

from heretek_swarm.actors.base import ActorMessage, AgentActor
from heretek_swarm.actors.mixins import DeliberationMixin, LearningMixin, MemoryMixin, PatternMixin
from heretek_swarm.actors.validation import validate_message

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator

logger = structlog.get_logger("DreamerAgent")


class CreativityTechnique(StrEnum):
    """Creative thinking techniques Dreamer employs."""
    BRAINSTORMING = "brainstorming"
    MIND_MAPPING = "mind_mapping"
    SCAMPER = "scamper"  # Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse
    SIX_THINKING_HATS = "six_thinking_hats"
    TRIZ = "triz"  # Theory of Inventive Problem Solving
    LATERAL_THINKING = "lateral_thinking"
    ANALOGICAL_THINKING = "analogical_thinking"
    FIRST_PRINCIPLES = "first_principles"


class IdeaCategory(StrEnum):
    """Categories of generated ideas."""
    PRODUCT = "product"
    PROCESS = "process"
    ARCHITECTURE = "architecture"
    ALGORITHM = "algorithm"
    USER_EXPERIENCE = "user_experience"
    BUSINESS = "business"
    SECURITY = "security"
    OPTIMIZATION = "optimization"


class NoveltyLevel(StrEnum):
    """Levels of idea novelty."""
    INCREMENTAL = "incremental"  # Small improvement
    SUBSTANTIAL = "substantial"  # Significant enhancement
    BREAKTHROUGH = "breakthrough"  # Paradigm-shifting


@dataclass
class CreativeIdea:
    """Generated creative idea record."""
    id: str
    title: str
    description: str
    category: IdeaCategory
    novelty: NoveltyLevel
    technique_used: CreativityTechnique
    feasibility_score: float  # 0-1 feasibility estimate
    impact_score: float  # 0-1 impact potential
    originality_score: float  # 0-1 originality measure
    generated_at: datetime
    related_to: str | None = None  # Reference to problem/task
    metadata: dict[str, Any] = field(default_factory=dict)
    variations: list[str] = field(default_factory=list)


@dataclass
class CreativeSession:
    """Record of a creative thinking session."""
    id: str
    problem_statement: str
    technique: CreativityTechnique
    ideas_generated: list[str]  # Idea IDs
    started_at: datetime
    completed_at: datetime | None = None
    constraints: list[str] = field(default_factory=list)
    inspiration_sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InnovationReport:
    """Consolidated innovation report."""
    id: str
    generated_at: datetime
    problem_area: str
    ideas: list[CreativeIdea]
    sessions: list[CreativeSession]
    top_recommendations: list[str]
    innovation_score: float  # 0-100 overall innovation potential
    implementation_roadmap: list[dict[str, Any]]
    risks: list[str]
    opportunities: list[str]


class DreamerAgent(DeliberationMixin, PatternMixin, MemoryMixin, LearningMixin, AgentActor):
    """
    Creative Solution Generation & Divergent Thinking Agent.

    Dreamer generates novel solutions through creative thinking techniques,
    providing the Collective with innovative approaches to complex problems.
    """

    def __init__(
        self,
        agent_id: str = "dreamer",
        name: str = "Dreamer",
        description: str = "Creative Solution Generation Specialist",
        swarms_agent=None,
        pattern_extractor=None,
        deliberation_engine=None,
        access_analyzer=None,
        zero_trust_validator=None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            **kwargs,
        )

        # Idea storage
        self._ideas: dict[str, CreativeIdea] = {}
        self._idea_counter = 0
        self.max_ideas = self._config.get("max_ideas", 500)

        # Creative sessions
        self._sessions: dict[str, CreativeSession] = {}
        self._active_sessions: set[str] = set()
        self.max_sessions = self._config.get("max_sessions", 50)

        # Creativity configuration
        self._default_technique = self._config.get("default_technique", CreativityTechnique.BRAINSTORMING)
        self._creativity_temperature = self._config.get("creativity_temperature", 0.8)  # LLM temp
        self._divergence_factor = self._config.get("divergence_factor", 5)  # Ideas per session

        # Inspiration cache
        self._inspiration_cache: list[dict[str, Any]] = []
        self.max_inspiration = self._config.get("max_inspiration", 100)

        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state (required by mixins)
        self._active_deliberations: dict[str, str] = {}
        self._pattern_emitted: set[str] = set()


        logger.info(
            "DreamerAgent initialized",
            agent_id=self.agent_id,
            default_technique=self._default_technique.value,
            creativity_temperature=self._creativity_temperature
        )

    def get_handlers(self) -> dict[str, callable]:
        """Return message handlers for Dreamer agent."""
        return {
            "generate_ideas": self._handle_generate_ideas,
            "start_creative_session": self._handle_start_creative_session,
            "explore_alternatives": self._handle_explore_alternatives,
            "apply_creativity_technique": self._handle_apply_creativity_technique,
            "get_innovation_report": self._handle_get_innovation_report,
            "get_idea_details": self._handle_get_idea_details,
            "combine_ideas": self._handle_combine_ideas,
        }

    async def _handle_generate_ideas(self, message: ActorMessage) -> dict[str, Any] | None:
        """
        Generate creative ideas for a problem.

        Content expected:
        {
            "problem": "Problem statement",
            "constraints": [...],
            "technique": "brainstorming",
            "num_ideas": 10
        }
        """
        try:
            content = validate_message(message.content, "DreamerGenerateIdeas")
            problem = content.get("problem", "")
            constraints = content.get("constraints", [])
            technique = CreativityTechnique(content.get("technique", self._default_technique.value))
            num_ideas = content.get("num_ideas", self._divergence_factor)

            logger.info(
                "Generating ideas",
                problem=problem[:100],
                technique=technique.value,
                num_ideas=num_ideas
            )

            # Generate ideas using specified technique
            ideas = await self._generate_creative_ideas(
                problem=problem,
                constraints=constraints,
                technique=technique,
                num_ideas=num_ideas
            )

            # Store ideas
            stored_ids = []
            for idea in ideas:
                self._idea_counter += 1
                idea.id = f"idea_{self._idea_counter}"
                self._ideas[idea.id] = idea
                stored_ids.append(idea.id)

            # LRU eviction
            if len(self._ideas) > self.max_ideas:
                excess = len(self._ideas) - self.max_ideas
                for _ in range(excess):
                    oldest_id = next(iter(self._ideas))
                    del self._ideas[oldest_id]

            return {
                "status": "success",
                "ideas_generated": len(ideas),
                "idea_ids": stored_ids,
                "technique_used": technique.value,
                "top_idea": {
                    "id": stored_ids[0] if stored_ids else None,
                    "title": ideas[0].title if ideas else None,
                    "novelty": ideas[0].novelty.value if ideas else None
                } if ideas else None
            }

        except Exception as e:
            logger.error("Failed to generate ideas", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_start_creative_session(self, message: ActorMessage) -> dict[str, Any] | None:
        """
        Start a structured creative thinking session.

        Content expected:
        {
            "problem_statement": "The problem to solve",
            "technique": "scamper",
            "constraints": [...],
            "inspiration_sources": [...]
        }
        """
        try:
            content = validate_message(message.content, "DreamerStartCreativeSession")
            problem_statement = content.get("problem_statement", "")
            technique = CreativityTechnique(content.get("technique", self._default_technique.value))
            constraints = content.get("constraints", [])
            inspiration_sources = content.get("inspiration_sources", [])

            session_id = f"session_{uuid.uuid4().hex[:8]}"
            session = CreativeSession(
                id=session_id,
                problem_statement=problem_statement,
                technique=technique,
                ideas_generated=[],
                started_at=datetime.now(UTC),
                constraints=constraints,
                inspiration_sources=inspiration_sources
            )

            self._sessions[session_id] = session
            self._active_sessions.add(session_id)

            # Trim sessions if needed
            if len(self._sessions) > self.max_sessions:
                oldest_id = next(iter(self._sessions))
                del self._sessions[oldest_id]
                self._active_sessions.discard(oldest_id)

            logger.info(
                "Creative session started",
                session_id=session_id,
                technique=technique.value
            )

            return {
                "status": "success",
                "session_id": session_id,
                "technique": technique.value,
                "problem_statement": problem_statement[:100],
                "estimated_duration_minutes": 15
            }

        except Exception as e:
            logger.error("Failed to start creative session", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_explore_alternatives(self, message: ActorMessage) -> dict[str, Any] | None:
        """
        Explore alternative approaches to a solution.

        Content expected:
        {
            "current_solution": "Current approach",
            "domain": "software|business|design",
            "divergence_level": "high"
        }
        """
        try:
            content = validate_message(message.content, "DreamerExploreAlternatives")
            current_solution = content.get("current_solution", "")
            domain = content.get("domain", "general")
            divergence_level = content.get("divergence_level", "medium")

            logger.info(
                "Exploring alternatives",
                current_solution=current_solution[:100],
                domain=domain,
                divergence_level=divergence_level
            )

            # Generate alternatives using analogical thinking
            alternatives = await self._generate_alternatives(
                current_solution=current_solution,
                domain=domain,
                divergence_level=divergence_level
            )

            return {
                "status": "success",
                "current_solution": current_solution[:200],
                "alternatives": alternatives,
                "count": len(alternatives)
            }

        except Exception as e:
            logger.error("Failed to explore alternatives", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_apply_creativity_technique(self, message: ActorMessage) -> dict[str, Any] | None:
        """
        Apply a specific creativity technique to a problem.

        Content expected:
        {
            "problem": "Problem statement",
            "technique": "six_thinking_hats",
            "context": {...}
        }
        """
        try:
            content = validate_message(message.content, "DreamerApplyTechnique")
            problem = content.get("problem", "")
            technique = CreativityTechnique(content.get("technique", self._default_technique.value))
            context = content.get("context", {})

            logger.info(
                "Applying creativity technique",
                technique=technique.value,
                problem=problem[:100]
            )

            # Apply specific technique
            result = await self._apply_technique(
                problem=problem,
                technique=technique,
                context=context
            )

            return {
                "status": "success",
                "technique": technique.value,
                "result": result,
                "insights_count": len(result.get("insights", []))
            }

        except Exception as e:
            logger.error("Failed to apply creativity technique", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_get_innovation_report(self, message: ActorMessage) -> dict[str, Any] | None:
        """
        Get comprehensive innovation report.

        Content expected:
        {
            "problem_area": "area of focus",
            "include_sessions": true,
            "time_range_days": 7
        }
        """
        try:
            content = validate_message(message.content, "DreamerInnovationReport")
            problem_area = content.get("problem_area", "all")
            include_sessions = content.get("include_sessions", True)
            content.get("time_range_days", 7)

            logger.info("Generating innovation report", problem_area=problem_area)

            # Gather ideas
            cutoff = datetime.now(UTC)
            ideas = [
                idea for idea in self._ideas.values()
                if idea.generated_at >= cutoff
            ]

            # Gather sessions
            sessions = list(self._sessions.values()) if include_sessions else []

            # Calculate innovation score
            innovation_score = self._calculate_innovation_score(ideas, sessions)

            # Generate report using LLM
            report_content = await self._generate_innovation_report(
                ideas=ideas,
                sessions=sessions,
                problem_area=problem_area,
                innovation_score=innovation_score
            )

            return {
                "status": "success",
                "report": {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "problem_area": problem_area,
                    "innovation_score": innovation_score,
                    "ideas_count": len(ideas),
                    "sessions_count": len(sessions),
                    "top_recommendations": report_content.get("recommendations", []),
                    "implementation_roadmap": report_content.get("roadmap", []),
                    "risks": report_content.get("risks", []),
                    "opportunities": report_content.get("opportunities", [])
                }
            }

        except Exception as e:
            logger.error("Failed to generate innovation report", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_get_idea_details(self, message: ActorMessage) -> dict[str, Any] | None:
        """
        Get details of a specific idea.

        Content expected:
        {
            "idea_id": "idea_123"
        }
        """
        try:
            content = validate_message(message.content, "DreamerGetIdeaDetails")
            idea_id = content.get("idea_id")

            if not idea_id:
                return {"status": "error", "error": "idea_id required"}

            idea = self._ideas.get(idea_id)
            if not idea:
                return {"status": "error", "error": f"Idea {idea_id} not found"}

            return {
                "status": "success",
                "idea": {
                    "id": idea.id,
                    "title": idea.title,
                    "description": idea.description,
                    "category": idea.category.value,
                    "novelty": idea.novelty.value,
                    "feasibility_score": idea.feasibility_score,
                    "impact_score": idea.impact_score,
                    "originality_score": idea.originality_score,
                    "generated_at": idea.generated_at.isoformat(),
                    "variations": idea.variations
                }
            }

        except Exception as e:
            logger.error("Failed to get idea details", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_combine_ideas(self, message: ActorMessage) -> dict[str, Any] | None:
        """
        Combine multiple ideas into a novel solution.

        Content expected:
        {
            "idea_ids": ["idea_1", "idea_2"],
            "combination_method": "synthesis"
        }
        """
        try:
            content = validate_message(message.content, "DreamerCombineIdeas")
            idea_ids = content.get("idea_ids", [])
            combination_method = content.get("combination_method", "synthesis")

            # Get ideas
            ideas = [self._ideas.get(iid) for iid in idea_ids]
            ideas = [i for i in ideas if i is not None]

            if len(ideas) < 2:
                return {"status": "error", "error": "Need at least 2 valid ideas to combine"}

            logger.info(
                "Combining ideas",
                idea_count=len(ideas),
                method=combination_method
            )

            # Generate combination using LLM
            combined = await self._combine_ideas_llm(
                ideas=ideas,
                method=combination_method
            )

            # Store as new idea
            self._idea_counter += 1
            new_idea = CreativeIdea(
                id=f"idea_{self._idea_counter}",
                title=combined.get("title", "Combined Solution"),
                description=combined.get("description", ""),
                category=IdeaCategory(combined.get("category", "product")),
                novelty=NoveltyLevel.BREAKTHROUGH,
                technique_used=CreativityTechnique.ANALOGICAL_THINKING,
                feasibility_score=combined.get("feasibility", 0.5),
                impact_score=combined.get("impact", 0.8),
                originality_score=combined.get("originality", 0.9),
                generated_at=datetime.now(UTC),
                related_to=", ".join(idea_ids),
                variations=combined.get("variations", [])
            )
            self._ideas[new_idea.id] = new_idea

            return {
                "status": "success",
                "combined_idea_id": new_idea.id,
                "title": new_idea.title,
                "novelty": new_idea.novelty.value,
                "source_ideas": idea_ids
            }

        except Exception as e:
            logger.error("Failed to combine ideas", error=str(e))
            return {"status": "error", "error": str(e)}

    # Internal helper methods

    async def _generate_creative_ideas(
        self,
        problem: str,
        constraints: list[str],
        technique: CreativityTechnique,
        num_ideas: int
    ) -> list[CreativeIdea]:
        """Generate creative ideas using specified technique."""
        try:
            technique_prompt = self._build_technique_prompt(technique)

            prompt = f"""{technique_prompt}

Problem: {problem}

Constraints: {constraints}

Generate {num_ideas} creative ideas. For each idea, provide:
1. Title (concise and descriptive)
2. Description (2-3 sentences)
3. Category (product/process/architecture/algorithm/ux/business/security/optimization)
4. Novelty level (incremental/substantial/breakthrough)
5. Feasibility score (0-1)
6. Impact score (0-1)

Return as JSON array."""

            response = await self.run_with_llm(
                prompt=prompt,
                timeout=60,
                temperature=self._creativity_temperature
            )

            # Parse response
            import json
            try:
                ideas_data = json.loads(response)
                ideas = []
                for data in ideas_data[:num_ideas]:
                    idea = CreativeIdea(
                        id="",  # Will be assigned later
                        title=data.get("title", "Untitled Idea"),
                        description=data.get("description", ""),
                        category=IdeaCategory(data.get("category", "product")),
                        novelty=NoveltyLevel(data.get("novelty", "incremental")),
                        technique_used=technique,
                        feasibility_score=float(data.get("feasibility", 0.5)),
                        impact_score=float(data.get("impact", 0.5)),
                        originality_score=float(data.get("originality", 0.5)),
                        generated_at=datetime.now(UTC)
                    )
                    ideas.append(idea)
                return ideas
            except Exception as e:
                logger.debug("dreamer_ideas_parse_failed_617", error=str(e))
                return [
                    CreativeIdea(
                        id="",
                        title=f"Creative Solution {i+1}",
                        description=f"Novel approach to: {problem[:50]}",
                        category=IdeaCategory.PROCESS,
                        novelty=NoveltyLevel.SUBSTANTIAL,
                        technique_used=technique,
                        feasibility_score=0.6,
                        impact_score=0.7,
                        originality_score=0.7,
                        generated_at=datetime.now(UTC)
                    )
                    for i in range(num_ideas)
                ]

        except Exception as e:
            logger.error("Failed to generate ideas", error=str(e))
            return []

    def _build_technique_prompt(self, technique: CreativityTechnique) -> str:
        """Build prompt for specific creativity technique."""
        prompts = {
            CreativityTechnique.BRAINSTORMING: "Generate diverse ideas through free-flowing brainstorming. Quantity over quality initially.",
            CreativityTechnique.MIND_MAPPING: "Create ideas by mapping related concepts and exploring branches.",
            CreativityTechnique.SCAMPER: "Apply SCAMPER technique: Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse.",
            CreativityTechnique.SIX_THINKING_HATS: "Apply Six Thinking Hats: White (facts), Red (emotions), Black (caution), Yellow (optimism), Green (creativity), Blue (process).",
            CreativityTechnique.TRIZ: "Apply TRIZ principles to resolve contradictions and find inventive solutions.",
            CreativityTechnique.LATERAL_THINKING: "Use lateral thinking to approach the problem from unexpected angles.",
            CreativityTechnique.ANALOGICAL_THINKING: "Draw analogies from unrelated domains to inspire solutions.",
            CreativityTechnique.FIRST_PRINCIPLES: "Break down to first principles and rebuild from fundamental truths."
        }
        return prompts.get(technique, "Generate creative ideas.")

    async def _generate_alternatives(
        self,
        current_solution: str,
        domain: str,
        divergence_level: str
    ) -> list[dict[str, Any]]:
        """Generate alternative approaches using analogical thinking."""
        try:
            temperature_map = {"low": 0.5, "medium": 0.7, "high": 0.9}
            temperature = temperature_map.get(divergence_level, 0.7)

            prompt = f"""Current solution: {current_solution}
Domain: {domain}

Generate 5 alternative approaches that are fundamentally different from the current solution.
Consider approaches from other domains, reverse assumptions, or radical simplifications.

For each alternative, provide:
1. Name
2. Core concept
3. Key difference from current
4. Potential advantage
5. Trade-off

Return as JSON array."""

            response = await self.run_with_llm(
                prompt=prompt,
                timeout=60,
                temperature=temperature
            )

            import json
            try:
                return json.loads(response)
            except Exception as e:
                logger.debug("dreamer_alternatives_parse_failed_688", error=str(e))
                return [{"name": f"Alternative {i+1}", "concept": "Different approach"} for i in range(5)]

        except Exception as e:
            logger.error("Failed to generate alternatives", error=str(e))
            return []

    async def _apply_technique(
        self,
        problem: str,
        technique: CreativityTechnique,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply specific creativity technique."""
        technique_prompts = {
            CreativityTechnique.SIX_THINKING_HATS: self._apply_six_hats,
            CreativityTechnique.SCAMPER: self._apply_scamper,
            CreativityTechnique.FIRST_PRINCIPLES: self._apply_first_principles,
        }

        handler = technique_prompts.get(technique)
        if handler:
            return await handler(problem, context)

        # Default: generic technique application
        return await self._apply_generic_technique(problem, technique, context)

    async def _apply_six_hats(self, problem: str, context: dict[str, Any]) -> dict[str, Any]:
        """Apply Six Thinking Hats technique."""
        hats = [
            ("White", "facts", "What do we know? What information is available?"),
            ("Red", "emotions", "What are the intuitions and feelings?"),
            ("Black", "caution", "What are the risks and problems?"),
            ("Yellow", "optimism", "What are the benefits and value?"),
            ("Green", "creativity", "What are the creative alternatives?"),
            ("Blue", "process", "What is the summary and next steps?")
        ]

        insights = []
        for hat_name, hat_type, question in hats:
            prompt = f"""Six Thinking Hats - {hat_name} Hat ({hat_type})

Problem: {problem}
{question}

Provide insights from this perspective."""

            try:
                response = await self.run_with_llm(prompt=prompt, timeout=30, temperature=0.4)
                insights.append({"hat": hat_name, "type": hat_type, "insight": response.strip()})
            except Exception as e:
                logger.debug("dreamer_hat_insight_failed", hat=hat_name, error=str(e))
                insights.append({"hat": hat_name, "type": hat_type, "insight": "Unable to generate"})

        return {"technique": "six_thinking_hats", "insights": insights}

    async def _apply_scamper(self, problem: str, context: dict[str, Any]) -> dict[str, Any]:
        """Apply SCAMPER technique."""
        scamper_prompts = {
            "Substitute": "What can be substituted or replaced?",
            "Combine": "What can be combined or merged?",
            "Adapt": "What can be adapted or adjusted?",
            "Modify": "What can be modified or magnified?",
            "Put to other use": "How can this be used differently?",
            "Eliminate": "What can be eliminated or simplified?",
            "Reverse": "What can be reversed or rearranged?"
        }

        insights = []
        for letter, question in scamper_prompts.items():
            prompt = f"""SCAMPER Technique - {letter}

Problem: {problem}
{question}

Generate ideas using this SCAMPER prompt."""

            try:
                response = await self.run_with_llm(prompt=prompt, timeout=30, temperature=0.7)
                insights.append({"letter": letter, "prompt": question, "ideas": response.strip()})
            except Exception as e:
                logger.debug("dreamer_scamper_insight_failed", letter=letter, error=str(e))
                insights.append({"letter": letter, "prompt": question, "ideas": "Unable to generate"})

        return {"technique": "scamper", "insights": insights}

    async def _apply_first_principles(self, problem: str, context: dict[str, Any]) -> dict[str, Any]:
        """Apply First Principles thinking."""
        prompt = f"""First Principles Analysis

Problem: {problem}

1. Identify all assumptions about this problem
2. Break down to fundamental truths (what we know is definitely true)
3. Rebuild solution from first principles

Provide a structured analysis."""

        try:
            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.3)
            return {"technique": "first_principles", "analysis": response.strip()}
        except Exception as e:
            logger.debug("dreamer_first_principles_failed", error=str(e))
            return {"technique": "first_principles", "analysis": "Unable to complete analysis"}

    async def _apply_generic_technique(self, problem: str, technique: CreativityTechnique, context: dict[str, Any]) -> dict[str, Any]:
        """Generic technique application."""
        prompt = f"""Apply {technique.value} technique to:

Problem: {problem}

Generate insights and ideas."""

        try:
            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.7)
            return {"technique": technique.value, "insights": [response.strip()]}
        except Exception as e:
            logger.debug("dreamer_generic_technique_failed", technique=technique.value, error=str(e))
            return {"technique": technique.value, "insights": []}

    def _calculate_innovation_score(self, ideas: list[CreativeIdea], sessions: list[CreativeSession]) -> float:
        """Calculate overall innovation score."""
        if not ideas and not sessions:
            return 0.0

        scores = []

        # Idea quality score
        if ideas:
            avg_originality = sum(i.originality_score for i in ideas) / len(ideas)
            avg_impact = sum(i.impact_score for i in ideas) / len(ideas)
            breakthrough_count = len([i for i in ideas if i.novelty == NoveltyLevel.BREAKTHROUGH])

            idea_score = (avg_originality * 0.4 + avg_impact * 0.4 + min(breakthrough_count / 5, 1) * 0.2) * 100
            scores.append(idea_score)

        # Session activity score
        if sessions:
            session_score = min(len(sessions) / 10, 1) * 100
            scores.append(session_score)

        return sum(scores) / len(scores) if scores else 0.0

    async def _generate_innovation_report(
        self,
        ideas: list[CreativeIdea],
        sessions: list[CreativeSession],
        problem_area: str,
        innovation_score: float
    ) -> dict[str, Any]:
        """Generate innovation report using LLM."""
        try:
            ideas_summary = "\n".join([f"- {i.title} ({i.novelty.value})" for i in ideas[:10]])

            prompt = f"""Innovation Report for: {problem_area}

Innovation Score: {innovation_score:.1f}/100
Ideas Generated: {len(ideas)}
Creative Sessions: {len(sessions)}

Top Ideas:
{ideas_summary}

Provide:
1. Top 3 recommendations
2. Implementation roadmap (3-5 steps)
3. Key risks
4. Key opportunities

Return as JSON with keys: recommendations, roadmap, risks, opportunities"""

            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.3)

            import json
            try:
                return json.loads(response)
            except Exception as e:
                logger.debug("dreamer_innovation_report_parse_failed_860", error=str(e))
                return {
                    "recommendations": ["Continue innovation efforts", "Prioritize breakthrough ideas"],
                    "roadmap": [{"step": 1, "action": "Review top ideas"}, {"step": 2, "action": "Select for implementation"}],
                    "risks": ["Implementation complexity"],
                    "opportunities": ["Breakthrough potential"]
                }
        except Exception as e:
            logger.debug("dreamer_innovation_report_llm_failed", error=str(e))
            return {"recommendations": [], "roadmap": [], "risks": [], "opportunities": []}


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return

        if item_id in self._pattern_emitted:
            return

        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"{item_type}_{item_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type=f"{item_type}_completion",
                content=content,
                timestamp=datetime.now(UTC).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: list[PatternType] | None = None) -> list[dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []

        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: list[str],
        domain: str = "general",
    ) -> str | None:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None

        try:
            deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=proposal[:200],
                participants=participating_agents,
                domain=domain,
            )
            self._active_deliberations[item_id] = deliberation_id

            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False

        try:
            success = self.deliberation_engine.submit_position(
                deliberation_id=deliberation_id,
                agent_id=agent_id,
                position=position,
                confidence=confidence,
                argument=argument,
            )

            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=f"delib_{deliberation_id}_{agent_id}",
                    access_type="write",
                    agent_id=agent_id,
                )

            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Any | None:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None

        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None

        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)

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

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str = "read") -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return

        memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD

        memory_id = f"{item_type}_{item_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> list[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []

        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> dict[str, Any]:
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


    async def _combine_ideas_llm(self, ideas: list[CreativeIdea], method: str) -> dict[str, Any]:
        """Combine ideas using LLM."""
        try:
            ideas_text = "\n\n".join([f"{i.title}: {i.description}" for i in ideas])

            prompt = f"""Combine these ideas into a novel solution using {method}:

{ideas_text}

Provide:
1. Combined solution title
2. Description
3. Category
4. Feasibility (0-1)
5. Impact (0-1)
6. Originality (0-1)
7. Variations (2-3 alternative implementations)

Return as JSON."""

            response = await self.run_with_llm(prompt=prompt, timeout=60, temperature=0.8)

            import json
            try:
                return json.loads(response)
            except Exception as e:
                logger.debug("dreamer_synthesis_parse_failed_1087", error=str(e))
                return {
                    "title": "Combined Solution",
                    "description": "Synthesis of multiple ideas",
                    "category": "product",
                    "feasibility": 0.5,
                    "impact": 0.7,
                    "originality": 0.8,
                    "variations": []
                }
        except Exception as e:
            logger.debug("dreamer_synthesis_llm_failed", error=str(e))
            return {}
