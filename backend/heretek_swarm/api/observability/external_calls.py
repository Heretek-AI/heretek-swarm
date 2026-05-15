"""External call log endpoints for the observability API."""

import json
import uuid as uuid_module
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import func, select

from heretek_swarm.models.external_call_log import ExternalCallLog
from heretek_swarm.models.external_call_log_encryption import get_encryptor
from heretek_swarm.schemas.external_call_log import (
    ExternalCallLogCreate,
    ExternalCallLogListItem,
    ExternalCallLogListResponse,
    ExternalCallLogResponse,
)

from . import (
    _get_external_call_log_session_factory,
    check_rate_limit,
    connection_manager,
    get_zero_trust,
    validate_input,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="", tags=["observability"])


@router.get("/external-calls", response_model=ExternalCallLogListResponse)
async def get_external_calls(
    request: Request,
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    call_type: str | None = Query(None, description="Filter by call type (http/mcp)"),
    status: str = Query("all", description="Filter by status: success, error, or all"),
    start_time: datetime | None = Query(  # noqa: B008
        None, description="Filter by start time (ISO format)"
    ),
    end_time: datetime | None = Query(  # noqa: B008
        None, description="Filter by end time (ISO format)"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
) -> ExternalCallLogListResponse:
    """Get external call logs with optional filtering and pagination."""
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        session_factory = _get_external_call_log_session_factory()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("external_calls_db_error", error=str(e))
        raise HTTPException(status_code=503, detail="External call log database unavailable") from e

    async with session_factory() as session:
        try:
            query = select(ExternalCallLog)
            count_query = select(func.count()).select_from(ExternalCallLog)

            if agent_id:
                query = query.where(ExternalCallLog.agent_id == agent_id)
                count_query = count_query.where(ExternalCallLog.agent_id == agent_id)

            if call_type:
                query = query.where(ExternalCallLog.call_type == call_type)
                count_query = count_query.where(ExternalCallLog.call_type == call_type)

            if status == "success":
                query = query.where(ExternalCallLog.status_code >= 200)
                query = query.where(ExternalCallLog.status_code < 300)
                count_query = count_query.where(ExternalCallLog.status_code >= 200)
                count_query = count_query.where(ExternalCallLog.status_code < 300)
            elif status == "error":
                query = query.where(
                    (ExternalCallLog.status_code < 200)
                    | (ExternalCallLog.status_code >= 300)
                    | (ExternalCallLog.error_message.isnot(None))
                )
                count_query = count_query.where(
                    (ExternalCallLog.status_code < 200)
                    | (ExternalCallLog.status_code >= 300)
                    | (ExternalCallLog.error_message.isnot(None))
                )

            if start_time:
                query = query.where(ExternalCallLog.created_at >= start_time)
                count_query = count_query.where(ExternalCallLog.created_at >= start_time)

            if end_time:
                query = query.where(ExternalCallLog.created_at <= end_time)
                count_query = count_query.where(ExternalCallLog.created_at <= end_time)

            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            query = query.order_by(ExternalCallLog.created_at.desc())
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            logs = result.scalars().all()

            items = []
            for log in logs:
                url_domain = log.url
                if "://" in url_domain:
                    url_domain = url_domain.split("://", 1)[1]
                if "/" in url_domain:
                    url_domain = url_domain.split("/", 1)[0]

                item = ExternalCallLogListItem(
                    id=log.id,
                    agent_id=log.agent_id,
                    agent_type=log.agent_type,
                    call_type=log.call_type,
                    url=log.url,
                    url_domain=url_domain,
                    url_full=log.url,
                    method=log.method,
                    status_code=log.status_code,
                    duration_ms=log.duration_ms,
                    tool_name=log.tool_name,
                    error_message=log.error_message,
                    created_at=log.created_at,
                )
                items.append(item)

            has_more = (offset + len(items)) < total

            logger.info(
                "external_calls_retrieved",
                total=total,
                returned=len(items),
                filters={"agent_id": agent_id, "call_type": call_type, "status": status},
            )

            return ExternalCallLogListResponse(
                items=items,
                total=total,
                offset=offset,
                limit=limit,
                has_more=has_more,
            )

        except Exception as e:
            logger.exception("external_calls_query_error", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to query external call logs") from e


@router.post("/external-calls", status_code=201)
async def create_external_call(
    request: Request,
    log_data: ExternalCallLogCreate,
) -> dict[str, Any]:
    """Create a new external call log entry."""
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    validator = get_zero_trust()
    validate_input(validator, {"agent_id": log_data.agent_id}, "external_call")
    validate_input(validator, {"call_type": log_data.call_type}, "external_call")

    try:
        session_factory = _get_external_call_log_session_factory()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("external_calls_db_error", error=str(e))
        raise HTTPException(status_code=503, detail="External call log database unavailable") from e

    encryptor = get_encryptor()

    encrypted_headers = None
    if log_data.request_headers is not None:
        sanitized_headers = encryptor.sanitize(log_data.request_headers)
        encrypted_headers = encryptor.encrypt(sanitized_headers).get("encrypted", "")

    encrypted_request_body = None
    if log_data.request_body is not None:
        encrypted_request_body = encryptor.encrypt({"body": log_data.request_body}).get(
            "encrypted", ""
        )

    encrypted_response_body = None
    if log_data.response_body is not None:
        encrypted_response_body = encryptor.encrypt({"body": log_data.response_body}).get(
            "encrypted", ""
        )

    async with session_factory() as session:
        try:
            log = ExternalCallLog(
                agent_id=log_data.agent_id,
                agent_type=log_data.agent_type,
                call_type=log_data.call_type,
                url=log_data.url,
                method=log_data.method,
                status_code=log_data.status_code,
                duration_ms=log_data.duration_ms,
                request_headers_encrypted=encrypted_headers,
                request_body_encrypted=encrypted_request_body,
                response_body_encrypted=encrypted_response_body,
                tool_name=log_data.tool_name,
                error_message=log_data.error_message,
            )

            session.add(log)
            await session.commit()
            await session.refresh(log)

            logger.info(
                "external_call_created",
                log_id=str(log.id),
                agent_id=log_data.agent_id,
                call_type=log_data.call_type,
            )

            await connection_manager.broadcast_observability(
                {
                    "type": "external_call_created",
                    "data": {
                        "id": str(log.id),
                        "agent_id": log.agent_id,
                        "agent_type": log.agent_type,
                        "call_type": log.call_type,
                        "url": log.url,
                        "method": log.method,
                        "status_code": log.status_code,
                        "duration_ms": log.duration_ms,
                        "tool_name": log.tool_name,
                        "error_message": log.error_message,
                        "created_at": log.created_at.isoformat() if log.created_at else None,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            return {
                "id": str(log.id),
                "agent_id": log.agent_id,
                "agent_type": log.agent_type,
                "call_type": log.call_type,
                "url": log.url,
                "method": log.method,
                "status_code": log.status_code,
                "duration_ms": log.duration_ms,
                "tool_name": log.tool_name,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "message": "External call log created successfully",
            }

        except Exception as e:
            logger.exception("external_call_create_error", error=str(e))
            await session.rollback()
            raise HTTPException(status_code=500, detail="Failed to create external call log") from e


@router.get("/external-calls/{call_id}", response_model=ExternalCallLogResponse)
async def get_external_call(
    call_id: str,
    request: Request,
    include_bodies: bool = Query(
        True,
        description="Include decrypted request/response bodies (sensitive data may be redacted)",
    ),
) -> ExternalCallLogResponse:
    """Get a single external call log entry by ID."""
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        call_uuid = uuid_module.UUID(call_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid call ID format")  # noqa: B904

    try:
        session_factory = _get_external_call_log_session_factory()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("external_calls_db_error", error=str(e))
        raise HTTPException(status_code=503, detail="External call log database unavailable") from e

    async with session_factory() as session:
        try:
            result = await session.execute(
                select(ExternalCallLog).where(ExternalCallLog.id == call_uuid)
            )
            log = result.scalar_one_or_none()

            if log is None:
                raise HTTPException(status_code=404, detail="External call log not found")

            response_data = {
                "id": log.id,
                "agent_id": log.agent_id,
                "agent_type": log.agent_type,
                "call_type": log.call_type,
                "url": log.url,
                "url_domain": log.url.split("://", 1)[1].split("/")[0]
                if "://" in log.url
                else log.url.split("/")[0],
                "url_full": log.url,
                "method": log.method,
                "status_code": log.status_code,
                "duration_ms": log.duration_ms,
                "tool_name": log.tool_name,
                "error_message": log.error_message,
                "created_at": log.created_at,
            }

            if include_bodies:
                encryptor = get_encryptor()

                decrypted_headers = None
                if log.request_headers_encrypted:
                    try:
                        decrypted_data = encryptor.decrypt(log.request_headers_encrypted)
                        if isinstance(decrypted_data, dict):
                            decrypted_headers = encryptor.sanitize(decrypted_data)
                        elif isinstance(decrypted_data, str):
                            decrypted_headers = encryptor.sanitize(json.loads(decrypted_data))
                    except Exception as e:
                        logger.warning(
                            "failed_to_decrypt_headers",
                            call_id=str(call_id),
                            error=str(e),
                        )
                        decrypted_headers = {"_error": "Failed to decrypt"}

                decrypted_request_body = None
                if log.request_body_encrypted:
                    try:
                        decrypted_data = encryptor.decrypt(log.request_body_encrypted)
                        if isinstance(decrypted_data, dict) and "body" in decrypted_data:
                            decrypted_request_body = decrypted_data["body"]
                        elif isinstance(decrypted_data, str):
                            decrypted_request_body = decrypted_data
                    except Exception as e:
                        logger.warning(
                            "failed_to_decrypt_request_body",
                            call_id=str(call_id),
                            error=str(e),
                        )
                        decrypted_request_body = "[decryption failed]"

                decrypted_response_body = None
                if log.response_body_encrypted:
                    try:
                        decrypted_data = encryptor.decrypt(log.response_body_encrypted)
                        if isinstance(decrypted_data, dict) and "body" in decrypted_data:
                            decrypted_response_body = decrypted_data["body"]
                        elif isinstance(decrypted_data, str):
                            decrypted_response_body = decrypted_data
                    except Exception as e:
                        logger.warning(
                            "failed_to_decrypt_response_body",
                            call_id=str(call_id),
                            error=str(e),
                        )
                        decrypted_response_body = "[decryption failed]"

                response_data["request_headers"] = decrypted_headers
                response_data["request_body"] = decrypted_request_body
                response_data["response_body"] = decrypted_response_body
            else:
                response_data["request_headers"] = None
                response_data["request_body"] = None
                response_data["response_body"] = None

            logger.info(
                "external_call_retrieved",
                call_id=str(call_id),
                include_bodies=include_bodies,
            )

            return ExternalCallLogResponse(**response_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("external_call_get_error", error=str(e))
            raise HTTPException(
                status_code=500, detail="Failed to retrieve external call log"
            ) from e
