# Multi-Tier Subagent Orchestration Plan: Heretek Swarm Full Codebase Transformation

## Objective
Perform a comprehensive, multi-tier subagent-driven deep dive into the **Heretek Swarm** codebase (`c:\Users\derek\Desktop\heretek-swarm`) to restructure, audit, debug, fix, document, and make the entire repository AI-ready. Leverage ALL installed MCP servers, plugins, skills, and agents in a coordinated, phased orchestration.

---

## Environment Inventory

### MCP Servers Available
- **SonarQube** — Static code analysis, quality gates, security hotspots, coverage metrics (project key: `Heretek-AI_heretek-swarm`)
- **GitHub Advanced Security** — Secret scanning, dependency vulnerability scanning, CodeQL
- **Context-Mode** — Sandboxed code execution, batch command execution, web fetching with indexing
- **Snyk** — SAST scanning, container scanning, IaC scanning, SBOM analysis
- **Cockpit Scheduler** — Todo cards, task management, job scheduling
- **Serena** — Symbol references, code insertion, memory management
- **Rigour** — Quality gates, security audits, code review on PR diffs
- **Notion MCP** — Documentation management
- **GitKraken GitLens** — PR management, launchpad, review workflows
- **Context-Matic** — API integration discovery and guidance
- **Heretek Swarm Docs** — Internal documentation filesystem queries

### Installed Plugins
- `advanced-security` — GitHub secret scanning, dependency scanning
- `ai-team-orchestration` — Multi-agent sprint planning and execution
- `software-engineering-team` — DevOps/CI, Product Manager, Responsible AI, Security, Architect, Tech Writer, UX Designer agents
- `sonarqube` — Code quality analysis integration
- `structured-autonomy` — Structured planning and implementation workflows
- `technical-spike` — Research and validation of technical decisions
- `napkin` — Visual whiteboard collaboration
- `frontend-web-dev` — Frontend development capabilities
- `doublecheck` — Three-layer verification pipeline
- `project-documenter` — MS Word documentation with draw.io diagrams
- `python-mcp-development` — Python MCP server development
- `roundup` — Status briefings from data sources
- `security-best-practices` — Security-focused code review
- `skills-for-copilot-studio` — Copilot Studio agent management
- `testing-automation` — Test generation and execution

### Key Sub-Agents Available
- **Explore** — Fast read-only codebase exploration
- **ai-readiness-reporter** — AgentRC readiness assessment → HTML dashboard
- **ai-team-dev** — Nova/Sage/Milo for frontend/backend/design
- **ai-team-producer** — Sprint planning, PRD writing, bug triage
- **ai-team-qa** — E2E testing, bug reports, QA sign-off
- **Project Documenter** — .docx documentation with draw.io diagrams
- **SE: Security** — OWASP Top 10, Zero Trust, LLM security
- **SE: Architect** — Well-Architected frameworks, design validation
- **SE: Tech Writer** — Developer documentation, tutorials
- **SE: DevOps/CI** — CI/CD pipelines, deployment debugging
- **SE: UX Designer** — UX research, user journey mapping
- **SE: Responsible AI** — Bias prevention, accessibility, ethical development
- **SE: Product Manager** — GitHub issues, business value alignment
- **Doublecheck** — Verification agent with source links
- **TDD Red/Green/Refactor Phase** — Test-driven development workflow
- **code-testing-generator** — Research-Plan-Implement test pipeline
- **test-quality-auditor** — Multi-dimensional test suite assessment
- **testability-migration** — Static dependency detection and wrapper generation
- **Context Architect** — Multi-file change planning
- **Meta Agentic Project Scaffold** — Project creation and workflow management
- **Copilot Studio Advisor/Author/Manage/Test** — Copilot Studio agent lifecycle

### Project Context
- **Language:** Python 3.11+ (backend), TypeScript/React (dashboard)
- **Framework:** FastAPI, Swarms framework, Docker Compose
- **Infrastructure:** PostgreSQL, Redis, Qdrant, NATS
- **Structure:** 23 agents across 6 tiers, ~50+ modules in `backend/heretek_swarm/`
- **Existing docs:** `docs/` directory with architecture, API, deployment docs
- **SonarQube:** Already configured with project key `Heretek-AI_heretek-swarm`
- **Test framework:** pytest (backend), Playwright (dashboard)

