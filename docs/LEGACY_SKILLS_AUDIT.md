# Legacy Skills Audit Report

**Date:** 2026-04-04  
**Auditor:** Agent Beta (Data Systems and Tooling Lead)  
**Scope:** 46 legacy shell-based skills from heretek-openclaw-core  
**Purpose:** Catalog skills for migration to Python-native Swarms tools

---

## Executive Summary

- **Total Skills:** 46
- **Shell Scripts:** 23 (50%)
- **JavaScript/Node:** 15 (33%)
- **Python:** 8 (17%)
- **Migration Priority:** High (shell scripts), Medium (Node.js), Low (Python)

---

## Skills Inventory

### Category 1: Memory & State Management (8 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `agemem-governance` | JS | Memory governance policies | Medium | Redis-based |
| `archivist` | JS | Long-term memory storage | Medium | PGVector integration |
| `backup-ledger` | Shell | State backup operations | High | Simple shell wrapper |
| `day-dream` | Shell | Memory consolidation | High | Batch processing |
| `dreamer-agent` | Shell | Subconscious processing | High | Background tasks |
| `memory-consolidation` | Python | Memory optimization | Low | Already Python |
| `redis-ttl-manager` | Python | TTL management | Low | Redis native |
| `session-wrap-up` | JS | Session state cleanup | Medium | State transitions |

### Category 2: Governance & Consensus (7 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `auto-deliberation-trigger` | Shell | Trigger deliberation | High | Event-based |
| `constitutional-deliberation` | JS | Constitutional review | Medium | Rule engine |
| `failover-vote` | Shell | Consensus voting | High | BFT protocol |
| `governance-modules` | JS | Governance rules | Medium | Policy engine |
| `quorum-enforcement` | JS | Quorum validation | Medium | Consensus logic |
| `autonomous-pulse` | Shell | Health monitoring | High | Heartbeat system |
| `autonomy-audit` | Shell | Autonomy compliance | High | Audit trail |

### Category 3: Communication & A2A (5 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `a2a-agent-register` | JS | Agent registration | Medium | Registry management |
| `a2a-message-send` | JS | Inter-agent messaging | Medium | Redis pub/sub |
| `cross-tier-correlator` | JS | Message correlation | Medium | Event tracking |
| `gap-detector` | Shell | Communication gaps | High | Pattern detection |
| `healthcheck` | JS | System health checks | Medium | Multi-service checks |

### Category 4: Knowledge & Learning (6 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `curiosity-auto-trigger` | Shell | Curiosity triggers | High | Event detection |
| `curiosity-engine` | Python | Exploration logic | Low | Already Python |
| `knowledge-ingest` | Shell | Knowledge ingestion | High | Data pipeline |
| `knowledge-retrieval` | Shell | Knowledge search | High | Query engine |
| `opportunity-scanner` | Shell | Opportunity detection | High | Pattern matching |
| `self-model` | Shell | Self-awareness model | High | Meta-cognition |

### Category 5: Agent Lifecycle (5 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `agent-lifecycle-manager` | JS | Lifecycle management | Medium | State machine |
| `deployment-health-check` | Shell | Deployment validation | High | Smoke tests |
| `deployment-smoke-test` | Shell | Integration testing | High | Test suite |
| `detect-corruption` | Shell | Corruption detection | High | Integrity checks |
| `steward-orchestrator` | Shell | Orchestration logic | High | Workflow engine |

### Category 6: User Context & Personalization (4 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `heretek-theme` | Shell | UI theming | High | Presentation layer |
| `importance-scorer` | JS | Importance scoring | Medium | ML-based |
| `user-context-resolve` | JS | Context resolution | Medium | User profiling |
| `user-rolodex` | JS | Contact management | Medium | CRM-like |

### Category 7: System Operations (6 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `audit-cleanup` | Shell | System cleanup | High | Maintenance |
| `config-validator` | Shell | Configuration validation | High | Schema validation |
| `fleet-backup` | Shell | Fleet-wide backup | High | Distributed backup |
| `litellm-ops` | JS | LiteLLM operations | Medium | Model management |
| `pgvector-optimizer` | JS | PGVector optimization | Medium | Query optimization |
| `tabula-backup` | Shell | Database backup | High | Backup operations |

### Category 8: Advanced Features (5 skills)

| Skill | Type | Function | Migration Priority | Notes |
|-------|------|----------|-------------------|-------|
| `browser-access` | Shell | Web browsing | High | Browser automation |
| `goal-arbitration` | JS | Goal conflict resolution | Medium | Arbitration logic |
| `thought-loop` | Shell | Recursive thinking | High | Iterative processing |
| `workspace-consolidation` | Shell | Workspace management | High | File operations |
| `matrix-triad` | Shell | Triad coordination | High | Multi-agent sync |

---

## Migration Strategy

