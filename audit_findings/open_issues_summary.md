# SonarQube Duplication Audit - Heretek-AI_heretek-swarm

**Date**: 2026-04-14
**Project**: Heretek-AI_heretek-swarm
**Tool**: SonarQube (via satanlovesfags MCP)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Duplicated Files** | 56 |
| **Total Duplicated Lines** | 5,203 |
| **Total Duplicated Blocks** | 166 |
| **Overall Duplication Density** | 2.1% |

---

## Top 15 Files by Duplicated Lines

| Rank | File | Path | Duplicated Lines | Duplicated Blocks | Density |
|------|------|------|-----------------|-------------------|---------|
| 1 | **triad.py** | `src/heretek_swarm/actors/triad.py` | 1,090 | 26 | 95.8% |
| 2 | **LLMProvidersSection.tsx** | `dashboard/frontend/src/components/Settings/LLMProvidersSection.tsx` | 297 | 8 | 63.3% |
| 3 | **beta.py** | `src/heretek_swarm/actors/beta.py` | 276 | 7 | 91.4% |
| 4 | **charlie.py** | `src/heretek_swarm/actors/charlie.py` | 271 | 7 | 91.2% |
| 5 | **alpha.py** | `src/heretek_swarm/actors/alpha.py` | 258 | 6 | 90.8% |
| 6 | **EmbeddingProvidersSection.tsx** | `dashboard/frontend/src/components/Settings/EmbeddingProvidersSection.tsx` | 279 | 7 | 56.9% |
| 7 | **steward.py** | `src/heretek_swarm/actors/steward.py` | 285 | 6 | 83.3% |
| 8 | **emergent_detection.py** | `src/heretek_swarm/collective/emergent_detection.py` | 105 | 2 | 21.5% |
| 9 | **wire_agents_session44.py** | `scripts/wire_agents_session44.py` | 104 | 1 | 27.1% |
| 10 | **wire_agents.py** | `scripts/wire_agents.py` | 104 | 1 | 17.5% |
| 11 | **tracing.py** (observability) | `src/heretek_swarm/observability/tracing.py` | 102 | 1 | 22.6% |
| 12 | **tracing.py** (otel) | `src/heretek_swarm/infrastructure/otel/tracing.py` | 87 | 1 | 20.8% |
| 13 | **emergence_analyzer.py** | `src/heretek_swarm/collective/emergence_analyzer.py` | 80 | 1 | 83.3% |
| 14 | **openai_provider.py** | `src/heretek_swarm/llm/providers/openai_provider.py` | 56 | 2 | 18.7% |
| 15 | **zai_provider.py** | `src/heretek_swarm/llm/providers/zai_provider.py` | 56 | 2 | 19.5% |

---

## Breakdown by Directory/Module

### Python Actors (`src/heretek_swarm/actors/`)
| File | Duplicated Lines | Blocks | Density |
|------|-----------------|--------|---------|
| triad.py | 1,090 | 26 | 95.8% |
| steward.py | 285 | 6 | 83.3% |
| beta.py | 276 | 7 | 91.4% |
| charlie.py | 271 | 7 | 91.2% |
| alpha.py | 258 | 6 | 90.8% |
| examiner.py | 127 | 1 | 11.4% |
| habit_forge.py | 156 | 4 | 11.9% |
| perceiver_plus.py | 156 | 4 | 10.5% |

**Observation**: The triad actor has extremely high duplication (95.8%), suggesting possible copy-paste or template-based code generation that should be refactored.

### Python LLM Providers (`src/heretek_swarm/llm/providers/`)
| File | Duplicated Lines | Blocks | Density |
|------|-----------------|--------|---------|
| base.py | 40 | 2 | 9.9% |
| openai_provider.py | 56 | 2 | 18.7% |
| zai_provider.py | 56 | 2 | 19.5% |
| openai_compatible.py | 23 | 1 | 8.0% |
| ollama_provider.py | 25 | 1 | 8.3% |
| llamacpp_provider.py | 25 | 1 | 8.5% |
| lemonade_provider.py | 23 | 1 | 8.6% |

**Observation**: Provider implementations share significant common code, suggesting need for a shared base class refactor.

### Python Embeddings Providers (`src/heretek_swarm/embeddings/providers/`)
| File | Duplicated Lines | Blocks | Density |
|------|-----------------|--------|---------|
| base.py | 19 | 1 | 6.9% |

### Frontend React Components (`dashboard/frontend/`)
| File | Duplicated Lines | Blocks | Density |
|------|-----------------|--------|---------|
| LLMProvidersSection.tsx | 297 | 8 | 63.3% |
| EmbeddingProvidersSection.tsx | 279 | 7 | 56.9% |
| ConnectorNode.tsx | 48 | 2 | 44.9% |
| LLMNode.tsx | 48 | 2 | 43.6% |
| MemoryNode.tsx | 48 | 2 | 44.0% |
| ToolNode.tsx | 48 | 2 | 40.7% |
| DecisionNode.tsx | 33 | 1 | 27.7% |

**Observation**: Frontend settings sections and workflow builder nodes have high duplication. Consider extracting shared UI components.

### Tracing Files
| File | Duplicated Lines | Blocks | Density |
|------|-----------------|--------|---------|
| observability/tracing.py | 102 | 1 | 22.6% |
| infrastructure/otel/tracing.py | 87 | 1 | 20.8% |

**Observation**: Two different tracing implementations share significant code.

---

## Critical Findings

1. **Actor triad.py is severely duplicated (95.8%)**: This single file has 1,090 duplicated lines across 26 blocks. This represents the highest priority for refactoring.

2. **Actor files (alpha, beta, charlie, steward, triad) share extensive code**: All showing 83-95% duplication density, suggesting a common base implementation that was copy-pasted with modifications.

3. **Frontend settings components (LLMProvidersSection, EmbeddingProvidersSection)**: 56-63% duplication suggests UI component reuse opportunities.

4. **Workflow builder node components**: All node types (LLMNode, MemoryNode, ConnectorNode, ToolNode) show 40-45% duplication with similar structure.

5. **Two separate tracing implementations**: `observability/tracing.py` and `infrastructure/otel/tracing.py` share 87-102 duplicated lines, indicating a refactoring opportunity to consolidate.

---

## Recommendations

1. **High Priority**: Refactor `triad.py` - extract common actor logic into a base class
2. **High Priority**: Create a shared actor base class to eliminate copy-paste across alpha, beta, charlie, steward
3. **Medium Priority**: Extract common UI components in frontend settings sections
4. **Medium Priority**: Consolidate tracing implementations or establish a clear pattern for which to use
5. **Low Priority**: Review and potentially merge provider base classes

---

## Available Metrics in SonarQube

The following metric categories are available in SonarQube for this project:
- **Size**: classes, files, functions, lines, ncloc, comment_lines
- **Coverage**: coverage, branch_coverage, line_coverage, conditions_to_cover
- **Duplications**: duplicated_blocks, duplicated_files, duplicated_lines, duplicated_lines_density
- **Complexity**: complexity, cognitive_complexity
- **Issues**: blocker_violations, critical_violations, major_violations, minor_violations, info_violations
- **Maintainability**: code_smells, sqale_rating, technical_debt
- **Reliability**: bugs, reliability_rating
- **Security**: vulnerabilities, security_hotspots, security_rating

---

*Audit report generated by worker-10 for team codebase-audit*