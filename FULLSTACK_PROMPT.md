# Full-Featured Dashboard Build: Comprehensive Prompt

## Project Overview

Build a complete, production-ready Heretek Swarm dashboard with a first-time setup wizard, full LLM/external service configuration, and all 23 agents integrated into the visual Workflow Builder.

### Current State

**What Already Exists:**
- ✅ 23 agent implementations in `src/heretek_swarm/actors/` (30 files)
- ✅ 10 LLM providers (OpenAI, Ollama, Z.AI, MiniMax, llama.cpp, lemonade, etc.)
- ✅ FastAPI backend with `/api/agents`, `/api/config`, `/api/workflows` endpoints
- ✅ Frontend React app with ReactFlow-based WorkflowBuilder
- ✅ Basic SetupWizard at `dashboard/frontend/src/components/Setup/SetupWizard.tsx`
- ✅ Settings pages in `dashboard/frontend/src/components/Settings/`
- ✅ Workflow engine, cycle detector, validator

**What Needs Building/Enhancing:**
- ❌ SetupWizard is incomplete (only basic structure, missing full service configuration)
- ❌ WorkflowBuilder AgentNode only shows 11 agents (needs all 23)
- ❌ Settings doesn't persist to backend (needs API integration)
- ❌ No database-backed configuration UI
- ❌ Missing validation for LLM provider credentials
- ❌ No agent health monitoring UI
- ❌ Missing workflow execution history
- ❌ No metrics dashboard integration

---

## Phase 1: Enhanced First-Time Setup Wizard

### Requirements

Create a multi-step setup wizard that:

1. **Welcome Screen**
   - Display system overview and capabilities
   - "Get Started" CTA

2. **Database Connection**
   - PostgreSQL host, port, username, password, database name
   - Test connection button with validation
   - Redis host, port (optional password)
   - Redis test connection

3. **External Services**
   - Qdrant (vector DB): host, port, API key
   - NATS: host, port, credentials
   - Test all connections

4. **LLM Provider Configuration**
   - Provider selection: OpenAI, Anthropic, Ollama, Z.AI, MiniMax, local, custom
   - API key input (masked password field)
   - Model selection per provider
   - Temperature, max_tokens defaults
   - Test chat completion button
   - "Add Another Provider" option

5. **Embedding Provider Configuration**
   - Provider selection (same as LLM + specialized)
   - API key input
   - Model selection
   - Dimension size display
   - Test embedding generation

6. **Agent Configuration**
   - Enable/disable agents by tier
   - Default timeout settings
   - Heartbeat interval

7. **Complete & Verify**
   - Save all configs to database
   - Run health checks
   - Success confirmation

### Implementation

- `dashboard/frontend/src/components/Setup/SetupWizard.tsx` (enhance existing)
- Steps: `welcome` → `database` → `external` → `llm` → `embedding` → `agents` → `complete`
- Use React state for step navigation
- API calls to `/api/config` for persistence
- Validation at each step before proceeding
- Progress indicator at top

> Save step data to server after each step completes (auto-save).

---

## Phase 2: Full LLM & External Service Settings

### Requirements

Create full settings pages for each service category.

#### LLM Providers Page (`/settings/llm`)

```
- List configured providers with status indicators
- Add new provider form
- Edit existing provider
- Delete provider (with confirmation)
- Test chat completion per provider
- Set default provider
- View usage metrics per provider
```

#### Embedding Providers Page (`/settings/embeddings`)

```
- List configured embedding providers
- Add/edit/delete functionality
- Test embedding generation
- Vector dimension settings
- Collection management
```

#### External Services Page (`/settings/external`)

```
- PostgreSQL: connection string, pool settings
- Redis: host, port, password, db
- Qdrant: URL, API key, collections
- NATS: server, credentials, streams
- mem0: API key, user ID
```

#### API Keys Page (`/settings/keys`)

```
- Encrypted key display (show last 4 chars)
- Add new key
- Revoke key
- Key usage audit log
```

### Implementation

- Enhance existing `dashboard/frontend/src/components/Settings/` components
- Add API integration to `/api/config` endpoints
- Use existing `configuration.ts` API client
- Persist all changes to database via ConfigurationService

---

## Phase 3: Workflow Builder - All 23 Agents

### Requirements

Update the WorkflowBuilder to support all 23 agents with full configuration.

#### AgentNode Enhancement

Current: Only 11 agents listed (STEWARD, ALPHA, BETA, CHARLIE, HISTORIAN, EXPLORER, EXAMINER, CODER, DREAMER, EMPATH, CUSTOM)

Add the remaining 12 agents:
- METIS (Strategic Planning)
- PERCEIVER (Sensory Input)
- ECHO (Communication)
- SENTINEL (Safety Guardian)
- SENTINEL-PRIME (Security)
- ARBITER (Conflict Resolution)
- COORDINATOR (Multi-Agent)
- NEXUS (External Integration)
- CATALYST (Change Management)
- CHRONOS (Scheduling)
- PRISM (Multi-Perspective)
- HABIT-FORGE (Optimization)
- PERCEIVER+ (Advanced Analytics)

#### Node Configuration Panel

When agent node is selected, show:
- Agent name (editable)
- Agent type (dropdown, pre-filled)
- System prompt (textarea)
- Temperature (slider: 0-2)
- Max tokens (input)
- Custom instructions (textarea)
- Output validation rules
- Retry configuration

#### Integration with Backend

- Load available agents from `/api/agents/available`
- Save agent configs to workflow definition
- Validate agent compatibility at save time
- Show agent capabilities in tooltip

### Implementation

1. Update `dashboard/frontend/src/components/WorkflowBuilder/types.ts`:
   - Add all AgentType enum values
   - Add all 23 agents
   - Add agent configuration schema

