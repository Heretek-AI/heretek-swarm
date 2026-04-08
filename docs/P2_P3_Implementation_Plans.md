# P2: Circular Dependencies Fix Plan

## Executive Summary

This document details the implementation plan for resolving circular dependency cycles identified in the Heretek Swarm codebase. The primary cycles involve the API layer, LLM providers, embedding providers, and frontend components.

---

## Cycle 1: API ↔ llm.providers ↔ API

### Current State

```python
# api/configuration.py imports directly from factory
from heretek_swarm.llm.providers.factory import (
    create_llm_provider,
    get_provider_class,
    list_available_providers,
)

from heretek_swarm.embeddings.providers.factory import (
    create_embedding_provider,
    get_provider_class,
    list_available_providers,
)
```

**Root Cause**: The API configuration module directly imports from provider factories, creating a tight coupling that can cause import-time circular dependencies if the API ever needs to be imported from within those factories.

### Solution: Dependency Inversion with Abstract Interfaces

**Step 1: Create Provider Interface Layer**

```python
# src/heretek_swarm/interfaces/providers.py
"""Abstract interfaces for LLM and embedding providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> Any:
        """Generate a completion."""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> Any:
        """Generate a chat completion."""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings."""
        pass


class EmbeddingProviderInterface(ABC):
    """Abstract interface for embedding providers."""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for a single text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
```

**Step 2: Create Provider Registry Interface**

```python
# src/heretek_swarm/interfaces/registry.py
"""Provider registry interface for lazy resolution."""

from typing import Dict, Optional, Type
from .providers import LLMProviderInterface, EmbeddingProviderInterface


class ProviderRegistryInterface(ABC):
    """Abstract registry for provider management."""
    
    @abstractmethod
    def get_llm_provider(self, name: str) -> Optional[LLMProviderInterface]:
        """Get an LLM provider by name."""
        pass
    
    @abstractmethod
    def get_embedding_provider(self, name: str) -> Optional[EmbeddingProviderInterface]:
        """Get an embedding provider by name."""
        pass
    
    @abstractmethod
    def list_llm_providers(self) -> List[str]:
        """List available LLM providers."""
        pass
    
    @abstractmethod
    def list_embedding_providers(self) -> List[str]:
        """List available embedding providers."""
        pass
```

**Step 3: Refactor API Configuration to Use Interfaces**

```python
# src/heretek_swarm/api/configuration.py - Modified imports
from heretek_swarm.interfaces.registry import ProviderRegistryInterface
from heretek_swarm.interfaces.providers import LLMProviderInterface, EmbeddingProviderInterface


def get_provider_registry() -> ProviderRegistryInterface:
    """Lazy initialization of provider registry."""
    # Import here to avoid circular dependency at module load time
    from heretek_swarm.llm.providers.factory import get_provider_registry as _get_reg
    return _get_reg()
```

**Step 4: Add Lazy Import Utility**

```python
# src/heretek_swarm/utils/lazy_imports.py
"""Lazy import utilities to break circular dependencies."""

from typing import Any, Callable, TypeVar, Optional
from functools import wraps
import importlib

T = TypeVar('T')


class LazyImport:
    """Lazy import wrapper that defers import until first access."""
    
    def __init__(self, import_path: str):
        self._import_path = import_path
        self._module: Optional[Any] = None
    
    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            self._module = importlib.import_module(self._import_path)
        return getattr(self._module, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        return self._module(*args, **kwargs)


def lazy_import(import_path: str) -> Callable[[str], Any]:
    """Decorator for lazy importing."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            module_path, attr_name = import_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            attr = getattr(module, attr_name)
            return attr(*args, **kwargs)
        return wrapper
    return decorator
```

### Implementation Order

| Phase | Task | Effort |
|-------|------|--------|
| 1 | Create `src/heretek_swarm/interfaces/` directory | 1 day |
| 2 | Implement `interfaces/providers.py` | 2 days |
| 3 | Implement `interfaces/registry.py` | 1 day |
| 4 | Create `utils/lazy_imports.py` | 1 day |
| 5 | Refactor API configuration imports | 2 days |
| 6 | Add type hints and validation tests | 1 day |

---

## Cycle 2: API ↔ embeddings.providers ↔ API

### Analysis