### Phase 1: Critical Shell Scripts (Weeks 1-2)
**Priority:** High - Core system functionality

1. **Communication Layer**
   - `a2a-message-send` → Python tool with Redis async client
   - `a2a-agent-register` → Agent registry service
   - `gap-detector` → Message pattern analyzer

2. **Governance Core**
   - `failover-vote` → Consensus tool with BFT logic
   - `auto-deliberation-trigger` → Event-driven trigger
   - `autonomous-pulse` → Health monitoring service

3. **System Operations**
   - `healthcheck` → Multi-service health checker
   - `config-validator` → Schema validation tool
   - `audit-cleanup` → Maintenance utility

### Phase 2: Memory & Knowledge (Weeks 3-4)
**Priority:** Medium - Data management

1. **Memory Systems**
   - `archivist` → Persistent memory tool
   - `backup-ledger` → Backup management
   - `session-wrap-up` → Session lifecycle

2. **Knowledge Pipeline**
   - `knowledge-ingest` → Data ingestion tool
   - `knowledge-retrieval` → Search and retrieval
   - `opportunity-scanner` → Pattern detection

### Phase 3: Advanced Features (Weeks 5-6)
**Priority:** Low - Enhancement features

1. **Agent Enhancement**
   - `curiosity-engine` → Exploration tool
   - `self-model` → Meta-cognition module
   - `goal-arbitration` → Conflict resolution

2. **User Experience**
   - `user-context-resolve` → Context management
   - `importance-scorer` → Priority scoring
   - `user-rolodex` → Contact management

---

## Technical Debt Assessment

### High Priority Issues

1. **Shell Script Limitations**
   - No type safety
   - Poor error handling
   - Difficult to test
   - Platform dependencies

2. **Inconsistent Patterns**
   - Mixed Redis client libraries (ioredis vs node-redis)
   - Hardcoded connection strings
   - No centralized configuration

3. **Missing Features**
   - No circuit breakers
   - Limited observability
   - Manual retry logic

### Migration Benefits

1. **Type Safety** - Pydantic models for all inputs/outputs
2. **Testing** - Comprehensive test suites with pytest
3. **Performance** - Async I/O, connection pooling
4. **Observability** - Structured logging, metrics
5. **Maintainability** - Clean architecture, documentation

---

## Tool Wrapper Pattern

For rapid migration, we'll use a wrapper pattern:

```python
from swarms import Tool
from typing import Optional, Dict, Any
import subprocess
import asyncio

class LegacySkillWrapper(Tool):
    """Wrapper for legacy shell-based skills"""
    
    def __init__(
        self,
        name: str,
        script_path: str,
        description: str,
        timeout: int = 30
    ):
        super().__init__(
            name=name,
            description=description,
            function=self.execute
        )
        self.script_path = script_path
        self.timeout = timeout
    
    async def execute(
        self,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute legacy skill with timeout"""
        try:
            # Build command
            cmd = [self.script_path]
            for key, value in kwargs.items():
                cmd.extend([f"--{key}", str(value)])
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode(),
                "error": stderr.decode(),
                "returncode": process.returncode
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Timeout after {self.timeout}s"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

---

## Next Steps

1. **Create Python wrappers** for all 23 shell scripts
2. **Build native Python tools** for high-priority skills
3. **Integrate with Tool Registry** for dynamic discovery
4. **Write comprehensive tests** for all migrated tools
5. **Update documentation** with migration guide

---

## Appendix: File Locations

```
/root/heretek/heretek-openclaw-core/skills/
├── a2a-agent-register/
├── a2a-message-send/
├── agemem-governance/
├── agent-lifecycle-manager/
├── archivist/
├── audit-cleanup/
├── auto-deliberation-trigger/
├── autonomous-pulse/
├── autonomy-audit/
├── backup-ledger/
├── browser-access/
├── config-validator/
├── constitutional-deliberation/
├── cross-tier-correlator/
├── curiosity-auto-trigger/
├── curiosity-engine/
├── day-dream/
├── deployment-health-check/
├── deployment-smoke-test/
├── detect-corruption/
├── dreamer-agent/
├── failover-vote/
├── fleet-backup/
├── gap-detector/
├── goal-arbitration/
├── governance-modules/
├── healthcheck/
├── heretek-theme/
├── importance-scorer/
├── knowledge-ingest/
├── knowledge-retrieval/
├── lib/
├── litellm-ops/
├── memory-consolidation/
├── opportunity-scanner/
├── pgvector-optimizer/
├── quorum-enforcement/
├── redis-ttl-manager/
├── self-model/
├── session-wrap-up/
├── steward-orchestrator/
├── tabula-backup/
├── thought-loop/
├── user-context-resolve/
├── user-rolodex/
└── workspace-consolidation/
```

---

**Status:** Audit Complete  
**Next Phase:** Python-native tool development
