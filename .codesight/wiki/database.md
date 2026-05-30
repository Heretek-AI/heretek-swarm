# Database

> **Navigation aid.** Schema shapes and field types extracted via AST. Read the actual schema source files before writing migrations or query logic.

**unknown** — 25 models

### swarm_memories

fk: session_id

- `session_id`: uuid _(fk)_
- `content_type`: varchar _(default)_
- `metadata`: jsonb _(default)_
- `tier`: varchar _(required)_

### agent_states

- `agent_type`: varchar _(required)_
- `tier`: varchar _(required)_
- `health_status`: varchar _(required)_
- `health_score`: float _(default)_
- `integrated_information`: float _(default)_
- `free_energy`: float _(default)_
- `attention_focus`: float _(default)_
- `global_workspace_activity`: float _(default)_
- `messages_per_second`: float _(default)_
- `avg_response_time_ms`: float _(default)_
- `error_count`: integer _(default)_
- `last_error_at`: timestamp with time zone
- `cpu_usage_percent`: float _(default)_
- `last_heartbeat`: timestamp with time zone
- `last_active`: timestamp with time zone

### workflow_states

fk: root_workflow_id, trace_id, span_id

- `workflow_version`: varchar _(required)_
- `workflow_type`: varchar _(required)_
- `status`: varchar _(required)_
- `progress_percent`: float _(default)_
- `output_data`: jsonb _(default)_
- `context`: jsonb _(default)_
- `root_workflow_id`: uuid _(fk)_
- `trace_id`: uuid _(fk)_
- `span_id`: uuid _(fk)_
- `current_agent`: varchar
- `last_checkpoint_at`: timestamp with time zone
- `completed_at`: timestamp with time zone
- `duration_ms`: integer
- `error_stack`: text
- `retry_count`: integer _(default)_
- `max_retries`: integer _(default)_

### consensus_proposals

- `proposal_title`: varchar _(required)_
- `proposal_description`: text
- `context`: jsonb _(default)_
- `result`: varchar
- `voting_end`: timestamp with time zone
- `voting_timeout_seconds`: integer _(default)_
- `required_quorum`: float _(default)_
- `required_majority`: float _(default)_
- `votes_against`: integer _(default)_
- `votes_abstain`: integer _(default)_
- `total_votes`: integer _(default)_
- `proposer_agent`: varchar _(required)_
- `resolved_at`: timestamp with time zone

### consensus_votes

- `vote`: varchar _(required)_
- `vote_weight`: float _(default)_
- `vote_data`: jsonb _(default)_

### collective_patterns

fk: parent_pattern_id

- `pattern_type`: varchar _(required)_
- `pattern_category`: varchar
- `description`: text
- `metadata`: jsonb _(default)_
- `validation_count`: integer _(default)_
- `validation_threshold`: float _(default)_
- `parent_pattern_id`: uuid _(fk)_
- `embedding_model`: varchar _(default)_
- `last_used_at`: timestamp with time zone
- `expires_at`: timestamp with time zone

### knowledge_transformations

fk: target_knowledge_id

- `source_knowledge_type`: varchar
- `target_knowledge_id`: uuid _(fk)_
- `target_knowledge_type`: varchar
- `transformation_description`: text
- `fidelity_score`: float _(default)_
- `downstream_transformations`: integer _(default)_
- `validated_at`: timestamp with time zone

### pattern_subscriptions

- `subscription_type`: varchar _(default)_
- `notification_frequency`: varchar _(default)_
- `matches_applied`: integer _(default)_
- `last_match_at`: timestamp with time zone
- `expires_at`: timestamp with time zone

### deliberation_arguments

fk: proposal_id

- `proposal_id`: uuid _(required, fk)_
- `argument_data`: jsonb _(default)_
- `agent_role`: varchar
- `relevance_score`: float _(default)_
- `upvotes`: integer _(default)_
- `downvotes`: integer _(default)_

### agent_expertise_profiles

- `agent_name`: varchar _(required)_
- `subdomain`: varchar
- `peer_endorsed`: boolean _(default)_
- `system_calculated`: boolean _(default)_
- `decay_rate`: float _(default)_
- `expires_at`: timestamp with time zone

### consensus_audit_trail

fk: deliberation_round_id, vote_id, argument_id

- `event_type`: varchar _(required)_
- `deliberation_round_id`: uuid _(fk)_
- `vote_id`: uuid _(fk)_
- `argument_id`: uuid _(fk)_
- `actor_role`: varchar
- `event_description`: text
- `state_after`: jsonb
- `recorded_at`: timestamp with time zone _(default)_

### memory_access_logs

fk: session_id, workflow_id

- `memory_type`: varchar _(required)_
- `session_id`: uuid _(fk)_
- `workflow_id`: uuid _(fk)_
- `access_duration_ms`: float
- `query_vector`: vector

### memory_tier_state

- `memory_type`: varchar _(required)_
- `tier_changes`: integer _(default)_
- `last_tier_change_at`: timestamp with time zone
- `compression_algorithm`: varchar
- `compressed_size_bytes`: integer

### compression_metadata

- `memory_type`: varchar _(required)_
- `compression_algorithm`: varchar
- `compressed_size_bytes`: integer
- `compression_ratio`: float _(default)_
- `decompression_time_ms`: float
- `expires_at`: timestamp with time zone