The same solution applies as Cycle 1 since both LLM providers and embedding providers follow identical patterns. The `EmbeddingProviderInterface` in the interfaces layer will handle both cases.

### Additional Changes

1. **Factory Registration**: Modify `src/heretek_swarm/embeddings/providers/factory.py` to implement the interface
2. **API Endpoint Updates**: Update `api/configuration.py` endpoints to use the interface-based registry

---

## Cycle 3: Frontend - UI ↔ Agents ↔ Settings ↔ UI

### Current State Analysis

```typescript
// App.tsx imports pages directly
import { HomePage } from './components/Home/HomePage';
import { AgentsPage } from './components/Agents/AgentsPage';
import { SettingsPage } from './components/Settings/SettingsPage';

// Components import settings
import { useDeveloperMode } from '../Settings/DeveloperModeToggle';
```

**Root Cause**: 
1. Direct component imports create coupling
2. Shared state hooks are imported across components without proper isolation
3. No clear boundary between feature modules

### Solution: Feature Module Pattern with Context Isolation

**Step 1: Create Feature Context Pattern**

```typescript
// src/contexts/FeatureContext.tsx
import React, { createContext, useContext, ReactNode } from 'react';

interface FeatureFlags {
  developerMode: boolean;
  advancedAnalytics: boolean;
  experimentalFeatures: boolean;
}

interface FeatureContextValue {
  flags: FeatureFlags;
  setFlag: (flag: keyof FeatureFlags, value: boolean) => void;
}

const FeatureContext = createContext<FeatureContextValue | null>(null);

export const FeatureProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [flags, setFlags] = React.useState<FeatureFlags>({
    developerMode: false,
    advancedAnalytics: false,
    experimentalFeatures: false,
  });

  const setFlag = (flag: keyof FeatureFlags, value: boolean) => {
    setFlags(prev => ({ ...prev, [flag]: value }));
  };

  return (
    <FeatureContext.Provider value={{ flags, setFlag }}>
      {children}
    </FeatureContext.Provider>
  );
};

export const useFeatures = () => {
  const context = useContext(FeatureContext);
  if (!context) {
    throw new Error('useFeatures must be used within FeatureProvider');
  }
  return context;
};
```

**Step 2: Create Feature-Based Lazy Loading**

```typescript
// src/components/FeatureLoader.tsx
import React, { Suspense, lazy, ReactComponentType } from 'react';

interface FeatureConfig {
  path: string;
  component: ReactComponentType<any>;
}

const featureRegistry: Record<string, FeatureConfig> = {};

export const registerFeature = (name: string, config: FeatureConfig) => {
  featureRegistry[name] = config;
};

export const useFeature = (name: string) => {
  const Feature = featureRegistry[name]?.component;
  if (!Feature) {
    throw new Error(`Feature "${name}" not registered`);
  }
  return Feature;
};

export const LazyFeature: React.FC<{ name: string; fallback?: React.ReactNode }> = ({ 
  name, 
  fallback = <div>Loading...</div> 
}) => {
  const Feature = useFeature(name);
  return (
    <Suspense fallback={fallback}>
      <Feature />
    </Suspense>
  );
};
```

**Step 3: Refactor App.tsx with Lazy Loading**

```typescript
// App.tsx - Refactored
import React, { Suspense, lazy } from 'react';
import { FeatureProvider } from './contexts/FeatureContext';
import LoadingSpinner from './components/UI/LoadingSpinner';

// Lazy load all pages
const HomePage = lazy(() => import('./components/Home/HomePage'));
const AgentsPage = lazy(() => import('./components/Agents/AgentsPage'));
const SettingsPage = lazy(() => import('./components/Settings/SettingsPage'));
const ConsciousnessPage = lazy(() => import('./components/Consciousness/ConsciousnessPage'));
const LogsPage = lazy(() => import('./components/Logs/LogsPage'));

const pages: Record<string, React.ComponentType> = {
  home: HomePage,
  agents: AgentsPage,
  settings: SettingsPage,
  consciousness: ConsciousnessPage,
  logs: LogsPage,
};

export default function App() {
  const [currentPage, setCurrentPage] = useState('home');
  
  const PageComponent = pages[currentPage];
  
  return (
    <FeatureProvider>
      <Suspense fallback={<LoadingSpinner />}>
        <PageComponent onNavigate={setCurrentPage} />
      </Suspense>
    </FeatureProvider>
  );
}
```

