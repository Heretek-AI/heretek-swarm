#!/usr/bin/env python3
"""
Session 44: Agent Wiring Script

This script wires all remaining agents with collective learning, consensus, and memory optimization.
It applies a standard integration pattern to each agent file.

Agents to wire:
1. chronos.py
2. coder.py
3. coordinator.py
4. dreamer.py
5. echo.py
6. empath.py
7. examiner.py
8. explorer.py
9. habit_forge.py
10. handoff.py
11. historian.py
12. metis.py
13. nexus.py
14. perceiver.py
15. perceiver_plus.py
16. prism.py
"""

import re
from pathlib import Path

# Base directory for actors
ACTORS_DIR = Path("src/heretek_swarm/actors")

# Standard imports to add
SESSION_44_IMPORTS = """
# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine, Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator
"""

# Standard __init__ parameters to add
SESSION_44_INIT_PARAMS = """
        # Session 44: Integration components
        pattern_extractor: Optional[PatternExtractor] = None,
        deliberation_engine: Optional[SwarmDeliberationEngine] = None,
        access_analyzer: Optional[AccessPatternAnalyzer] = None,
        zero_trust_validator: Optional[ZeroTrustValidator] = None,
"""

# Standard __init__ body to add
SESSION_44_INIT_BODY = """
        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)

        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )

        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()

        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()

        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()
"""

# Standard integration methods to add at end of class
SESSION_44_METHODS = '''
    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: Dict[str, Any]) -> None:
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
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: Optional[List[PatternType]] = None) -> List[Dict[str, Any]]:
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
        participating_agents: List[str],
        domain: str = "general",
    ) -> Optional[str]:
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

    async def _finalize_deliberation(self, item_id: str) -> Optional[Any]:
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

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> List[str]:
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

'''


def wire_agent_file(filepath: Path) -> bool:
    """Apply Session 44 wiring to an agent file."""
    if not filepath.exists():
        return False

    content = filepath.read_text()
    original_content = content

    # 1. Add imports after existing imports
    if "Session 44: Collective Learning Integration" not in content:
        # Find the last import line
        lines = content.split("\n")
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith(("from ", "import ")):
                insert_idx = i + 1

        lines.insert(insert_idx, SESSION_44_IMPORTS)
        content = "\n".join(lines)

    # 2. Add __init__ parameters
    if "pattern_extractor: Optional[PatternExtractor]" not in content:
        # Find __init__ method and add parameters
        init_pattern = r"(def __init__\([^)]*config: Optional\[Dict\[str, Any\]\] = None,)"
        match = re.search(init_pattern, content)
        if match:
            insert_pos = match.end()
            # Find the closing parenthesis
            paren_count = 1
            i = insert_pos
            while i < len(content) and paren_count > 0:
                if content[i] == "(":
                    paren_count += 1
                elif content[i] == ")":
                    paren_count -= 1
                i += 1

            # Insert before closing parenthesis
            content = content[:i-1] + SESSION_44_INIT_PARAMS + content[i-1:]

    # 3. Add __init__ body
    if "Session 44: Collective Learning Integration" in content and "self.pattern_extractor = pattern_extractor" not in content:
        # Find logger.info call after __init__ body starts and add before it
        init_body_pattern = r"(logger\.info\([^)]*initialized[^)]*\))"
        match = re.search(init_body_pattern, content, re.IGNORECASE)
        if match:
            insert_pos = match.start()
            content = content[:insert_pos] + SESSION_44_INIT_BODY + "\n\n        " + content[insert_pos:]

    # 4. Add integration methods at end of class (before last method)
    if "Session 44: Collective Learning Integration Methods" not in content:
        # Find the last method in the class and add after it
        # Look for the last async def or def pattern
        method_pattern = r"(    async def|    def)"
        matches = list(re.finditer(method_pattern, content))

        if matches:
            # Find a good insertion point - look for _send_error or similar utility method
            insert_pos = matches[-1].start()

            # Try to find a better insertion point
            for match in reversed(matches):
                if "_send_error" in content[match.start():match.start()+200]:
                    insert_pos = match.start()
                    break

            content = content[:insert_pos] + SESSION_44_METHODS + "\n" + content[insert_pos:]

    # Write the modified content
    if content != original_content:
        filepath.write_text(content)
        return True

    return False


def main():
    """Main entry point."""
    agents_to_wire = [
        "chronos.py",
        "coder.py",
        "coordinator.py",
        "dreamer.py",
        "echo.py",
        "empath.py",
        "examiner.py",
        "explorer.py",
        "habit_forge.py",
        "handoff.py",
        "historian.py",
        "metis.py",
        "nexus.py",
        "perceiver.py",
        "perceiver_plus.py",
        "prism.py",
    ]


    wired_count = 0
    for agent_file in agents_to_wire:
        filepath = ACTORS_DIR / agent_file

        if wire_agent_file(filepath):
            wired_count += 1
        else:
            pass



if __name__ == "__main__":
    main()
