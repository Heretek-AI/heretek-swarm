# Heretek Swarm - Database Migrations

This directory contains SQL migrations for the Heretek Swarm PostgreSQL database.

## Migrations

### 001_create_swarm_memories.sql
Creates the `swarm_memories` table for long-term memory storage with vector embeddings.

**Features:**
- Vector embeddings using pgvector (1536 dimensions for OpenAI)
- Memory classification (episodic, semantic, working)
- Importance scoring with decay
- Access tracking and statistics
- Automatic cleanup functions

**Tables Created:**
- `swarm_memories` - Main memory storage
- `active_memories` - View for active memories

**Functions Created:**
- `update_memory_access(memory_id)` - Update access statistics
- `decay_memory_importance()` - Decay importance scores over time
- `cleanup_expired_memories()` - Remove expired memories

### 002_create_agent_states.sql
Creates the `agent_states` table for tracking agent runtime state and health.

**Features:**
- Agent health metrics and status
- Consciousness metrics (Phi, IIT, FEP)
- Performance tracking
- Resource usage monitoring

**Tables Created:**
- `agent_states` - Agent runtime state
- `healthy_agents` - View for healthy agents
- `agents_needing_attention` - View for agents requiring intervention

### 003_create_workflow_states.sql
Creates the `workflow_states` table for workflow execution tracking.

**Features:**
- Workflow state and progress tracking
- Checkpointing support
- Lineage tracking (parent/root workflows)
- Error handling and retries

**Tables Created:**
- `workflow_states` - Workflow execution state
- `active_workflows` - View for running workflows
- `workflows_completed_today` - View for recently completed workflows
- `failed_workflows` - View for failed workflows

### 004_create_consensus_votes.sql
Creates tables for multi-agent consensus decision making.

**Features:**
- Proposal creation and management
- Vote tracking with weights
- Quorum and majority requirements
- Automatic vote counting

**Tables Created:**
- `consensus_proposals` - Decision proposals
- `consensus_votes` - Individual agent votes
- `open_proposals` - View for active proposals
- `resolved_proposals` - View for completed proposals

## Qdrant Collections

The `scripts/setup_qdrant_collections.py` script creates vector collections:

| Collection | Vector Size | Purpose |
|------------|-------------|---------|
| heretek_rag | 1536 | RAG document embeddings |
| heretek_memory | 1536 | Agent memory embeddings |
| heretek_semantic | 1536 | Semantic knowledge |
| heretek_context | 1536 | Context embeddings |

## Running Migrations

### Prerequisites

1. PostgreSQL 15+ with pgvector extension
2. psycopg2-binary Python package
3. Database connection configured via `DATABASE_URL` environment variable

### Execute Migrations

```bash
# Run all pending migrations
python scripts/run_migrations.py

# Check migration status
python scripts/run_migrations.py --status

# Dry run (show what would be executed)
python scripts/run_migrations.py --dry-run
```

### Setup Qdrant Collections

```bash
# Requires qdrant-client package
pip install qdrant-client

# Set Qdrant URL (optional, defaults to http://localhost:6333)
export QDRANT_URL=http://localhost:6333

# Run collection setup
python migrations/scripts/setup_qdrant_collections.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://heretek:heretek@localhost:5432/heretek` |
| `QDRANT_URL` | Qdrant vector store URL | `http://localhost:6333` |
| `QDRANT_API_KEY` | Qdrant API key (optional) | - |

## Database Schema

### swarm_memories

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| agent_id | VARCHAR(255) | Owner agent |
| session_id | UUID | Session context |
| content | TEXT | Memory content |
| content_type | VARCHAR(100) | Content MIME type |
| metadata | JSONB | Additional metadata |
| memory_type | VARCHAR(50) | episodic/semantic/working |
| tier | VARCHAR(20) | persistent/ephemeral |
| tags | TEXT[] | Classification tags |
| embedding | vector(1536) | Vector embedding |
| parent_id | UUID | Parent memory reference |
| importance_score | FLOAT | Importance (0-1) |
| decay_rate | FLOAT | Decay multiplier |

### agent_states

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| agent_name | VARCHAR(255) | Agent identifier |
| state | VARCHAR(50) | Runtime state |
| health_status | VARCHAR(50) | healthy/warning/critical |
| health_score | FLOAT | 0.0-1.0 health metric |
| phi_integration | FLOAT | IIT consciousness metric |
| integrated_information | FLOAT | IIT phi value |
| free_energy | FLOAT | FEP energy value |
| messages_processed | INTEGER | Total messages |
| avg_response_time_ms | FLOAT | Average latency |

### workflow_states

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| workflow_name | VARCHAR(255) | Workflow identifier |
| state | VARCHAR(50) | pending/running/completed/failed |
| progress_percent | FLOAT | 0-100 progress |
| input_data | JSONB | Workflow inputs |
| output_data | JSONB | Workflow outputs |
| parent_workflow_id | UUID | Parent workflow |
| trace_id | UUID | Distributed trace ID |
| last_checkpoint | JSONB | Last checkpoint data |

### consensus_proposals

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| proposal_type | VARCHAR(100) | Proposal category |
| state | VARCHAR(50) | open/passed/rejected |
| votes_for | INTEGER | For vote count |
| votes_against | INTEGER | Against vote count |
| votes_abstain | INTEGER | Abstain vote count |
| required_quorum | FLOAT | Minimum participation |
| required_majority | FLOAT | Required majority |

## Troubleshooting

### pgvector Extension

If pgvector is not available:

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Connection Issues

```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check PostgreSQL is running
pg_isready -h localhost -p 5432
```

### Migration Errors

If a migration fails:

1. Check the error message for details
2. Verify database connection and permissions
3. Ensure pgvector extension is installed
4. Check if table already exists (may need rollback)

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-04-07 | Initial migrations (001-004) |
