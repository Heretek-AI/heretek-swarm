# Schema

### swarm_memories
- session_id: uuid (fk)
- content_type: varchar (default)
- metadata: jsonb (default)
- tier: varchar (required)

### agent_states
- agent_type: varchar (required)
- tier: varchar (required)
- health_status: varchar (required)
- health_score: float (default)
- integrated_information: float (default)
- free_energy: float (default)
- attention_focus: float (default)
- global_workspace_activity: float (default)
- messages_per_second: float (default)
- avg_response_time_ms: float (default)
- error_count: integer (default)
- last_error_at: timestamp with time zone
- cpu_usage_percent: float (default)
- last_heartbeat: timestamp with time zone
- last_active: timestamp with time zone

### workflow_states
- workflow_version: varchar (required)
- workflow_type: varchar (required)
- status: varchar (required)
- progress_percent: float (default)
- output_data: jsonb (default)
- context: jsonb (default)
- root_workflow_id: uuid (fk)
- trace_id: uuid (fk)
- span_id: uuid (fk)
- current_agent: varchar
- last_checkpoint_at: timestamp with time zone
- completed_at: timestamp with time zone
- duration_ms: integer
- error_stack: text
- retry_count: integer (default)
- max_retries: integer (default)

### consensus_proposals
- proposal_title: varchar (required)
- proposal_description: text
- context: jsonb (default)
- result: varchar
- voting_end: timestamp with time zone
- voting_timeout_seconds: integer (default)
- required_quorum: float (default)
- required_majority: float (default)
- votes_against: integer (default)
- votes_abstain: integer (default)
- total_votes: integer (default)
- proposer_agent: varchar (required)
- resolved_at: timestamp with time zone

### consensus_votes
- vote: varchar (required)
- vote_weight: float (default)
- vote_data: jsonb (default)

### collective_patterns
- pattern_type: varchar (required)
- pattern_category: varchar
- description: text
- metadata: jsonb (default)
- validation_count: integer (default)
- validation_threshold: float (default)
- parent_pattern_id: uuid (fk)
- embedding_model: varchar (default)
- last_used_at: timestamp with time zone
- expires_at: timestamp with time zone

### knowledge_transformations
- source_knowledge_type: varchar
- target_knowledge_id: uuid (fk)
- target_knowledge_type: varchar
- transformation_description: text
- fidelity_score: float (default)
- downstream_transformations: integer (default)
- validated_at: timestamp with time zone

### pattern_subscriptions
- subscription_type: varchar (default)
- notification_frequency: varchar (default)
- matches_applied: integer (default)
- last_match_at: timestamp with time zone
- expires_at: timestamp with time zone

### deliberation_arguments
- proposal_id: uuid (required, fk)
- argument_data: jsonb (default)
- agent_role: varchar
- relevance_score: float (default)
- upvotes: integer (default)
- downvotes: integer (default)

### agent_expertise_profiles
- agent_name: varchar (required)
- subdomain: varchar
- peer_endorsed: boolean (default)
- system_calculated: boolean (default)
- decay_rate: float (default)
- expires_at: timestamp with time zone

### consensus_audit_trail
- event_type: varchar (required)
- deliberation_round_id: uuid (fk)
- vote_id: uuid (fk)
- argument_id: uuid (fk)
- actor_role: varchar
- event_description: text
- state_after: jsonb
- recorded_at: timestamp with time zone (default)

### memory_access_logs
- memory_type: varchar (required)
- session_id: uuid (fk)
- workflow_id: uuid (fk)
- access_duration_ms: float
- query_vector: vector

### memory_tier_state
- memory_type: varchar (required)
- tier_changes: integer (default)
- last_tier_change_at: timestamp with time zone
- compression_algorithm: varchar
- compressed_size_bytes: integer

### compression_metadata
- memory_type: varchar (required)
- compression_algorithm: varchar
- compressed_size_bytes: integer
- compression_ratio: float (default)
- decompression_time_ms: float
- expires_at: timestamp with time zone