---

## Orchestration Plan: 4 Phases

### PHASE 1 — DISCOVERY & ASSESSMENT (Read-Only)
**Goal:** Map the entire codebase, assess current state, identify all issues without making changes.

#### Tier 1.1 — Codebase Cartography
- Deploy **Explore** sub-agent to map the full directory tree, module dependencies, and import graphs for `backend/heretek_swarm/`
- Deploy **Explore** sub-agent to map `swarm-dashboard/` structure, component tree, and data flow
- Deploy **Explore** sub-agent to catalog all 23 agents in `agent_workspace/agents/` — their roles, dependencies, and inter-agent communication patterns
- Use **Context-Mode batch execution** to run `pip list`, `docker compose config`, and dependency analysis in parallel
- Compile a master inventory of all files, their purposes, and cross-references

#### Tier 1.2 — Quality & Security Baseline
- Run **SonarQube** analysis on all source files (`backend/heretek_swarm`, `swarm-dashboard/src`, `tests`)
- Run **Snyk SAST scan** on the full codebase
- Run **Snyk container scan** on Docker images
- Run **Snyk IaC scan** on `docker-compose.yml` and infrastructure configs
- Run **GitHub Advanced Security** dependency scanning on `pyproject.toml` and `package.json`
- Run **GitHub Advanced Security** secret scanning across the entire repo
- Run **Rigour security audit** (`mcp_rigour-mcp_rigour_security_audit`) on project dependencies
- Collect all findings into a structured issue inventory categorized by severity

#### Tier 1.3 — AI-Readiness Assessment
- Run **ai-readiness-reporter** agent to produce `reports/index.html` with full AgentRC assessment
- Evaluate existing `AGENTS.md`, `copilot-instructions.md`, `.github/instructions/` files for completeness
- Assess whether the codebase follows agent-safety governance patterns (reference `agent-safety.instructions.md`)
- Identify gaps in AI-friendly documentation, CI workflows, and issue templates

#### Tier 1.4 — Test Coverage & Quality Audit
- Run **test-quality-auditor** on the full test suite
- Run **coverage-analysis** to identify coverage gaps and CRAP score hotspots
- Run **test-anti-patterns** audit on existing tests
- Run **test-gap-analysis** for pseudo-mutation testing
- Run **assertion-quality** analysis

**Deliverable:** Consolidated findings report with prioritized issues across all dimensions.

---

### PHASE 2 — REMEDIATION & RESTRUCTURING
**Goal:** Fix critical issues, restructure codebase, eliminate technical debt.

#### Tier 2.1 — Critical Security Fixes
- Address all CRITICAL and HIGH severity findings from Phase 1 security scans
- Fix hardcoded secrets, injection vulnerabilities, and insecure configurations
- Apply **SE: Security** agent review on authentication, authorization, and data handling code
- Verify fixes with **Doublecheck** verification pipeline

#### Tier 2.2 — Code Quality Remediation
- Fix SonarQube bugs and code smells (target: zero Critical/Blocker issues)
- Run **code-testing-fixer** on any compilation/test errors
- Apply **testability-migration** to detect and wrap static dependencies (`DateTime.now`, `File.*`, etc.)
- Run **ruff-recursive-fix** for Python code style consistency
- Fix duplicate code blocks identified by SonarQube

#### Tier 2.3 — Structural Restructuring
- Deploy **Context Architect** to plan multi-file refactoring of `backend/heretek_swarm/` modules
- Consolidate duplicate patterns across the 50+ modules
- Improve module boundaries — ensure clean separation between `actors/`, `orchestration/`, `memory/`, `api/`, etc.
- Standardize naming conventions, imports, and type annotations
- Remove dead code, unused imports, and commented-out blocks
- Apply **python-design-patterns** and **python-project-structure** best practices