**Step 4: Decouple Settings Dependencies**

```typescript
// Instead of importing useDeveloperMode directly
// Use the context-based approach

// OLD (tightly coupled):
import { useDeveloperMode } from '../Settings/DeveloperModeToggle';

// NEW (decoupled via context):
import { useFeatures } from '../../contexts/FeatureContext';

const MyComponent = () => {
  const { flags } = useFeatures();
  // Use flags.developerMode
};
```

### Implementation Order

| Phase | Task | Effort |
|-------|------|--------|
| 1 | Create `contexts/FeatureContext.tsx` | 1 day |
| 2 | Implement `FeatureLoader.tsx` with lazy loading | 2 days |
| 3 | Refactor App.tsx with lazy page loading | 1 day |
| 4 | Migrate Settings imports to use FeatureContext | 2 days |
| 5 | Add loading states and error boundaries | 1 day |
| 6 | Test all navigation flows | 1 day |

---

## Verification Strategy

After implementing the fixes, use these verification methods:

1. **Import Cycle Detection**: Run `python -c "from heretek_swarm.api.main import app"` to confirm no import errors
2. **Static Analysis**: Use `ruff check src/heretek_swarm --select=F401` for unused imports
3. **Runtime Tests**: Execute API endpoint tests to verify provider functionality
4. **Frontend Tests**: Run `npm run build` to verify no circular dependency errors

---

# P3: Long Functions Refactor Plan

## Executive Summary

This document details decomposition strategies for the 10 functions/components identified as exceeding 150 lines. Each refactoring plan includes specific extraction strategies and target complexity reduction.

---

## Python Functions Refactoring

### 1. mcp_tools._register_default_tools (213 lines)

**Current State**: Lines 290-502 in `src/heretek_swarm/tools/mcp_tools.py`

**Problems**:
- Single method registers 14 different tools
- Each tool registration is nearly identical code
- Handler methods defined inline

**Decomposition Strategy**:

**Extract Tool Registrars by Category**:

```python
# New file: src/heretek_swarm/tools/registrars.py
"""Tool registration helpers by category."""

from typing import Callable, Dict, Any
from .mcp_tools import MCPToolDefinition, MCPToolRegistry


class MemoryToolsRegistrar:
    """Register memory-related MCP tools."""
    
    def __init__(self, registry: MCPToolRegistry):
        self._registry = registry
    
    def register(self) -> None:
        """Register all memory tools."""
        self._registry.register(MCPToolDefinition(
            name="memory_store",
            description="Store information in collective memory...",
            input_schema={...},
            handler=self._handle_memory_store,
            category="memory"
        ))
        self._registry.register(MCPToolDefinition(
            name="memory_retrieve",
            ...
        ))
    
    async def _handle_memory_store(self, arguments: Dict, context: Dict) -> Dict:
        ...


class CommunicationToolsRegistrar:
    """Register communication-related MCP tools."""
    
    def __init__(self, registry: MCPToolRegistry):
        self._registry = registry
    
    def register(self) -> None:
        """Register all communication tools."""
        # agent_message, agent_handoff


class ConsensusToolsRegistrar:
    """Register consensus-related MCP tools."""
    
    def __init__(self, registry: MCPToolRegistry):
        self._registry = registry
    
    def register(self) -> None:
        """Register all consensus tools."""
        # consensus_propose, consensus_vote


class RAGToolsRegistrar:
    """Register RAG-related MCP tools."""
    
    def __init__(self, registry: MCPToolRegistry):
        self._registry = registry
    
    def register(self) -> None:
        """Register all RAG tools."""
        # rag_query, rag_ingest


class IntegrationToolsRegistrar:
    """Register integration-related MCP tools."""
    
    def __init__(self, registry: MCPToolRegistry):
        self._registry = registry
    
    def register(self) -> None:
        """Register all integration tools."""
        # external_api_call, notification_send


class WorkflowToolsRegistrar:
    """Register workflow-related MCP tools."""
    
    def __init__(self, registry: MCPToolRegistry):
        self._registry = registry
    
    def register(self) -> None:
        """Register all workflow tools."""
        # workflow_start, workflow_status
```