### prefetch_cache
- cache_type: varchar (required)
- miss_count: integer (default)
- last_hit_at: timestamp with time zone
- expires_at: timestamp with time zone

### agent_learning_state
- agent_name: varchar (required)
- agent_type: varchar
- learning_state: varchar (default)
- can_teach: boolean (default)
- can_share_knowledge: boolean (default)
- patterns_learned: integer (default)
- retention_score: float (default)
- adaptation_score: float (default)
- expertise_levels: jsonb (default)
- collaborative: learning_goals jsonb (default)
- last_learning_session_at: timestamp with time zone
- successful_learnings: integer (default)
- failed_learnings: integer (default)
- last_active_at: timestamp with time zone (default)

### agent_memory_config
- max_memory_size_bytes: bigint (default)
- warm_tier_threshold: float (default)
- cold_tier_threshold: float (default)
- base_decay_rate: float (default)
- decay_interval_seconds: integer (default)
- compression_algorithm: varchar (default)
- compression_threshold_bytes: integer (default)
- prefetch_lookahead: integer (default)
- prefetch_confidence_threshold: float (default)
- vector_index_type: varchar (default)
- vector_search_k: integer (default)
- auto_cleanup_enabled: boolean (default)
- cleanup_interval_seconds: integer (default)
- semantic_enabled: boolean (default)
- working_enabled: boolean (default)
- require_encryption: boolean (default)

### agent_consensus_config
- can_propose: boolean (default)
- can_vote: boolean (default)
- can_deliberate: boolean (default)
- use_expertise_weighting: boolean (default)
- max_vote_weight: float (default)
- min_vote_weight: float (default)
- min_rounds_to_participate: integer (default)
- max_arguments_per_round: integer (default)
- proposal_threshold: float (default)
- aggressive: deliberation_style varchar (default)
- quorum_participation_weight: float (default)
- notify_on_vote: boolean (default)
- notify_on_consensus: boolean (default)
- votes_cast: integer (default)
- arguments_submitted: integer (default)
- consensus_participations: integer (default)
- voting_accuracy: float (default)
- last_participation_at: timestamp with time zone

### llm_providers
- provider_type: varchar (required)
- api_key_encrypted: text
- api_key_hint: varchar
- available_models: jsonb (default)
- model_aliases: jsonb (default)
- supports_function_calling: boolean (default)
- supports_vision: boolean (default)
- max_tokens: integer
- max_context_length: integer
- rate_limit_tokens_per_minute: integer
- is_default: boolean (default)
- health_status: varchar (default)
- last_health_check: timestamp with time zone
- health_check_error: text

### embedding_providers
- provider_type: varchar (required)
- api_key_encrypted: text
- api_key_hint: varchar
- available_models: jsonb (default)
- supported_input_formats: jsonb (default)
- max_batch_size: integer (default)
- max_tokens_per_batch: integer (default)
- is_default: boolean (default)
- health_status: varchar (default)
- last_health_check: timestamp with time zone
- health_check_error: text

### agent_configs
- agent_id: varchar (fk)
- config_data: jsonb (required)
- embedding_provider_id: uuid (fk)
- is_default_for_type: boolean (default)
- created_by: varchar
- updated_by: varchar(255

### config_audit_log
- entity_id: uuid (required, fk)
- action: varchar (required)
- new_value: jsonb
- change_reason: text
- ip_address: inet

### config_cache
- access_count: integer (default)
- last_accessed_at: timestamp with time zone (default)

### external_call_logs
- agent_type: varchar (required)
- url: varchar (required)
- method: varchar (required)
- status_code: integer
- duration_ms: integer

### infrastructure_config
- id: uuid (pk)
- service: varchar (required)
- host: varchar (required)
- port: integer (required)
- connection_url: text
- is_enabled: boolean (required)
- health_status: varchar (default)
- last_health_check: timestamp with time zone
- health_check_latency_ms: integer
- health_check_error: text
- extra_config: jsonb (default)