#### Tier 2.4 — Test Suite Enhancement
- Generate missing tests using **code-testing-generator** (Research → Plan → Implement pipeline)
- Target 80%+ coverage on critical paths
- Fix flaky tests and test anti-patterns
- Add integration tests for API endpoints
- Add Playwright E2E tests for dashboard critical flows

**Deliverable:** Cleaned, restructured codebase with passing tests and resolved critical issues.

---

### PHASE 3 — DOCUMENTATION
**Goal:** Produce comprehensive, AI-friendly documentation.

#### Tier 3.1 — Architecture Documentation
- Deploy **Project Documenter** agent to generate full `.docx` documentation with draw.io architecture diagrams
- Generate C4 architecture diagrams (Context → Container → Component → Code levels)
- Document all 23 agents with their roles, NATS subjects, dependencies, and message contracts
- Document API endpoints with OpenAPI specs
- Document database schema from `migrations/`

#### Tier 3.2 — Developer Documentation
- Update `README.md` with current architecture and quick-start guides
- Create/update `CONTRIBUTING.md` with development workflow
- Document deployment procedures and infrastructure
- Create troubleshooting guides for common issues
- Deploy **SE: Tech Writer** for technical writing quality review

#### Tier 3.3 — Operational Documentation
- Document monitoring and observability setup (Prometheus metrics, health checks)
- Document incident response procedures
- Create runbooks for common operational tasks
- Document the agent governance and safety mechanisms

**Deliverable:** Complete documentation suite in `docs/`, updated README, and generated `.docx` report.

---

### PHASE 4 — AI-READY TRANSFORMATION
**Goal:** Make the repository fully optimized for AI-assisted development.

#### Tier 4.1 — AI Configuration Files
- Generate/update `AGENTS.md` with project conventions, architecture overview, and development guidelines
- Generate/update `.github/copilot-instructions.md` with code style, testing patterns, and security requirements
- Generate/update `.github/instructions/` files for domain-specific guidance
- Create `CLAUDE.md` if missing or update existing one
- Ensure all instruction files follow agent-safety governance patterns

#### Tier 4.2 — CI/CD & Automation
- Review and optimize GitHub Actions workflows
- Add automated quality gates (SonarQube, tests, security scans) to CI pipeline
- Configure Dependabot for automated dependency updates
- Set up pre-commit hooks for linting and formatting
- Add automated documentation generation to CI

#### Tier 4.3 — Issue Templates & Project Management
- Create/update GitHub issue templates (bug report, feature request, technical debt)
- Create PR template with checklist
- Set up project board automation
- Configure auto-labeling for issues and PRs

#### Tier 4.4 — Final Verification
- Run full **Doublecheck** verification on all changes
- Run final SonarQube quality gate check
- Run final security audit
- Run full test suite with coverage report
- Generate final AI-readiness score via **ai-readiness-reporter**

**Deliverable:** Fully AI-ready repository with comprehensive configuration, automation, and passing quality gates.

---

## Execution Rules

1. **Read-only first:** Phase 1 must complete with a consolidated report before any changes are made
2. **Parallel where possible:** Within each phase, independent tasks should run concurrently using sub-agents
3. **Verify after fix:** Every fix must be verified — use Doublecheck or re-run the relevant scan
4. **Commit per phase:** Create a git commit at the end of each phase with conventional commit format
5. **Track progress:** Use Cockpit Scheduler to create and track todo cards for each tier
6. **Fail safe:** If any critical security issue is found, pause and report before proceeding
7. **SonarQube integration:** Disable automatic analysis at start, re-enable after all changes are complete
8. **Preserve git history:** Use `git mv` for renames, avoid squashing unrelated changes

## Success Criteria
- [ ] Zero Critical/Blocker SonarQube issues
- [ ] Zero CRITICAL/HIGH security vulnerabilities
- [ ] Test coverage ≥ 80% on critical paths
- [ ] All tests passing (backend + frontend)
- [ ] Complete architecture documentation generated
- [ ] AGENTS.md, copilot-instructions.md, and .github/instructions/ created/updated
- [ ] CI/CD pipeline with automated quality gates
- [ ] AI-Readiness score ≥ 80%
- [ ] Docker Compose stack builds and runs successfully