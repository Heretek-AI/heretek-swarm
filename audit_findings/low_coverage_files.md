# Low Test Coverage Audit - Heretek-AI_heretek-swarm

**Date:** 2026-04-13
**Project:** Heretek-AI_heretek-swarm
**Tool:** SonarQube coverage analysis

## Executive Summary

The SonarQube `search_files_by_coverage` API returned **0 files** with `maxCoverage=50`, which may indicate:
1. Coverage data is not being computed/published to SonarQube
2. The coverage sensor is not configured for this project
3. All files have >50% coverage (unlikely given Quality Gate failures)

**Quality Gate Status:** FAILING
- New reliability rating: ERROR
- New security rating: ERROR
- Duplicated lines density: 3.1% (above 3% threshold)
- Security hotspots reviewed: 0.0%

## Project Overview

| Metric | Value |
|--------|-------|
| Total Source Files | 268 Python, ~25 TypeScript |
| Total Test Files | 106 Python |
| Source Lines (ncloc) | 146,105 |
| Test-to-Source Ratio | ~1:2.5 |
| Modules | 33 Python packages |

### Module Breakdown (Source Files)

| Module | Files | Module | Files |
|--------|-------|--------|-------|
| actors | 48 | mcp | 3 |
| api | 27 | memory | 8 |
| infrastructure | 11 | observability | 4 |
| collective | 18 | plugins | 6 |
| consensus | 11 | rag | 5 |
| llm | 10 | runtime | 9 |
| integrations | 10 | security | 5 |

## Coverage Analysis Observations

### Test Distribution Analysis

Based on pytest collection, test file count per module:

| Module Area | Test Files | Source Files | Ratio |
|-------------|------------|--------------|-------|
| actors | ~7 modules | 48 | Low |
| collective | ~5 modules | 18 | Moderate |
| consciousness | ~6 modules | 8 | High |
| consensus | ~8 modules | 11 | High |
| gateway | ~3 modules | 8 | Moderate |
| memory | ~5 modules | 8 | High |
| security | ~4 modules | 5 | High |
| state | ~4 modules | 3 | High |

### Likely Low Coverage Areas (Based on File Count Ratio)

**Critical Priority (0-30% coverage):**
- `src/heretek_swarm/actors/` - 48 source files, limited test coverage
- `src/heretek_swarm/api/` - 27 files, API tests only in integration folder
- `src/heretek_swarm/infrastructure/` - 11 files
- `src/heretek_swarm/integrations/` - 10 files
- `src/heretek_swarm/llm/` - 10 files
- `src/heretek_swarm/routing/` - 1 file (no dedicated tests)
- `src/heretek_swarm/logging/` - 1 file (no dedicated tests)
- `src/heretek_swarm/evaluation/` - 1 file (only 11 test cases found)

**High Priority (30-50% coverage):**
- `src/heretek_swarm/collective/` - 18 files
- `src/heretek_swarm/runtime/` - 9 files
- `src/heretek_swarm/gateway/` - 8 files

## Root Cause Analysis

### Why SonarQube Coverage API Returns Empty

1. **Coverage Not Configured**: The project may not have coverage reporting set up with SonarQube
2. **Sensor Not Running**: The coverage sensor may be disabled or misconfigured
3. **Coverage Tool Mismatch**: SonarQube expects specific coverage formats (Cobertura, JaCoCo, etc.)

### Evidence of Testing Activity

- 106 test files exist and pytest can collect 1000+ test cases
- Recent test files show active testing (test_rag_pipeline.py, test_agents.py, etc.)
- Quality Gate shows code issues but no coverage-related failures, suggesting coverage IS computed

## Recommendations

### Immediate Actions

1. **Verify SonarQube Coverage Configuration**
   ```bash
   # Check if coverage is being uploaded
   sonar-scanner -X 2>&1 | grep -i coverage
   ```

2. **Check sonar-project.properties or sonar config in pyproject.toml**

### Coverage Improvement Strategy

#### Phase 1: Critical Modules (Target: 80%+)
Focus on modules with highest risk:

| Priority | Module | Action |
|----------|--------|--------|
| 1 | actors | Add unit tests for message handlers, strategies |
| 2 | api | Add integration tests for API endpoints |
| 3 | state | Add tests for event_store, repository |
| 4 | security | Add adversarial test coverage |

#### Phase 2: High-Value Modules (Target: 70%+)
| Priority | Module | Action |
|----------|--------|--------|
| 5 | collective | Add algorithm tests (ACO, PSO, ABC) |
| 6 | runtime | Add autonomous_runtime tests |
| 7 | gateway | Add NATS mesh tests |

#### Phase 3: Maintenance (Target: 60%+)
- Complete coverage for remaining modules

### Coverage Targets

| Category | Current | Target | Critical Files |
|----------|---------|--------|----------------|
| Critical | Unknown | 80%+ | actors/*, api/*, state/* |
| High | Unknown | 70%+ | collective/*, runtime/*, gateway/* |
| Medium | Unknown | 60%+ | remaining modules |

## Files Needing Immediate Test Coverage

Based on critical open issues and file count:

### Critical (No/Low Coverage - Primary Risk)
- `src/heretek_swarm/actors/arbiter/handlers.py` - CRITICAL issues closed but no coverage record
- `src/heretek_swarm/actors/arbiter/strategies.py` - Many open issues
- `src/heretek_swarm/actors/base/message_handling.py` - CRITICAL cognitive complexity
- `src/heretek_swarm/actors/base/state_management.py` - CRITICAL cognitive complexity
- `src/heretek_swarm/runtime/autonomous_runtime.py` - CRITICAL cognitive complexity
- `src/heretek_swarm/runtime/main_loop.py` - CRITICAL cognitive complexity (28 complexity)

### High Risk Files with Open Issues
- `src/heretek_swarm/collective/algorithms/abc.py`
- `src/heretek_swarm/config/crud.py`
- `src/heretek_swarm/mem0_server/main.py`

## Technical Notes

### Why Coverage Data May Be Missing

1. **Python Coverage Tool**: The project likely uses `pytest-cov` but SonarQube expects Cobertura XML format
2. **Configuration**: Need to add to sonar-scanner or CI:
   ```bash
   pytest --cov=src --cov-report=xml
   sonar-scanner -Dsonar.coverageReportPaths=coverage.xml
   ```

3. **Sensor Configuration**: Verify in SonarQube project settings that Python coverage sensor is enabled

### Next Steps for Team Lead

1. Check SonarQube project settings -> Coverage tab
2. Verify CI/CD pipeline publishes coverage reports
3. Run local coverage: `pytest --cov=src --cov-report=html`
4. Review coverage/index.html for detailed per-file breakdown

## Summary

| Category | Count | Notes |
|----------|-------|-------|
| Source Files | 268 | Across 33 modules |
| Test Files | 106 | ~1:2.5 ratio |
| Critical Priority Files | ~15 | High risk, low coverage likely |
| High Priority Files | ~20 | Medium risk |
| Modules Needing Coverage Work | ~20 | All major modules |

**Recommendation:** Begin coverage improvement with `actors`, `api`, and `state` modules as they have the most critical issues and largest file counts.