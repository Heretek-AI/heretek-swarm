# Configuration Migration Guide

## Step 4: Dynamic Configuration & Multi-Provider LLM Support

This guide explains how to migrate from `.env` file-based configuration to the new database-backed configuration system with multi-provider LLM support.

## Overview

The new configuration system provides:

- **Database-backed storage**: All user-facing configurations stored in PostgreSQL
- **Multi-provider LLM support**: OpenAI, Ollama, llama.cpp, Z.AI, MiniMax, lemonade-server, and OpenAI-compatible APIs
- **Multi-provider embedding support**: OpenAI, Ollama, and compatible APIs
- **UI-based management**: Configure providers through the dashboard
- **Import/Export**: Backup and restore configurations
- **Audit logging**: Track all configuration changes

## Architecture

### Backend Structure

```
src/heretek_swarm/
├── config/
│   ├── models.py          # Pydantic data models
│   └── service.py         # CRUD operations with caching
├── llm/
│   └── providers/
│       ├── base.py              # Abstract base class
│       ├── openai_provider.py   # OpenAI implementation
│       ├── openai_compatible.py # Generic OpenAI-compatible
│       ├── ollama_provider.py   # Ollama implementation
│       ├── llamacpp_provider.py # llama.cpp implementation
│       ├── zai_provider.py      # Z.AI implementation
│       ├── minimax_provider.py  # MiniMax implementation
│       ├── lemonade_provider.py # lemonade-server implementation
│       └── factory.py           # Provider factory
├── embeddings/
│   └── providers/
│       ├── base.py              # Abstract base class
│       ├── openai_provider.py   # OpenAI embeddings
│       ├── ollama_provider.py   # Ollama embeddings
│       └── factory.py           # Embedding factory
└── api/
    └── configuration.py         # REST API endpoints
```

### Database Schema

The migration creates the following tables:

- `user_configurations` - System-wide settings
- `llm_providers` - LLM provider configurations
- `embedding_providers` - Embedding provider configurations
- `agent_configs` - Per-agent configurations
- `config_audit_log` - Change history
- `config_cache` - Frequently accessed config cache

## Migration Steps

### 1. Run Database Migration

Execute the migration SQL file:

```bash
psql -U postgres -d heretek_swarm -f migrations/009_create_configuration_tables.sql
```

Or if using the application's migration system:

```bash
python -m heretek_swarm.migrations.run 009
```

### 2. Migrate Environment Variables

Use the API endpoint to migrate existing environment variables:

```bash
curl -X POST http://localhost:8000/api/config/migrate-from-env \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Or through the UI:
1. Navigate to Settings → System
2. Click "Migrate from .env"

### 3. Configure LLM Providers

#### Via UI (Recommended)

1. Navigate to Settings → LLM Providers
2. Click "Add Provider"
3. Fill in provider details:
   - **Provider Name**: Unique identifier (e.g., `my-openai`)
   - **Provider Type**: Select from dropdown
   - **Base URL**: API endpoint
   - **API Key**: Authentication key
   - **Default Model**: Model to use by default
4. Click "Add Provider"
5. Test connectivity with the "Test" button

#### Via API

```bash
# Add OpenAI provider
curl -X POST http://localhost:8000/api/config/llm/providers \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "my-openai",
    "provider_type": "openai",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "default_model": "gpt-4o",
    "is_enabled": true,
    "is_default": true
  }'

# Add Ollama provider
curl -X POST http://localhost:8000/api/config/llm/providers \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "local-ollama",
    "provider_type": "ollama",
    "base_url": "http://localhost:11434",
    "default_model": "llama2",
    "is_enabled": true
  }'
```

### 4. Configure Embedding Providers

```bash
# Add OpenAI embedding provider
curl -X POST http://localhost:8000/api/config/embedding/providers \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_name": "my-openai-embeddings",
    "provider_type": "openai",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    "default_model": "text-embedding-3-small",
    "embedding_dimensions": 1536,
    "is_enabled": true,
    "is_default": true
  }'