**Refactored CoreMCPTools**:

```python
class CoreMCPTools:
    def __init__(self, memory_system=None, rag_pipeline=None, ...):
        self.memory = memory_system
        self.rag = rag_pipeline
        self.consensus = consensus_engine
        self.event_mesh = event_mesh
        self.registry = MCPToolRegistry()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default tools via specialized registrars."""
        registrars = [
            MemoryToolsRegistrar(self.registry),
            CommunicationToolsRegistrar(self.registry),
            ConsensusToolsRegistrar(self.registry),
            RAGToolsRegistrar(self.registry),
            IntegrationToolsRegistrar(self.registry),
            WorkflowToolsRegistrar(self.registry),
        ]
        
        for registrar in registrars:
            registrar.register()
```

**Target**: Reduce from 213 lines to ~30 lines (registration logic only)

---

### 2. channels/registry._setup_default_channels (202 lines)

**Current State**: Lines 150-351 in `src/heretek_swarm/channels/registry.py`

**Problems**:
- Creates 14 channels in a single method
- Each channel registration is verbose
- No separation between internal, system, and external channels

**Decomposition Strategy**:

**Extract Channel Definitions to Data Module**:

```python
# New file: src/heretek_swarm/channels/defaults.py
"""Default channel and group definitions."""

from typing import List
from .registry import ChannelDefinition, ChannelType, QoSLevel


def get_internal_channels() -> List[ChannelDefinition]:
    """Get default internal agent channels."""
    return [
        ChannelDefinition(
            name="swarm.internal.triad",
            description="Core governance deliberation channel",
            channel_type=ChannelType.INTERNAL,
            subscribers=["steward", "alpha", "beta", "charlie"],
            message_types=["proposal", "analysis", "validation", ...],
            qos=QoSLevel.AT_LEAST_ONCE,
            retention="24h",
            priority="high",
        ),
        # ... more internal channels
    ]


def get_system_channels() -> List[ChannelDefinition]:
    """Get default system channels."""
    return [
        ChannelDefinition(
            name="swarm.system.health",
            description="Health monitoring channel",
            ...
        ),
        # ... more system channels
    ]


def get_external_channels() -> List[ChannelDefinition]:
    """Get default external integration channels."""
    return [...]
```

**Refactored ChannelRegistry**:

```python
class ChannelRegistry:
    def __init__(self):
        self._channels: Dict[str, ChannelDefinition] = {}
        self._agent_subscriptions: Dict[str, Set[str]] = {}
        self._message_handlers: Dict[str, callable] = {}
        self._stats: Dict[str, Dict] = {}
        self._setup_default_channels()
    
    def _setup_default_channels(self):
        """Set up default channels from configuration."""
        from .defaults import (
            get_internal_channels,
            get_system_channels,
            get_external_channels,
        )
        
        for channel in get_internal_channels():
            self.register(channel)
        
        for channel in get_system_channels():
            self.register(channel)
        
        for channel in get_external_channels():
            self.register(channel)
```

**Target**: Reduce from 202 lines to ~25 lines

---

### 3. security/guardrails.validate_input (162 lines)

**Current State**: Lines 115-277 in `src/heretek_swarm/security/guardrails.py`

**Problems**:
- Multiple validation checks in single method
- No separation between different validation categories
- Complex nested logic

**Decomposition Strategy**:

**Create Validation Strategy Pattern**:

