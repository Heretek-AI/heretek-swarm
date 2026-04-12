# Technology Stack

**Analysis Date:** 2026-04-12

## Languages

**Primary:**
- Python 3.11+ - Core agent runtime and API backend
- TypeScript 5.3+ - Dashboard frontend and Electron desktop app

**Secondary:**
- JavaScript (ES2020) - Frontend components

## Runtime

**Python Environment:**
- Python 3.11, 3.12
- Package manager: pip/setuptools
- Lockfile: `requirements.txt` (when generated)

**Node.js Environment:**
- Node.js runtime for dashboard
- Package manager: npm
- Lockfile: `package-lock.json`

## Frameworks

**Python - Agent & API:**
- **swarms 5.0+** - Multi-agent framework foundation
- **FastAPI 0.109+** - REST API framework
- **Starlette 0.27+** - ASGI web toolkit (underlying FastAPI)
- **uvicorn 0.25+** - ASGI server
- **websockets 12.0+** - WebSocket support

**Python - CLI & Configuration:**
- **click 8.1+** - CLI framework
- **pydantic 2.0+** - Data validation and settings

**Python - Desktop/Agent Frameworks:**
- **autogen** - AutoGen agent framework integration
- **crewai** - CrewAI agent framework integration
- **langgraph** - LangGraph workflow integration

**TypeScript - Frontend:**
- **React 18.2+** - UI framework
- **Vite 5.0+** - Build tool and dev server
- **react-router-dom 6.21+** - Client-side routing
- **Tailwind CSS 3.4+** - Utility-first CSS
- **Zustand 4.4+** - State management
- **lucide-react 0.303+** - Icon library

**TypeScript - Desktop:**
- **Electron 28+** - Desktop application framework
- **electron-builder 24+** - Electron packaging

## Key Dependencies

**Agent Intelligence:**
- **mem0ai 1.0+** - Long-term memory for agents
- **opentelemetry-api/sdk 1.22+** - Observability/tracing
- **opentelemetry-exporter-otlp 1.22+** - OTLP trace export

**Data & Storage:**
- **redis 5.0+** - Caching and pub/sub
- **qdrant-client 1.7+** - Vector database client
- **httpx 0.25+** - Async HTTP client

**Reliability:**
- **structlog 24.1+** - Structured logging
- **tenacity 8.2+** - Retry logic
- **circuitbreaker 2.0+** - Circuit breaker pattern

**LLM Providers:**
- **openai** - OpenAI API integration
- **anthropic** - Anthropic/Claude integration
- Custom providers: minimax, ollama, llamacpp, lemonade, zai, openai_compatible

**Testing:**
- **pytest 8.0+** - Test framework
- **pytest-asyncio 0.23+** - Async test support
- **pytest-cov 4.1+** - Coverage reporting
- **pytest-xdist 3.5+** - Parallel test execution
- **hypothesis 6.98+** - Property-based testing
- **faker 24.0+** - Test data generation

**Code Quality:**
- **ruff 0.2+** - Linter and formatter
- **mypy 1.8+** - Static type checking
- **pre-commit 3.6+** - Git hooks

**TypeScript Build:**
- **electron-log 5.0+** - Electron logging
- **electron-store 8.1+** - Electron persistent storage
- **clsx 2.1+** - Class name utility
- **tailwind-merge 2.2+** - Tailwind merge utility

## Configuration

**Python Configuration:**
- `pyproject.toml` - Project metadata and dependencies
- `[tool.pytest.ini_options]` - Test configuration
- `[tool.ruff]` - Linter configuration
- `[tool.mypy]` - Type checker configuration
- `[tool.coverage]` - Coverage configuration

**TypeScript Configuration:**
- `tsconfig.json` - TypeScript base config
- `vite.config.ts` - Vite bundler configuration
- `tailwind.config.js` - Tailwind CSS configuration
- `postcss.config.js` - PostCSS configuration

**Environment:**
- `.env.example` - Template for environment variables
- Environment variables for API keys, URLs, and feature flags

## Platform Requirements

**Development:**
- Python 3.11+
- Node.js 18+
- npm or yarn
- Redis server (for local development)
- PostgreSQL (for persistent storage)
- Qdrant (for vector storage)
- NATS server (for message broker)

**Production:**
- Linux server (tested on Linux 6.x)
- Python 3.11+ runtime
- Node.js 18+ runtime (for dashboard)
- Redis 5.0+
- PostgreSQL 14+
- Qdrant (vector database)
- NATS server 3.0+

**Desktop App:**
- macOS, Windows, or Linux
- Electron 28+

---

*Stack analysis: 2026-04-12*