```

### 5. Update .env File

After migration, your `.env` file should only contain deployment secrets:

```bash
# Keep these in .env (deployment secrets)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/heretek_swarm
REDIS_URL=redis://localhost:6379
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Remove these (now in database)
# OPENAI_API_KEY - moved to database
# RATE_LIMIT_ENABLED - moved to database
# MEMORY_MAX_SIZE - moved to database
# CONSENSUS_MIN_VOTES - moved to database
```

## Provider Configuration Reference

### LLM Provider Types

| Type | Base URL | API Key Required | Notes |
|------|----------|------------------|-------|
| `openai` | https://api.openai.com/v1 | Yes | GPT-4, GPT-3.5 |
| `openai_compatible` | Custom | Optional | vLLM, LocalAI, etc. |
| `ollama` | http://localhost:11434 | No | Local inference |
| `llamacpp` | http://localhost:8080 | No | GGUF models |
| `zai` | https://open.bigmodel.cn/api/paas/v4 | Yes | Zhipu AI GLM models |
| `minimax` | https://api.minimax.chat/v1 | Yes | Requires group_id |
| `lemonade` | http://localhost:5000 | No | lemonade-server |

### Embedding Provider Types

| Type | Base URL | API Key Required | Notes |
|------|----------|------------------|-------|
| `openai` | https://api.openai.com/v1 | Yes | text-embedding-3-small |
| `openai_compatible` | Custom | Optional | Compatible APIs |
| `ollama` | http://localhost:11434 | No | nomic-embed-text |

## API Endpoints

### Configuration Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | List all configurations |
| `/api/config/{key}` | GET | Get specific configuration |
| `/api/config/{key}` | PUT | Update configuration |
| `/api/config` | POST | Create configuration |
| `/api/config/{key}` | DELETE | Delete configuration |

### LLM Providers

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config/llm/providers` | GET | List LLM providers |
| `/api/config/llm/providers/{id}` | GET | Get LLM provider |
| `/api/config/llm/providers` | POST | Create LLM provider |
| `/api/config/llm/providers/{id}` | PUT | Update LLM provider |
| `/api/config/llm/providers/{id}` | DELETE | Delete LLM provider |
| `/api/config/llm/providers/{id}/test` | POST | Test connectivity |
| `/api/config/llm/types` | GET | List available provider types |

### Embedding Providers

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config/embedding/providers` | GET | List embedding providers |
| `/api/config/embedding/providers/{id}` | GET | Get embedding provider |
| `/api/config/embedding/providers` | POST | Create embedding provider |
| `/api/config/embedding/providers/{id}` | PUT | Update embedding provider |
| `/api/config/embedding/providers/{id}` | DELETE | Delete embedding provider |
| `/api/config/embedding/providers/{id}/test` | POST | Test connectivity |
| `/api/config/embedding/types` | GET | List available provider types |

### Import/Export

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config/export` | GET | Export all configurations |
| `/api/config/import` | POST | Import configurations |
| `/api/config/migrate-from-env` | POST | Migrate from environment variables |

## Frontend Components

### Settings Page Structure

```
dashboard/frontend/src/components/Settings/
├── SettingsPage.tsx           # Main settings page with tabs
├── LLMProvidersSection.tsx    # LLM provider management
├── EmbeddingProvidersSection.tsx # Embedding provider management
├── SystemConfigSection.tsx    # System configuration
├── AgentDefaultsSection.tsx   # Agent default settings
├── ImportExportSection.tsx    # Import/export functionality
└── index.ts                   # Component exports
```

### Usage in Dashboard

1. Navigate to Settings in the dashboard
2. Use tabs to switch between sections:
   - **LLM Providers**: Manage LLM connections
   - **Embedding**: Manage embedding models
   - **System**: System-wide settings
   - **Agent Defaults**: Per-agent provider assignments
   - **Import/Export**: Backup and restore

## Testing Provider Connectivity

### Via UI

1. Go to Settings → LLM Providers or Embedding
2. Click "Test" on any provider
3. View test results including latency and response

### Via API

```bash
# Test LLM provider
curl -X POST http://localhost:8000/api/config/llm/providers/{id}/test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, this is a test.",
    "max_tokens": 10
  }'

# Test embedding provider
curl -X POST http://localhost:8000/api/config/embedding/providers/{id}/test \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test sentence for embedding."
  }'
```

## Backup and Restore

### Export Configurations

```bash
# Via API
curl -X GET http://localhost:8000/api/config/export \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -o config-backup.json

# Via UI: Settings → Import/Export → Export Configurations
```

### Import Configurations

```bash
# Via API
curl -X POST http://localhost:8000/api/config/import \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "import_data": { ... },
    "options": {
      "skip_conflicts": true,
      "overwrite_existing": false
    }
  }'

# Via UI: Settings → Import/Export → Select File
```

## Troubleshooting

### Migration Fails

1. Check database connection: `psql -U postgres -d heretek_swarm -c "\dt"`
2. Verify migration file exists: `ls migrations/009_create_configuration_tables.sql`
3. Check for existing tables: Migration is idempotent

### Provider Test Fails

1. Verify base URL is correct
2. Check API key validity
3. Ensure network connectivity
4. Check provider status in health_status field

### Configuration Not Applied

1. Verify provider is enabled (`is_enabled: true`)
2. Check if provider is set as default for its type
3. Restart application if cache needs refresh

## Security Considerations

- API keys are stored encrypted in the database
- Use HTTPS for API communication in production
- Regularly rotate API keys
- Export files contain sensitive data - keep secure
- Audit log tracks all configuration changes

## Next Steps

After completing migration:

1. Test all configured providers
2. Set up agent defaults for each agent type
3. Configure backup schedule for configurations
4. Monitor audit logs for changes
5. Document custom configurations for your team