```python
# Add to guardrails.py

class InputValidator(ABC):
    """Base class for input validators."""
    
    @abstractmethod
    async def validate(self, text: str, config: GuardrailsConfig) -> Optional[ValidationResult]:
        """Validate input and return result if invalid."""
        pass


class LengthValidator(InputValidator):
    """Validates input length constraints."""
    
    async def validate(self, text: str, config: GuardrailsConfig) -> Optional[ValidationResult]:
        if len(text) < config.min_input_length:
            return ValidationResult(valid=False, reason="Input too short")
        if len(text) > config.max_input_length:
            return ValidationResult(valid=False, reason="Input too long")
        return None


class BlockedPatternValidator(InputValidator):
    """Validates against blocked patterns."""
    
    def __init__(self, patterns: List[re.Pattern]):
        self._patterns = patterns
    
    async def validate(self, text: str, config: GuardrailsConfig) -> Optional[ValidationResult]:
        for pattern in self._patterns:
            match = pattern.search(text)
            if match:
                return ValidationResult(valid=False, reason=...)
        return None


class PersonalInfoValidator(InputValidator):
    """Detects personal information in input."""
    
    async def validate(self, text: str, config: GuardrailsConfig) -> Optional[ValidationResult]:
        if not config.block_personal_info:
            return None
        
        # Check email, phone, SSN, API keys
        ...


class CodeExecutionValidator(InputValidator):
    """Detects code execution attempts."""
    
    async def validate(self, text: str, config: GuardrailsConfig) -> Optional[ValidationResult]:
        if not config.block_code_execution:
            return None
        
        # Check shell commands, Python exec patterns
        ...


class AllowedPatternValidator(InputValidator):
    """Validates against allowed patterns."""
    
    async def validate(self, text: str, config: GuardrailsConfig) -> Optional[ValidationResult]:
        if not config.allowed_patterns:
            return None
        
        # Check against allowed patterns
        ...
```

**Refactored GuardrailsSystem**:

```python
class GuardrailsSystem:
    def __init__(self, config: Optional[GuardrailsConfig] = None):
        self.config = config or GuardrailsConfig()
        self._blocked_patterns = self._compile_blocked_patterns()
        self._validators = self._build_validators()
    
    def _build_validators(self) -> List[InputValidator]:
        return [
            LengthValidator(),
            BlockedPatternValidator(self._blocked_patterns),
            PersonalInfoValidator(),
            CodeExecutionValidator(),
            AllowedPatternValidator(),
        ]
    
    async def validate_input(self, input_text: str, agent_id: Optional[str] = None) -> ValidationResult:
        """Run all validators in sequence."""
        for validator in self._validators:
            result = await validator.validate(input_text, self.config)
            if result and not result.valid:
                return result
        
        return ValidationResult(valid=True)
```

**Target**: Reduce from 162 lines to ~40 lines

---

### 4. orchestration/heavyswarm.execute (155 lines)

**Current State**: Located in `src/heretek_swarm/orchestration/heavyswarm.py`

**Decomposition Strategy**:

Based on general execution pattern - likely involves workflow phases. Extract phase handlers:

```python
class HeavySwarmExecutor:
    async def execute(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute heavyswarm workflow."""
        # Delegate to phase handlers
        return await PhaseRunner([
            AnalysisPhase(),
            ResearchPhase(),
            SynthesisPhase(),
            ValidationPhase(),
        ]).run(topic, context)
```

---

### 5. actors/handoff.execute_handoff (153 lines)

**Current State**: Located in `src/heretek_swarm/actors/handoff.py`

**Decomposition Strategy**:

Based on handoff pattern - extract validation, context transfer, and notification as separate methods:

```python
class HandoffManager:
    async def execute_handoff(self, from_agent: str, to_agent: str, context: Dict) -> Dict:
        # Validate handoff
        validation = await self._validate_handoff(from_agent, to_agent, context)
        if not validation.valid:
            return validation
        
        # Transfer context
        transferred = await self._transfer_context(from_agent, to_agent, context)
        
        # Notify agents
        await self._notify_agents(from_agent, to_agent, transferred)
        
        return {"success": True, "handoff_id": ...}
    
    async def _validate_handoff(self, from_agent, to_agent, context):
        # Extract validation logic
    
    async def _transfer_context(self, from_agent, to_agent, context):
        # Extract context transfer logic
    
    async def _notify_agents(self, from_agent, to_agent, context):
        # Extract notification logic
```

---

### 6. memory/tiering._migrate_memory (151 lines)

**Current State**: Located in `src/heretek_swarm/memory/tiering.py`

**Decomposition Strategy**:

Extract migration strategies:

```python
class MemoryTiering:
    async def _migrate_memory(self, memory_entry: MemoryEntry, source_tier: str, target_tier: str) -> None:
        """Migrate memory between tiers."""
        migration_strategy = self._get_migration_strategy(source_tier, target_tier)
        await migration_strategy.execute(memory_entry)
    
    def _get_migration_strategy(self, source: str, target: str) -> MigrationStrategy:
        strategies = {
            ("ephemeral", "persistent"): EphemeralToPersistentStrategy(),
            ("persistent", "ephemeral"): PersistentToEphemeralStrategy(),
            # ...
        }
        return strategies.get((source, target), DefaultMigrationStrategy())
```