2. Update `AgentNode.tsx`:
   - Support all 23 agent types
   - Add node configuration panel
   - Dynamic handles for connections

3. Update `WorkflowBuilder.tsx`:
   - Load agents from API
   - Add to node palette
   - Validate on save

---

## Phase 4: Agent Monitoring & Metrics

### Requirements

Full agent health dashboard.

#### Agents Overview Page (`/agents`)

```
- Grid of all 23 agents
- Status card per agent: Online/Offline/Error
- Last heartbeat timestamp
- Messages processed count
- CPU/Memory usage
- Quick actions: Start/Stop/Restart
```

#### Agent Detail Page (`/agents/:id`)

```
- Agent information
- Configuration view/edit
- Message inbox preview
- Sent messages log
- Error messages
- Performance metrics
- Behavior profile (if available)
```

#### Agent Logs Page

```
- Real-time log stream per agent
- Filter by log level
- Search functionality
- Export logs
```

### Implementation

- Use existing `/api/agents` endpoints
- Add agent detail pages
- Integrate with observability API

---

## Phase 5: Workflow Execution & History

### Requirements

Complete workflow execution management.

#### Workflows List (`/workflows`)

```
- Saved workflows grid
- Create new workflow button
- Clone workflow
- Delete workflow
- Last execution status
- Quick execute
```

#### Workflow Detail/Editor (`/workflows/:id`)

```
- Full ReactFlow editor
- Node configuration panel
- Edge conditions
- Save workflow
- Execute workflow
- View execution history
```

#### Execution History (`/workflows/:id/history`)

```
- List of executions
- Execution status
- Duration
- Node-by-node results
- Error details
- Re-run execution
- Export results
```

#### Real-time Execution View

```
- Current node highlighted
- Progress indicator
- Cancel execution
- View logs
- Node output in real-time
```

### Implementation

- Use `/api/workflows` endpoints
- Enhance WorkflowBuilder for full editing
- Add execution monitoring
- WebSocket for real-time updates (use existing `/ws`)

---

## Phase 6: Dashboard Layout & Navigation

### Requirements

Complete dashboard shell with proper navigation.

#### Navigation Structure

```
- Dashboard (home)
- Workflows
  - List
  - New
  - Editor
- Agents
  - Overview
  - Detail pages
- Settings
  - General
  - LLM Providers
  - Embeddings
  - External Services
  - API Keys
- Observability
  - Metrics
  - Logs
- Help/Docs
```

#### Layout Components

- Sidebar navigation (collapsible)
- Top header with user info + status
- Breadcrumb navigation
- Page title + actions
- Responsive design
- Toast notifications
- Loading states

### Implementation

- Enhance existing `App.tsx` and routing
- Create layout components
- Add proper breadcrumb routing

---

## Success Criteria

### Must Have

- [ ] SetupWizard completes database connection test
- [ ] SetupWizard configures at least one LLM provider
- [ ] LLM settings page shows all configured providers
- [ ] All 23 agents appear in WorkflowBuilder palette
- [ ] Workflow can be saved and executed
- [ ] Execution results displayed
- [ ] Agent health shown in dashboard

### Should Have

- [ ] All external services configurable via UI
- [ ] Embedding provider configuration
- [ ] Workflow execution history
- [ ] Agent detail pages

### Nice to Have

- [ ] Real-time execution stream
- [ ] Behavior profiling UI
- [ ] consciousness metrics panel
- [ ] Export/import configurations

---

## API Endpoints Reference

Use existing endpoints:

- `GET /api/agents/available` - List available agents
- `POST /api/agents/deploy` - Deploy agent
- `GET /api/config` - Get all config
- `POST /api/config` - Set config
- `GET /api/workflows` - List workflows
- `POST /api/workflows` - Create workflow
- `POST /api/workflows/{id}/execute` - Execute workflow
- `GET /api/observability/metrics` - System metrics

---

## File Structure

```
dashboard/frontend/src/
├── api/
│   ├── agents.ts        (enhance)
│   ├── configuration.ts (enhance)
│   └── workflows.ts    (new)
├── components/
│   ├── Setup/
│   │   └── SetupWizard.tsx    (enhance)
│   ├── Settings/
│   │   ├── LLMSection.tsx (new)
│   │   ├── EmbeddingsSection.tsx (new)
│   │   ├── ExternalSection.tsx (new)
│   │   └── KeysSection.tsx (new)
│   ├── WorkflowBuilder/
│   │   ├── AgentNode.tsx  (enhance)
│   │   └── types.ts    (enhance)
│   └── Agents/
│       ├── AgentGrid.tsx  (new)
│       └── AgentDetail.tsx (new)
├── pages/
│   ├── AgentsPage.tsx      (new)
│   ├── AgentDetailPage.tsx (new)
│   ├── WorkflowsPage.tsx  (new)
│   └── SettingsPage.tsx  (enhance)
└── App.tsx
```

EOFMARKDOWN

Now I have a complete, comprehensive prompt ready for building the full-featured dashboard. The prompt covers:

1. **Enhanced Setup Wizard** - Multi-step wizard for database, external services, LLM/embedding providers
2. **Full Settings Pages** - LLM, embeddings, external services, API keys configuration
3. **23 Agents in Workflow Builder** - All agents from the backend integrated into the visual editor
4. **Agent Monitoring** - Health dashboard and detail pages
5. **Workflow Execution** - Full execution management and history
6. **Dashboard Layout** - Navigation, pages, and proper routing

The prompt includes success criteria (must-have/should-have/nice-to-have), API references, and file structure guidance. Let me finalize the todo: