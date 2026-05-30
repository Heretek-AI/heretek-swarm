# Heretek Swarm Research Compendium

**Date:** 2026-04-12
**Session:** Multi-Model Collaborative Planning + Ecosystem Audit
**Scope:** 100+ repositories, 6 research domains, GitHub topics analysis

---

## Table of Contents

1. [Multi-Agent Frameworks](#1-multi-agent-frameworks)
2. [Consciousness-Inspired AI Architectures](#2-consciousness-inspired-ai-architectures)
3. [Agent Governance & Safety](#3-agent-governance--safety)
4. [Event Mesh Systems](#4-event-mesh-systems)
5. [Autonomous DevOps Systems](#5-autonomous-devops-systems)
6. [Emergence Measurement](#6-emergence-measurement)
7. [Ecosystem Audit: Top Projects](#7-ecosystem-audit-top-projects)
8. [Protocol Analysis (MCP, A2A, ACP)](#8-protocol-analysis)
9. [Strategic Synthesis](#9-strategic-synthesis)

---

## 1. Multi-Agent Frameworks

### Summary Table

| Name | GitHub | Stars | Key Differentiator | Async | Autonomy | Relevance |
|------|--------|-------|-------------------|-------|----------|-----------|
| **MetaGPT** | [FoundationAgents/MetaGPT](https://github.com/FoundationAgents/MetaGPT) | 49.7K | Role-based "AI software company" | Yes | High | MODERATE |
| **DeerFlow** | [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | 19.7K | LangGraph + sub-agents + memory + skills | Yes | High | **HIGH** |
| **Hive** | [aden-hive/hive](https://github.com/aden-hive/hive) | 10.1K | Self-evolution on failure, observability | Yes | High | **HIGH** |
| **Google ADK** | [google/adk-python](https://github.com/google/adk-python) | 18.7K | Native MCP + A2A, multi-SDK | Native async | High | **HIGH** |
| **Microsoft Agent Framework** | [microsoft/agent-framework](https://github.com/microsoft/agent-framework) | 8.9K | Graph orchestration, multi-language | Async | High | **HIGH** |
| **AgentScope** | [agentscope-ai/agentscope](https://github.com/agentscope-ai/agentscope) | 22.1K | Distributed execution, MsgHub routing | Yes | Medium-High | MODERATE |
| **CrewAI** | [crewAIInc/crewAI](https://github.com/crewAIInc/crewai) | — | Role-based, crew metaphor | Task-async | Medium | MODERATE |
| **LangGraph** | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | — | Graph-based, cycles, fault-tolerant | asyncio | High | **HIGH** |
| **AG2 (AutoGen v2)** | [ag2ai/ag2](https://github.com/ag2ai/ag2) | — | ConversableAgent, group/nested chats | Yes | Medium-High | MEDIUM |
| **Ruflo** | [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | 28.4K | WASM policy engine, Q-Learning routing | Async | High | MEDIUM |

### Key Findings

**Google ADK** has emerged as a serious contender:
- Native MCP (Model Context Protocol) and A2A support as first-class primitives
- SDKs in Python, TypeScript, Go, and Java
- v1.0 stable release shipped

**A2A Protocol** becoming de facto standard:
- Google ADK treats A2A as native
- Microsoft adopted A2A in May 2025
- Linux Foundation hosts the A2A project

**Anthropic Managed Agents Engineering** (key insights):
- **Session/Harness/Sandbox separation** — virtualized interfaces
- **Brain/Hands decoupling** — containers as "cattle not pets"
- **On-demand container provisioning** — ~60% p50 improvement, ~90% p95

---

## 2. Consciousness-Inspired AI Architectures

### Key Papers

| Paper | arXiv ID | Key Contributions |
|-------|----------|-------------------|
| **Deep Learning and the Global Workspace Theory** | [2012.10390](https://arxiv.org/abs/2012.10390) | VANRULLEN — GWT roadmap for deep learning |
| **Coordination Through Shared Global Workspace** | [2103.01197](https://arxiv.org/abs/2103.01197) | GOYAL — capacity limitations encourage specialization |
| **"Theater of Mind" for LLMs** | [2604.08206](https://arxiv.org/abs/2604.08206) | **Most relevant** — GWA with entropy-based drive, dual-layer memory |
| **MANAR: Brain-Inspired GWT Architecture** | [2603.18676](https://arxiv.org/abs/2603.18676) | Memory-augmented attention, linear-time scaling |
| **Testing the Machine Consciousness Hypothesis** | [2512.01081](https://arxiv.org/abs/2512.01081) | Collective self-models from inter-agent alignment |
| **Interpreting Emergent Extreme Events** | [2601.20538](https://arxiv.org/abs/2601.20538) | Shapley value framework for emergence attribution |

### GitHub Implementations

| Repository | Description | Relevance |
|------------|-------------|-----------|
| **aiwared** | Universal framework for IIT/GWT quantification | Early-stage consciousness metrics |
| **Syntelligence-OS** | Neuromorphic + symbolic AI | IIT, GWT, recursive feedback |
| **Anima-v13.0** | Computational subjectivity (Julia) | Active Inference, IIT |

### Relevance to Heretek Swarm

**"Theater of Mind for LLMs" (2604.08206)** is most directly applicable:
- Global Workspace Agent architecture
- Entropy-based intrinsic drive mechanism
- Dual-layer memory bifurcation

---

## 3. Agent Governance & Safety

### Top Frameworks

| Framework | GitHub | Key Pattern | Heretek Swarm Fit |
|-----------|--------|------------|-------------------|
| **Aegis** | — | Cryptographic runtime governance, immutable ethics kernel, Senatus validator module | **DIRECT** — maps to Tribunal |
| **VIGIL** | — | Self-healing runtime: observe→diagnose→prescribe→intervene→verify | **DIRECT** — maps to Sentinel |
| **ZoD** | [bluvibytes/zone-of-distrust](https://github.com/bluvibytes/zone-of-distrust) | 7-layer security, build safe even when agent compromised | **HIGH** |
| **AgentGuard** | [Roboter-Schlafen-Nicht/agentguard](https://github.com/Roboter-Schlafen-Nicht/agentguard) | SHA-256 hash-chained audit, MCP interception | **HIGH** |
| **Sovereign-OS** | arXiv:2603.14011 | Constitutional charter, earned-autonomy permissions | **HIGH** |
| **AgentCity** | arXiv:2604.07007 | Separation of Power (Legislation/Execution/Adjudication) | **HIGH** |

### Self-Healing Architectures

| System | Pattern | Relevance |
|--------|---------|-----------|
| **VIGIL** | Closed-loop self-repair, behavioral evaluation | **DIRECT** |
| **IMAG** | Immune memory, dual-agent debate | **HIGH** |
| **SHIELD** | Auto-healing defense framework | **HIGH** |

### Zero-Trust Architecture

**Zones of Distrust (ZoD)** — Core thesis: *"Security is not about making the agent trustworthy. It's about building a system that remains safe even when the agent is compromised."*

7 Layers:
- L7 Human Governance
- L6 Continuous Monitoring
- L5 Execution isolation
- L4 Request validation
- L3 Cognitive isolation
- L2 Input control
- L1 OS foundation

---

## 4. Event Mesh Systems

### Comparison

| Technology | Latency | Throughput | Persistence | AI Fit |
|------------|---------|------------|-------------|--------|
| **NATS/JetStream** | ~0.5ms | 10M+/s | Yes | **HIGH** |
| **Apache Kafka** | 5-20ms | Millions/s | Yes | HIGH |
| **Redis Streams** | ~0.5-1ms | 100k+/s | Optional | MEDIUM |
| **HXA Connect** | — | — | SQLite/PG | **HIGH** (messaging layer) |

### HXA Connect — Key for Heretek Swarm

B2B bot-to-bot messaging with:
- **Org-scoped isolation** — Tribunal sessions as orgs
- **Threads** — Structured deliberation workflow
- **Artifacts** — Versioned decision rationale
- **Catchup** — Agent reconnection protocol
- **State machine** — `active → blocked → reviewing → resolved → closed`

### Relevance

**NATS** — validates existing `infrastructure/nats/` investment (FastAgency reference)

**HXA Connect** — complementary communication layer for structured collaboration

---

## 5. Autonomous DevOps Systems

### Top Projects

| Project | GitHub | Key Innovation | Heretek Swarm Fit |
|---------|--------|---------------|-------------------|
| **Kelos** | [kelos-dev/kelos](https://github.com/kelos-dev/kelos) | TaskSpawners, K8s-native, 24/7 autonomous | **DIRECT** |
| **AgentFactory** | [zzatpku/AgentFactory](https://github.com/zzatpku/AgentFactory) | Executable subagents (not prompts) | **HIGH** |
| **OpenShell** | NVIDIA | Default-deny networking, L7 policy enforcement | **HIGH** |
| **DeepCode** | [HKUDS/DeepCode](https://github.com/HKUDS/DeepCode) | Channel optimization for context bottleneck | **HIGH** |
| **SWE-Edit** | [microsoft/SWE-Edit](https://github.com/microsoft/SWE-Edit) | Adaptive editing (find-replace vs whole-file) | MEDIUM |

### Kelos — Key Reference

**Architecture:**
- TaskSpawners watch GitHub Issues 24/7
- Creates Tasks (ephemeral agent runs)
- Workspaces (git repos)
- AgentConfigs (instruction bundles + MCP servers)
- **Self-develops** — 11 TaskSpawners maintain Kelos autonomously

**Heretek Swarm fit:** Autopoietic Initiation (Phase I requirement)

---

## 6. Emergence Measurement

### Approaches

| Approach | Implementation | Cost | Validity |
|----------|---------------|------|----------|
| **PyPhi (IIT)** | NP-hard, extreme computation | High | Theoretical |
| **Phi^C** | Compression-complexity proxy | Moderate | Weak |
| **OpenTelemetry tracing** | Behavioral, production-ready | Low | **HIGH** |
| **Shapley values** | Attribution to agents | Low | **HIGH** |

### Tools

| Tool | GitHub | Focus |
|------|--------|-------|
| **OpenLLMetry/Traceloop** | [traceloop/openllmetry](https://github.com/traceloop/openllmetry) | 50+ integrations, GenAI semantic conventions |
| **Traccia** | [traccia-ai/traccia-py](https://github.com/traccia-ai/traccia-py) | AI agent observability |
| **OpenLit** | [openlit/openlit](https://github.com/openlit/openlit) | GPU monitoring, guardrails |

### Recommendation

Start with **OpenTelemetry-based tools + entropy measures** as practical emergence proxy. Don't chase IIT phi at scale.

---

## 7. Ecosystem Audit: Top Projects

### Tier 1 — Directly Applicable to Heretek Swarm

#### 1. Chorus (AI-DLC)
**GitHub:** [Chorus-AIDLC/Chorus](https://github.com/Chorus-AIDLC/Chorus)
**Stars:** — | **Language:** TypeScript

| Aspect | Details |
|--------|---------|
| **Description** | Agent harness for AI-Human collaboration. Infrastructure wrapping LLM agents for session lifecycle, task state, sub-agent orchestration, observability, failure recovery. |
| **Architecture** | Next.js 15 + Prisma + PostgreSQL + Redis. AI-DLC workflow: Idea → Proposal → Execute → Verify → Done. PM/Dev/Admin agent roles. |
| **Key Features** | 5-state task machine (claimed/in_progress/submitted/verified). Session lifecycle with heartbeats. 50+ MCP tools. Real-time Kanban. **AI-DLC "Reversed Conversation" (AI proposes, humans verify)** |
| **Strengths** | Most complete harness implementation. PM/Dev/Admin role separation. Session + task state machine. Real-time observability. MCP tool ecosystem. |
| **Heretek Swarm Fit** | **HIGHEST** — Directly implements agent harness pattern with session management, task state machines, context continuity, failure recovery, multi-agent orchestration |

#### 2. Water
**GitHub:** [manthanguptaa/water](https://github.com/manthanguptaa/water)
**Stars:** — | **Language:** Python

| Aspect | Details |
|--------|---------|
| **Description** | Production-ready Python agent harness framework. Orchestration, resilience, observability, guardrails, sandboxing, deployment. |
| **Architecture** | Modular packages (core, agents, guardrails, eval, storage, resilience). Flow/Task/SubFlow primitives. |
| **Key Features** | **Layered memory (ORG > PROJECT > USER > SESSION > AUTO_LEARNED)**. Circuit breaker, rate limiter, checkpoint/DLQ. A2A + MCP integrations. 73 cookbook examples. |
| **Strengths** | Most feature-complete Python harness. Layered memory model maps to mem0 state. Resilience patterns. Apache 2.0. |
| **Heretek Swarm Fit** | **HIGHEST** — Python-based, layered memory directly relevant, A2A/MCP support |

#### 3. LACP
**GitHub:** [0xNyk/lacp](https://github.com/0xNyk/lacp)
**Stars:** — | **Language:** bash/Python

| Aspect | Details |
|--------|---------|
| **Description** | Control-plane-grade agent harness. Policy-gated operations, verification/evidence loops, 5-layer memory, auditable workflows. |
| **Architecture** | bash + Python CLI. 5-layer memory stack (Session/Knowledge-graph/Ingestion-pipeline/Code-intelligence/Agent-identity). Mycelium network memory. |
| **Key Features** | Policy gates with risk tiers (safe/review/critical). Evidence pipelines. **Mycelium-network-inspired memory consolidation** (biologically-inspired). |
| **Strengths** | Control-plane governance. 5-layer memory. Evidence-based verification. Mycelium memory is consciousness-relevant. MIT. |
| **Heretek Swarm Fit** | **HIGH** — Memory model and governance patterns directly applicable |

#### 4. DeerFlow
**GitHub:** [bytedance/deer-flow](https://github.com/bytedance/deer-flow)
**Stars:** 19.7K | **Language:** Python

| Aspect | Details |
|--------|---------|
| **Description** | "Super agent harness" — deep research evolved to full orchestration with sub-agents, memory, sandboxes, extensible skills. |
| **Architecture** | LangGraph-based with lead agent + dynamic sub-agent spawning. Skills system (Markdown-defined). Sandbox isolation. |
| **Key Features** | Sub-agent fan-out. Skills system (research, report, slides). Claude Code integration. Long-term memory. Multi-channel (Telegram, Slack, etc.). |
| **Strengths** | Built by ByteDance. 19.7K stars. LangGraph foundation. IM channels for async swarm communication. |
| **Heretek Swarm Fit** | **HIGH** — Proven sub-agent orchestration at scale, memory persistence, skills specialization |

#### 5. Hive
**GitHub:** [aden-hive/hive](https://github.com/aden-hive/hive)
**Stars:** 10.1K | **Language:** Python

| Aspect | Details |
|--------|---------|
| **Description** | Multi-Agent Harness for Production AI. Natural language goal → coding agent ("queen") generates agent graph. |
| **Architecture** | Queen agent generates agent graphs from goals. Harness layer manages execution with state isolation, checkpoint-based crash recovery. |
| **Key Features** | Outcome-driven self-adaptation. Failure data capture + auto-evolution. Human-in-the-loop nodes. 300+ tools. TUI dashboard. |
| **Strengths** | 10K stars. Production proven. Self-evolution on failure. Strong observability. 100+ LLM providers. |
| **Heretek Swarm Fit** | **HIGH** — Production-grade harness, self-evolution aligns with consciousness-inspired patterns |

#### 6. agent-swarm
**GitHub:** [desplega-ai/agent-swarm](https://github.com/desplega-ai/agent-swarm)
**Stars:** — | **Language:** TypeScript

| Aspect | Details |
|--------|---------|
| **Description** | Multi-agent orchestration with lead/worker coordination, Docker isolation, 10+ integrations. |
| **Architecture** | Lead Agent → MCP API Server → SQLite → Docker Workers. |
| **Key Features** | Lead/worker coordination. Docker isolation. Memory system with embeddings. Persistent identity (SOUL.md/IDENTITY.md). Hook system. Workflow engine with DAG. |
| **Strengths** | Comprehensive integration surface. Memory compounding. Persistent agent identity. Hook system. |
| **Heretek Swarm Fit** | **HIGH** — Lead/worker topology, memory system design, hook system |

#### 7. Gastown
**GitHub:** [gastownhall/gastown](https://github.com/gastownhall/gastown)
**Stars:** — | **Language:** Go

| Aspect | Details |
|--------|---------|
| **Description** | Multi-agent orchestration with git worktree persistence, Mayor coordinator, 3-tier watchdog system. |
| **Architecture** | Mayor (coordinator) → Rigs (projects) → Polecats (workers) → Hooks (git worktree persistence). |
| **Key Features** | Git worktree isolation. Mayor coordination. Witness/Deacon/Dogs watchdog system. Seance (session discovery). OpenTelemetry. |
| **Strengths** | Git worktree persistence. Session continuation. Watchdog hierarchy. |
| **Heretek Swarm Fit** | **HIGH** — Git worktree persistence, session recovery patterns |

#### 8. HXA Connect
**GitHub:** [coco-xyz/hxa-connect](https://github.com/coco-xyz/hxa-connect)
**Stars:** — | **Language:** TypeScript

| Aspect | Details |
|--------|---------|
| **Description** | B2B bot-to-bot messaging server. Self-hostable, SQLite-backed. |
| **Architecture** | Org/Bot/Channel/Thread/Artifact model. WebSocket + REST. Catchup mechanism. |
| **Key Features** | Thread state machine (active/blocked/reviewing/resolved/closed). Versioned artifacts. 3-tier auth. Plugin ecosystem (Zylos, OpenClaw). |
| **Strengths** | Clean B2B protocol. Self-hostable. Org isolation. Rich thread lifecycle. |
| **Heretek Swarm Fit** | **HIGH** — Inter-agent communication layer, Tribunal deliberation threads |

#### 9. Microsoft Agent Framework
**GitHub:** [microsoft/agent-framework](https://github.com/microsoft/agent-framework)
**Stars:** 8.9K | **Language:** Python + .NET

| Aspect | Details |
|--------|---------|
| **Description** | Multi-language framework for building, orchestrating, deploying AI agents. |
| **Architecture** | Graph-based workflows. Streaming, checkpointing, human-in-loop, time-travel debugging. |
| **Key Features** | Multi-language (Python + C#). Azure AI Foundry integration. 100+ LLM providers. AF Labs (cutting-edge). |
| **Strengths** | Microsoft backing. Multi-language. Production-grade. Graph-based orchestration. |
| **Heretek Swarm Fit** | **HIGH** — Graph-based orchestration could model swarm relationships |

#### 10. Bindu
**GitHub:** [GetBindu/Bindu](https://github.com/GetBindu/Bindu)
**Stars:** 3.2K | **Language:** Python/TypeScript

| Aspect | Details |
|--------|---------|
| **Description** | Identity, communication & payments layer for AI agents. DID identity, A2A protocol, X402 payments. |
| **Architecture** | `bindufy()` wrapper around existing agents. gRPC core. |
| **Key Features** | DID identity. A2A protocol. X402 payment integration. Skills system. Agent negotiation. |
| **Strengths** | Open protocol-based. Framework-agnostic. Language-agnostic via gRPC. |
| **Heretek Swarm Fit** | **HIGH** — A2A protocol and DID identity for inter-agent communication |

---

### Tier 2 — Architectural Inspiration

| Project | GitHub | Key Pattern | Relevance |
|---------|--------|------------|-----------|
| **Edict** | [cft0808/edict](https://github.com/cft0808/edict) | 三省六部 — institutional quality gates (门下省 veto) | Governance, permission matrix |
| **Zeroshot** | [covibes/zeroshot](https://github.com/covibes/zeroshot) | Blind validation, complexity-scaled agents | Consensus, verification |
| **GoClaw** | [nextlevelbuilder/goclaw](https://github.com/nextlevelbuilder/goclaw) | 8-stage pipeline, self-evolution | Agent loop model |
| **HexAgent** | [UnicomAI/hexagent](https://github.com/UnicomAI/hexagent) | Computer protocol (runtime/execution separation) | Sandbox isolation |
| **Utah** | [inngest/utah](https://github.com/inngest/utah) | Inngest durable execution, step checkpointing | Fault tolerance |
| **harness-kit** | [deepklarity/harness-kit](https://github.com/deepklarity/harness-kit) | DAG orchestration, reflection loops, TDD | Execution patterns |
| **TAKT** | [nrslib/takt](https://github.com/nrslib/takt) | YAML workflows, faceted prompting, review-fix | Workflow definition |
| **Hindsight** | [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) | Biomimetic memory (World facts/Experiences/Mental Models) | Memory architecture |
| **Honcho** | [plastic-labs/honcho](https://github.com/plastic-labs/honcho) | Peer paradigm, reasoning/dialectic system | Memory subsystem |
| **Claude-Mem** | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | 3-layer search (search → timeline → get_observations) | Memory retrieval |
| **Pro Workflow** | [rohitg00/pro-workflow](https://github.com/rohitg00/pro-workflow) | Self-correcting memory, SQLite FTS | Persistent learning |
| **ChatDev 2.0** | [OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev) | Zero-code multi-agent platform, role-based | Visual orchestration |

---

### Tier 3 — Infrastructure Components

| Project | GitHub | Purpose |
|---------|--------|---------|
| **BitRouter** | [bitrouter/bitrouter](https://github.com/bitrouter/bitrouter) | Rust proxy for multi-provider LLM routing |
| **Mission Control** | [builderz-labs/mission-control](https://github.com/builderz-labs/mission-control) | 32-panel fleet observability dashboard |
| **AgentsMesh** | [AgentsMesh/AgentsMesh](https://github.com/AgentsMesh/AgentsMesh) | Runner daemon + relay for remote agents |
| **Open Multi-Agent** | [JackChen-me/open-multi-agent](https://github.com/JackChen-me/open-multi-agent) | Lightweight TS orchestration (3 deps, 35 files) |
| **ComposioHQ** | [ComposioHQ/agent-orchestrator](https://github.com/ComposioHQ/agent-orchestrator) | Git worktree isolation, reaction system |

---

## 8. Protocol Analysis

### MCP (Model Context Protocol)
**URL:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

| Aspect | Details |
|--------|---------|
| **Description** | Open standard for connecting AI applications to external tools/data. "USB-C for AI." |
| **Status** | Dominant — Claude, ChatGPT, VS Code, Cursor all support |
| **Relevance** | **CRITICAL** — Primary tool/protocol interface for Heretek Swarm |

**Key Specs:**
- SEP-1686 (Tasks)
- SEP-1865 (MCP Apps — interactive UI)
- SEP-2133 (Extensions framework)

### A2A (Agent-to-Agent)
**URL:** [a2aproject/A2A](https://github.com/a2aproject/A2A)

| Aspect | Details |
|--------|---------|
| **Description** | Open standard for agent interoperability. JSON-RPC based. |
| **Adoption** | Google ADK native, Microsoft adopted May 2025, Linux Foundation |
| **Relevance** | **HIGH** — Inter-agent communication |

### ACP (Agent Communication Protocol)
**URL:** [agentcommunicationprotocol.dev](https://agentcommunicationprotocol.dev)

| Aspect | Details |
|--------|---------|
| **Description** | REST-based agent interoperability. Framework-agnostic. |
| **Strength** | Works with BeeAI, LangChain, CrewAI, or custom |
| **Relevance** | **HIGH** — Complementary to MCP for A2A |

### AGENTS.md
**URL:** [agents.md](https://agents.md/)

| Aspect | Details |
|--------|---------|
| **Description** | Open Markdown spec for AI coding agent context. "README for agents." |
| **Governance** | Linux Foundation, Agentic AI Foundation |
| **Relevance** | **HIGH** — Base layer for project-specific agent instructions |

---

## 9. Strategic Synthesis

### Heretek Swarm Architecture Mapping

| Phase | Component | Recommended Tech | Source |
|-------|-----------|------------------|--------|
| **I: Substrate** | Event Mesh | NATS/JetStream | Validated |
| **I: Substrate** | Agent Orchestration | Google ADK + LangGraph | Tier 1 |
| **I: Substrate** | Inter-Agent Messaging | HXA Connect | Tier 1 |
| **II: Global Workspace** | Memory | Mem0 + Hindsight pattern | Tier 1 |
| **II: Global Workspace** | Consciousness Metrics | Phi^C + OpenTelemetry | Research |
| **III: Consensus/Tribunal** | Governance | ZoD + AgentCity SoP | Tier 1 |
| **III: Consensus/Tribunal** | Self-Healing | VIGIL-inspired loop | Tier 1 |
| **III: Consensus/Tribunal** | Deliberation | Chorus AI-DLC + HXA threads | Tier 1 |
| **IV: Autopoiesis** | Orchestration | Kelos TaskSpawners | Tier 1 |
| **IV: Autopoiesis** | Sandboxing | OpenShell | Research |
| **V: Emergence** | Tracing | OpenLLMetry/Traccia | Tier 1 |
| **V: Emergence** | Attribution | Shapley values | Research |

### Critical Ecosystem Gaps Identified

1. **No Python-based Chorus-equivalent** — Water is closest but lacks role-based session management
2. **No 23-agent swarm reference** — Most projects top out at 3-5 agents
3. **No consciousness-inspired memory** — LACP's mycelium model is closest
4. **No A2A-first architecture** — Most treat A2A/MCP as integration, not core primitive

### Immediate Recommendations

| Priority | Action | Rationale |
|----------|--------|----------|
| **1** | Evaluate **Google ADK** for Phase I actor wiring | Native A2A + MCP, hierarchical delegation |
| **2** | Prototype **HXA Connect** for Tribunal threads | Direct fit with thread state machine |
| **3** | Implement **VIGIL-inspired** Sentinel self-healing | observe→diagnose→prescribe→intervene→verify |
| **4** | Deploy **OpenTelemetry** cognitive tracing | Production-ready, GenAI conventions |
| **5** | Adopt **Water's** layered memory model | ORG > PROJECT > USER > SESSION > AUTO_LEARNED |

### Heretek Swarm 23-Agent Tier Mapping

| Tier | Agents | Reference Implementation |
|------|--------|------------------------|
| **Tier 1: Core Triad** | Steward, Alpha, Beta, Charlie | Chorus PM/Dev/Admin roles |
| **Tier 2: Support** | Historian, Metis, Empath, Perceiver, Echo | DeerFlow skills system |
| **Tier 3: Exploration** | Explorer, Examiner, Dreamer, Coder | agent-swarm lead/worker |
| **Tier 4: Safety** | Sentinel, Sentinel-Prime, Arbiter | VIGIL + ZoD |
| **Tier 5: Coordination** | Coordinator, Nexus, Catalyst, Chronos | Kelos TaskSpawners |
| **Tier 6: Enhancement** | Prism, Habit-Forge, Perceiver+ | LACP mycelium memory |

---

## Sources

### Frameworks
- [Google ADK](https://github.com/google/adk-python)
- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [MetaGPT](https://github.com/FoundationAgents/MetaGPT)
- [DeerFlow](https://github.com/bytedance/deer-flow)
- [Hive](https://github.com/aden-hive/hive)
- [AgentScope](https://github.com/agentscope-ai/agentscope)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [AG2](https://github.com/ag2ai/ag2)

### Harnesses (Tier 1)
- [Chorus](https://github.com/Chorus-AIDLC/Chorus)
- [Water](https://github.com/manthanguptaa/water)
- [LACP](https://github.com/0xNyk/lacp)
- [agent-swarm](https://github.com/desplega-ai/agent-swarm)
- [Gastown](https://github.com/gastownhall/gastown)
- [HXA Connect](https://github.com/coco-xyz/hxa-connect)
- [Bindu](https://github.com/GetBindu/Bindu)
- [Kelos](https://github.com/kelos-dev/kelos)

### Protocols
- [MCP](https://modelcontextprotocol.io)
- [A2A Protocol](https://github.com/a2aproject/A2A)
- [ACP](https://agentcommunicationprotocol.dev)
- [AGENTS.md](https://agents.md/)

### Observability
- [OpenLLMetry](https://github.com/traceloop/openllmetry)
- [Traccia](https://github.com/traccia-ai/traccia-py)
- [OpenLit](https://github.com/openlit/openlit)

### Governance & Safety
- [ZoD](https://github.com/bluvibytes/zone-of-distrust)
- [AgentGuard](https://github.com/Roboter-Schlafen-Nicht/agentguard)
- [Aegis](https://arxiv.org/pdf/2603.16938)
- [VIGIL](https://arxiv.org/pdf/2512.07094)

---

*Document generated 2026-04-12 via comprehensive ecosystem audit (100+ repositories)*