---

## Frontend Components Refactoring

### 7. WorkflowBuilder.tsx (559 lines)

**Current Problems**:
- Canvas, node configuration, and toolbar all in one component
- No separation between state management and rendering
- Event handlers inline

**Decomposition Strategy**:

```
WorkflowBuilder/
├── WorkflowBuilder.tsx          # Container, ~100 lines
├── WorkflowCanvas.tsx           # Canvas rendering, ~150 lines  
├── NodePalette.tsx              # Node selection panel, ~80 lines
├── NodeConfigPanel.tsx          # Configuration sidebar, ~120 lines
├── WorkflowToolbar.tsx          # Toolbar actions, ~60 lines
├── hooks/
│   ├── useWorkflowState.ts      # State management
│   ├── useNodeDrag.ts           # Drag and drop logic
│   └── useWorkflowValidation.ts # Validation logic
└── types/
    └── index.ts                 # Type definitions
```

**Extract State Management**:

```typescript
// hooks/useWorkflowState.ts
import { create } from 'zustand';

interface WorkflowState {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  selectedNode: string | null;
  // ... actions
}

export const useWorkflowState = create<WorkflowState>((set) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),
  // ...
}));
```

**Target**: Reduce from 559 lines to ~100 lines (container only)

---

### 8. ConsciousnessDashboard.tsx (231 lines)

**Decomposition Strategy**:

```
ConsciousnessDashboard/
├── ConsciousnessDashboard.tsx  # Container
├── ConsciousnessMetrics.tsx     # Phi, attention displays
├── GlobalStateChart.tsx         # State visualization
├── IntegrationMatrix.tsx        # Integration metrics
└── hooks/
    └── useConsciousnessData.ts  # Data fetching
```

**Target**: Reduce to ~80 lines container

---

### 9. SwarmHealthDashboard.tsx (211 lines)

**Decomposition Strategy**:

```
SwarmHealthDashboard/
├── SwarmHealthDashboard.tsx     # Container
├── AgentHealthGrid.tsx          # Agent status grid
├── SystemHealthOverview.tsx     # Overall health
├── AlertPanel.tsx               # Active alerts
└── hooks/
    └── useHealthData.ts         # Health data
```

**Target**: Reduce to ~70 lines container

---

### 10. AgentsPage.tsx (207 lines)

**Decomposition Strategy**:

```
AgentsPage/
├── AgentsPage.tsx               # Container
├── AgentList.tsx                # Agent table/list
├── AgentDetail.tsx              # Detail view
├── AgentCreationModal.tsx       # Create agent
├── AgentFilters.tsx             # Filter controls
└── hooks/
    ├── useAgents.ts             # Agent data
    └── useAgentActions.ts       # CRUD operations
```

**Target**: Reduce to ~80 lines container

---

## Implementation Priority

| Priority | Function | Current Lines | Target Lines | Effort |
|----------|----------|---------------|--------------|--------|
| 1 | _register_default_tools | 213 | ~30 | 2 days |
| 2 | _setup_default_channels | 202 | ~25 | 1 day |
| 3 | validate_input | 162 | ~40 | 2 days |
| 4 | WorkflowBuilder.tsx | 559 | ~100 | 3 days |
| 5 | ConsciousnessDashboard.tsx | 231 | ~80 | 2 days |
| 6 | execute_handoff | 153 | ~50 | 1 day |
| 7 | _migrate_memory | 151 | ~40 | 1 day |
| 8 | execute | 155 | ~50 | 1 day |
| 9 | SwarmHealthDashboard.tsx | 211 | ~70 | 2 days |
| 10 | AgentsPage.tsx | 207 | ~80 | 2 days |

---

## Quality Gates

After each refactoring:

1. **Test Coverage**: Ensure existing tests still pass
2. **Type Safety**: Update type hints for extracted modules
3. **Documentation**: Add docstrings for new classes and methods
4. **Linting**: Run `ruff check` and fix any new issues
5. **Bundle Size** (Frontend): Verify no significant increase in bundle size