### prefetch_cache

- `cache_type`: varchar _(required)_
- `miss_count`: integer _(default)_
- `last_hit_at`: timestamp with time zone
- `expires_at`: timestamp with time zone

### agent_learning_state

- `agent_name`: varchar _(required)_
- `agent_type`: varchar
- `learning_state`: varchar _(default)_
- `can_teach`: boolean _(default)_
- `can_share_knowledge`: boolean _(default)_
- `patterns_learned`: integer _(default)_
- `retention_score`: float _(default)_
- `adaptation_score`: float _(default)_
- `expertise_levels`: jsonb _(default)_
- `collaborative`: learning_goals jsonb _(default)_
- `last_learning_session_at`: timestamp with time zone
- `successful_learnings`: integer _(default)_
- `failed_learnings`: integer _(default)_
- `last_active_at`: timestamp with time zone _(default)_

### agent_memory_config

- `max_memory_size_bytes`: bigint _(default)_
- `warm_tier_threshold`: float _(default)_
- `cold_tier_threshold`: float _(default)_
- `base_decay_rate`: float _(default)_
- `decay_interval_seconds`: integer _(default)_
- `compression_algorithm`: varchar _(default)_
- `compression_threshold_bytes`: integer _(default)_
- `prefetch_lookahead`: integer _(default)_
- `prefetch_confidence_threshold`: float _(default)_
- `vector_index_type`: varchar _(default)_
- `vector_search_k`: integer _(default)_
- `auto_cleanup_enabled`: boolean _(default)_
- `cleanup_interval_seconds`: integer _(default)_
- `semantic_enabled`: boolean _(default)_
- `working_enabled`: boolean _(default)_
- `require_encryption`: boolean _(default)_

### agent_consensus_config

- `can_propose`: boolean _(default)_
- `can_vote`: boolean _(default)_
- `can_deliberate`: boolean _(default)_
- `use_expertise_weighting`: boolean _(default)_
- `max_vote_weight`: float _(default)_
- `min_vote_weight`: float _(default)_
- `min_rounds_to_participate`: integer _(default)_
- `max_arguments_per_round`: integer _(default)_
- `proposal_threshold`: float _(default)_
- `aggressive`: deliberation_style varchar _(default)_
- `quorum_participation_weight`: float _(default)_
- `notify_on_vote`: boolean _(default)_
- `notify_on_consensus`: boolean _(default)_
- `votes_cast`: integer _(default)_
- `arguments_submitted`: integer _(default)_
- `consensus_participations`: integer _(default)_
- `voting_accuracy`: float _(default)_
- `last_participation_at`: timestamp with time zone

### llm_providers

- `provider_type`: varchar _(required)_
- `api_key_encrypted`: text
- `api_key_hint`: varchar
- `available_models`: jsonb _(default)_
- `model_aliases`: jsonb _(default)_
- `supports_function_calling`: boolean _(default)_
- `supports_vision`: boolean _(default)_
- `max_tokens`: integer
- `max_context_length`: integer
- `rate_limit_tokens_per_minute`: integer
- `is_default`: boolean _(default)_
- `health_status`: varchar _(default)_
- `last_health_check`: timestamp with time zone
- `health_check_error`: text

### embedding_providers

- `provider_type`: varchar _(required)_
- `api_key_encrypted`: text
- `api_key_hint`: varchar
- `available_models`: jsonb _(default)_
- `supported_input_formats`: jsonb _(default)_
- `max_batch_size`: integer _(default)_
- `max_tokens_per_batch`: integer _(default)_
- `is_default`: boolean _(default)_
- `health_status`: varchar _(default)_
- `last_health_check`: timestamp with time zone
- `health_check_error`: text

### agent_configs

fk: agent_id, embedding_provider_id

- `agent_id`: varchar _(fk)_
- `config_data`: jsonb _(required)_
- `embedding_provider_id`: uuid _(fk)_
- `is_default_for_type`: boolean _(default)_
- `created_by`: varchar
- `updated_by`: varchar(255

### config_audit_log

fk: entity_id

- `entity_id`: uuid _(required, fk)_
- `action`: varchar _(required)_
- `new_value`: jsonb
- `change_reason`: text
- `ip_address`: inet

### config_cache

- `access_count`: integer _(default)_
- `last_accessed_at`: timestamp with time zone _(default)_

### external_call_logs

- `agent_type`: varchar _(required)_
- `url`: varchar _(required)_
- `method`: varchar _(required)_
- `status_code`: integer
- `duration_ms`: integer

### infrastructure_config

pk: `id` (uuid)

- `id`: uuid _(pk)_
- `service`: varchar _(required)_
- `host`: varchar _(required)_
- `port`: integer _(required)_
- `connection_url`: text
- `is_enabled`: boolean _(required)_
- `health_status`: varchar _(default)_
- `last_health_check`: timestamp with time zone
- `health_check_latency_ms`: integer
- `health_check_error`: text
- `extra_config`: jsonb _(default)_

## Schema Source Files

Read and edit these files when adding columns, creating migrations, or changing relations:

- `/db_models.py` — imported by **10** files
- `/models.py` — imported by **5** files

---
_Back to [overview.md](./overview.md)_