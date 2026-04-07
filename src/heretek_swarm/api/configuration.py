"""
Configuration API Endpoints

HTTP endpoints for managing system configurations, LLM providers, and embedding providers.
Provides CRUD operations through a RESTful API.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import structlog

from heretek_swarm.config.service import (
    ConfigurationService,
    get_config_service,
)
from heretek_swarm.config.models import (
    UserConfiguration,
    UserConfigurationCreate,
    UserConfigurationUpdate,
    LLMProvider,
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderTestRequest,
    LLMProviderTestResponse,
    EmbeddingProvider,
    EmbeddingProviderCreate,
    EmbeddingProviderUpdate,
    EmbeddingProviderTestRequest,
    EmbeddingProviderTestResponse,
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    ConfigAuditLog,
    ConfigurationExport,
    ConfigurationImport,
    ImportOptions,
    ImportResult,
    HealthStatus,
)
from heretek_swarm.gateway.auth import verify_auth
from heretek_swarm.llm.providers.factory import (
    create_llm_provider,
    list_available_providers as list_llm_provider_types,
    get_provider_info as get_llm_provider_info,
)
from heretek_swarm.embeddings.providers.factory import (
    create_embedding_provider,
    list_available_providers as list_embedding_provider_types,
    get_provider_info as get_embedding_provider_info,
)

logger = structlog.get_logger("api.configuration")

router = APIRouter(prefix="/api/config", tags=["Configuration"])


# =============================================================================
# Helper Functions
# =============================================================================

def get_service() -> ConfigurationService:
    """Dependency injection for ConfigurationService."""
    return get_config_service()


# =============================================================================
# User Configuration Endpoints
# =============================================================================

@router.get("")
async def get_all_configs(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Get all configurations with optional filtering."""
    configs = await service.list_configs(category=category, limit=limit, offset=offset)
    return {
        "configurations": [c.model_dump() for c in configs],
        "total": len(configs),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{key}")
async def get_config(
    key: str,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Get a specific configuration by key."""
    config = await service.get_config(key)
    if not config:
        raise HTTPException(404, f"Configuration '{key}' not found")
    return config.model_dump()


@router.put("/{key}")
async def update_config(
    key: str,
    update: UserConfigurationUpdate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Update a configuration."""
    config = await service.update_config(key, update, changed_by=authenticated)
    if not config:
        raise HTTPException(404, f"Configuration '{key}' not found")
    return config.model_dump()


@router.post("")
async def create_config(
    config: UserConfigurationCreate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Create a new configuration."""
    try:
        new_config = await service.create_config(config, changed_by=authenticated)
        return new_config.model_dump()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{key}")
async def delete_config(
    key: str,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Delete a configuration."""
    success = await service.delete_config(key, changed_by=authenticated)
    if not success:
        raise HTTPException(404, f"Configuration '{key}' not found")
    return {"status": "deleted", "key": key}


# =============================================================================
# LLM Provider Endpoints
# =============================================================================

@router.get("/llm/types")
async def list_llm_provider_types() -> Dict[str, Any]:
    """List available LLM provider types."""
    types = list_llm_provider_types()
    info = [get_llm_provider_info(t) for t in types]
    return {"provider_types": info}


@router.get("/llm/providers")
async def list_llm_providers(
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    enabled_only: bool = Query(False, description="Only return enabled providers"),
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """List configured LLM providers."""
    providers = await service.list_llm_providers(
        provider_type=provider_type,
        enabled_only=enabled_only,
    )
    return {
        "providers": [p.model_dump() for p in providers],
        "total": len(providers),
    }


@router.get("/llm/providers/{provider_id}")
async def get_llm_provider(
    provider_id: UUID,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Get a specific LLM provider."""
    provider = await service.get_llm_provider(provider_id)
    if not provider:
        raise HTTPException(404, f"LLM provider '{provider_id}' not found")
    return provider.model_dump()


@router.post("/llm/providers")
async def create_llm_provider(
    provider: LLMProviderCreate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Create a new LLM provider."""
    try:
        # Note: API key should be encrypted before storage in production
        new_provider = await service.create_llm_provider(provider, changed_by=authenticated)
        return new_provider.model_dump()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/llm/providers/{provider_id}")
async def update_llm_provider(
    provider_id: UUID,
    update: LLMProviderUpdate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Update an LLM provider."""
    provider = await service.update_llm_provider(provider_id, update, changed_by=authenticated)
    if not provider:
        raise HTTPException(404, f"LLM provider '{provider_id}' not found")
    return provider.model_dump()


@router.delete("/llm/providers/{provider_id}")
async def delete_llm_provider(
    provider_id: UUID,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Delete an LLM provider."""
    success = await service.delete_llm_provider(provider_id, changed_by=authenticated)
    if not success:
        raise HTTPException(404, f"LLM provider '{provider_id}' not found")
    return {"status": "deleted", "id": str(provider_id)}


@router.post("/llm/providers/{provider_id}/test")
async def test_llm_provider(
    provider_id: UUID,
    test_request: LLMProviderTestRequest,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Test LLM provider connectivity."""
    provider = await service.get_llm_provider(provider_id)
    if not provider:
        raise HTTPException(404, f"LLM provider '{provider_id}' not found")
    
    try:
        # Create provider instance
        llm_provider = create_llm_provider(
            provider.provider_type,
            {
                "base_url": provider.base_url,
                "api_key": "test-key",  # In production, decrypt the actual key
                "default_model": test_request.model or provider.default_model,
                "extra_config": provider.extra_config,
            }
        )
        
        # Test connectivity
        result = await llm_provider.test_connectivity(model=test_request.model)
        
        return {
            "provider_id": str(provider_id),
            "provider_name": provider.provider_name,
            "success": result.success,
            "model_used": result.model_used,
            "latency_ms": result.latency_ms,
            "response_text": result.response_text if result.success else None,
            "error": result.error if not result.success else None,
        }
        
    except Exception as e:
        return {
            "provider_id": str(provider_id),
            "provider_name": provider.provider_name,
            "success": False,
            "error": str(e),
        }


# =============================================================================
# Embedding Provider Endpoints
# =============================================================================

@router.get("/embedding/types")
async def list_embedding_provider_types() -> Dict[str, Any]:
    """List available embedding provider types."""
    types = list_embedding_provider_types()
    info = [get_embedding_provider_info(t) for t in types]
    return {"provider_types": info}


@router.get("/embedding/providers")
async def list_embedding_providers(
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    enabled_only: bool = Query(False, description="Only return enabled providers"),
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """List configured embedding providers."""
    providers = await service.list_embedding_providers(
        provider_type=provider_type,
        enabled_only=enabled_only,
    )
    return {
        "providers": [p.model_dump() for p in providers],
        "total": len(providers),
    }


@router.get("/embedding/providers/{provider_id}")
async def get_embedding_provider(
    provider_id: UUID,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Get a specific embedding provider."""
    provider = await service.get_embedding_provider(provider_id)
    if not provider:
        raise HTTPException(404, f"Embedding provider '{provider_id}' not found")
    return provider.model_dump()


@router.post("/embedding/providers")
async def create_embedding_provider(
    provider: EmbeddingProviderCreate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Create a new embedding provider."""
    try:
        new_provider = await service.create_embedding_provider(provider, changed_by=authenticated)
        return new_provider.model_dump()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/embedding/providers/{provider_id}")
async def update_embedding_provider(
    provider_id: UUID,
    update: EmbeddingProviderUpdate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Update an embedding provider."""
    provider = await service.update_embedding_provider(provider_id, update, changed_by=authenticated)
    if not provider:
        raise HTTPException(404, f"Embedding provider '{provider_id}' not found")
    return provider.model_dump()


@router.delete("/embedding/providers/{provider_id}")
async def delete_embedding_provider(
    provider_id: UUID,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Delete an embedding provider."""
    success = await service.delete_embedding_provider(provider_id, changed_by=authenticated)
    if not success:
        raise HTTPException(404, f"Embedding provider '{provider_id}' not found")
    return {"status": "deleted", "id": str(provider_id)}


@router.post("/embedding/providers/{provider_id}/test")
async def test_embedding_provider(
    provider_id: UUID,
    test_request: EmbeddingProviderTestRequest,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Test embedding provider connectivity."""
    provider = await service.get_embedding_provider(provider_id)
    if not provider:
        raise HTTPException(404, f"Embedding provider '{provider_id}' not found")
    
    try:
        # Create provider instance
        embedding_provider = create_embedding_provider(
            provider.provider_type,
            {
                "base_url": provider.base_url,
                "api_key": "test-key",  # In production, decrypt the actual key
                "default_model": test_request.model or provider.default_model,
                "extra_config": provider.extra_config,
            }
        )
        
        # Test connectivity by generating an embedding
        import time
        start_time = time.time()
        response = await embedding_provider.embed(
            texts=[test_request.text],
            model=test_request.model,
        )
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "provider_id": str(provider_id),
            "provider_name": provider.provider_name,
            "success": True,
            "model_used": response.model,
            "dimensions": response.dimensions,
            "latency_ms": latency_ms,
        }
        
    except Exception as e:
        return {
            "provider_id": str(provider_id),
            "provider_name": provider.provider_name,
            "success": False,
            "error": str(e),
        }


# =============================================================================
# Agent Configuration Endpoints
# =============================================================================

@router.get("/agent/configs")
async def list_agent_configs(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    active_only: bool = Query(True, description="Only return active configs"),
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """List agent configurations."""
    configs = await service.list_agent_configs(agent_type=agent_type, active_only=active_only)
    return {
        "configs": [c.model_dump() for c in configs],
        "total": len(configs),
    }


@router.get("/agent/configs/{config_id}")
async def get_agent_config(
    config_id: UUID,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Get a specific agent configuration."""
    config = await service.get_agent_config(config_id)
    if not config:
        raise HTTPException(404, f"Agent config '{config_id}' not found")
    return config.model_dump()


@router.post("/agent/configs")
async def create_agent_config(
    config: AgentConfigCreate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Create a new agent configuration."""
    try:
        new_config = await service.create_agent_config(config, changed_by=authenticated)
        return new_config.model_dump()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/agent/configs/{config_id}")
async def update_agent_config(
    config_id: UUID,
    update: AgentConfigUpdate,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Update an agent configuration."""
    config = await service.update_agent_config(config_id, update, changed_by=authenticated)
    if not config:
        raise HTTPException(404, f"Agent config '{config_id}' not found")
    return config.model_dump()


@router.delete("/agent/configs/{config_id}")
async def delete_agent_config(
    config_id: UUID,
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Delete an agent configuration."""
    success = await service.delete_agent_config(config_id, changed_by=authenticated)
    if not success:
        raise HTTPException(404, f"Agent config '{config_id}' not found")
    return {"status": "deleted", "id": str(config_id)}


# =============================================================================
# Audit Log Endpoints
# =============================================================================

@router.get("/audit-log")
async def get_audit_log(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(100, ge=1, le=1000),
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Get configuration audit log."""
    logs = await service.get_audit_log(entity_type=entity_type, limit=limit)
    return {
        "logs": [log.model_dump() for log in logs],
        "total": len(logs),
    }


# =============================================================================
# Import/Export Endpoints
# =============================================================================

@router.get("/export")
async def export_configurations(
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Export all configurations."""
    export_data = await service.export_configurations(exported_by=authenticated)
    return export_data.model_dump()


@router.post("/import")
async def import_configurations(
    import_data: ConfigurationImport,
    options: ImportOptions = ImportOptions(),
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Import configurations from a bundle."""
    result = await service.import_configurations(import_data, options, changed_by=authenticated)
    return result.model_dump()


# =============================================================================
# Migration Endpoint
# =============================================================================

@router.post("/migrate-from-env")
async def migrate_from_env(
    authenticated: str = Depends(verify_auth),
    service: ConfigurationService = Depends(get_service),
) -> Dict[str, Any]:
    """Migrate configurations from environment variables to database."""
    result = await service.migrate_from_env(changed_by=authenticated)
    return result
