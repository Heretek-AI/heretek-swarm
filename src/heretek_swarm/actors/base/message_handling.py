"""
Message handling module for AgentActor.

This module contains:
- Message sending methods (send, send_to_actor, send_with_reply, broadcast)
- Message processing (_process_mailbox, process_message, put_message)
- Default message handlers (_handle_*)
- LLM integration (run_with_llm)
"""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from heretek_swarm.actors.base.core import AgentActor, ActorMessage

logger = structlog.get_logger("AgentActor")


class AgentActorMessageHandling(AgentActor):
    """Mixin class for message handling functionality."""

    async def send(
        self,
        topic: str,
        content: dict[str, Any],
        message_type: str = "default",
        reply_to: str | None = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Send a message to a topic.

        Args:
            topic: Target topic
            content: Message content
            message_type: Type identifier for the message
            reply_to: Optional topic for responses
            correlation_id: Optional correlation ID
            metadata: Additional metadata

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())

        message = ActorMessage(
            sender=self.agent_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(UTC).isoformat(),
            correlation_id=correlation_id,
            reply_to=reply_to,
            metadata=metadata or {},
        )

        # Route through event mesh if available
        event_mesh = self._event_mesh or self.get_state("_event_mesh")
        if event_mesh is not None:
            try:
                # Send via event mesh
                await event_mesh.send_to_json(
                    topic,
                    {
                        "type": message_type,
                        "from": self.agent_id,
                        "content": content,
                        "correlation_id": correlation_id,
                        "reply_to": reply_to,
                        "metadata": metadata or {},
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                logger.info(
                    f"[{self.agent_id}] Message {message_id} sent via event mesh to {topic}",
                    extra={"message_type": message_type},
                )
                return message_id
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Event mesh send failed: {e}",
                    extra={"message_id": message_id, "topic": topic},
                )

        # Fallback: Direct delivery to actors subscribed to topic
        # Use global actor registry from supervisor
        actor_registry = self._get_actor_registry()
        if actor_registry is not None:
            try:
                # Find actors subscribed to this topic
                delivered = False
                for reg_actor in actor_registry.values():
                    if topic in getattr(reg_actor, "topics", []):
                        await reg_actor.put_message(message)
                        delivered = True
                if delivered:
                    logger.info(
                        f"[{self.agent_id}] Message {message_id} delivered directly to topic subscribers",
                        extra={"message_type": message_type},
                    )
                    return message_id
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Direct delivery failed: {e}",
                    extra={"message_id": message_id, "topic": topic},
                )

        # Last resort: log the message (should not happen in production)
        logger.warning(
            f"[{self.agent_id}] Message {message_id} queued (no delivery mechanism available)",
            extra={"message_type": message_type, "topic": topic},
        )

        # Store in internal queue for later delivery
        self._queue_message(message)
        return message_id

    def _queue_message(self, message: ActorMessage) -> None:
        """Queue a message for later delivery when event mesh becomes available."""
        pending_messages = self.get_state("_pending_messages", [])
        pending_messages.append(message)
        self.update_state("_pending_messages", pending_messages)
        logger.debug(
            f"[{self.agent_id}] Message queued for later delivery",
            extra={"message_type": message.message_type},
        )

    async def send_to_actor(
        self,
        target_actor_id: str,
        message_type: str,
        content: dict[str, Any],
        correlation_id: str | None = None,
    ) -> str:
        """
        Send a message directly to another actor.

        Args:
            target_actor_id: Target actor ID
            message_type: Message type identifier
            content: Message content
            correlation_id: Optional correlation ID

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())

        # Use global actor registry from supervisor
        actor_registry = self._get_actor_registry()
        if actor_registry is not None and target_actor_id in actor_registry:
            try:
                target_actor = actor_registry[target_actor_id]
                message = ActorMessage(
                    sender=self.agent_id,
                    message_type=message_type,
                    content={
                        "message_type": message_type,
                        "content": content,
                        "sender": self.agent_id,
                    },
                    timestamp=datetime.now(UTC).isoformat(),
                    correlation_id=correlation_id,
                )
                await target_actor.put_message(message)
                logger.info(
                    f"[{self.agent_id}] Direct message sent to {target_actor_id}",
                    extra={"message_type": message_type},
                )
                return message_id
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Direct actor send failed: {e}",
                    extra={"target": target_actor_id},
                )

        # Fallback to topic-based routing
        return await self.send(
            topic=f"actor:{target_actor_id}",
            content={
                "message_type": message_type,
                "content": content,
                "sender": self.agent_id,
            },
            message_type=message_type,
            correlation_id=correlation_id,
        )

    async def send_with_reply(
        self,
        recipient: str,
        message_type: str,
        content: dict[str, Any],
        timeout: int = 30,
    ) -> dict[str, Any] | None:
        """
        Send message and wait for reply with correlation tracking.

        Implements the request-reply pattern from Microsoft AutoGen for
        synchronous inter-agent communication.

        Args:
            recipient: Target actor ID or topic
            message_type: Message type identifier
            content: Message payload
            timeout: Seconds to wait for reply (default: 30)

        Returns:
            Reply content dict, or None if timeout/failure

        Raises:
            asyncio.TimeoutError: If no reply received within timeout
        """
        # Generate unique correlation ID for this request
        correlation_id = str(uuid.uuid4())
        reply_channel = f"reply_{self.agent_id}_{correlation_id}"

        logger.info(
            f"[{self.agent_id}] Sending request to {recipient} with correlation_id={correlation_id}",
            extra={"message_type": message_type, "timeout": timeout},
        )

        # Create a temporary queue for the reply
        reply_queue: asyncio.Queue = asyncio.Queue()

        # Register reply handler
        async def handle_reply(message: ActorMessage) -> None:
            """Handle incoming reply message."""
            await reply_queue.put(message)

        # Register the reply handler for this specific channel
        self.register_handler(reply_channel, handle_reply)

        try:
            # Send request with reply_to channel
            await self.send(
                topic=recipient,
                content=content,
                message_type=message_type,
                correlation_id=correlation_id,
                reply_to=reply_channel,
            )

            # Wait for reply with timeout
            try:
                reply_message = await asyncio.wait_for(
                    reply_queue.get(),
                    timeout=timeout,
                )

                logger.info(
                    f"[{self.agent_id}] Reply received for correlation_id={correlation_id}",
                    extra={"message_type": reply_message.message_type},
                )

                return reply_message.content

            except TimeoutError:
                logger.warning(
                    f"[{self.agent_id}] Request timeout after {timeout}s for correlation_id={correlation_id}",
                    extra={"recipient": recipient, "message_type": message_type},
                )
                raise

        finally:
            # Cleanup: unregister reply handler
            self.unregister_handler(reply_channel)

    async def put_message(self, message: ActorMessage) -> None:
        """
        Put a message in the actor's mailbox.

        Args:
            message: Actor message to process
        """
        # P1-10e fix: Add retry logic for message queuing instead of dropping
        max_retries = 3
        retry_delay = 0.1  # 100ms initial delay

        for attempt in range(max_retries):
            try:
                await asyncio.wait_for(
                    self.mailbox.put(message),
                    timeout=5.0,
                )
                logger.debug(
                    f"[{self.agent_id}] Message queued",
                    extra={"message_type": message.message_type},
                )
                return  # Success, exit retry loop
            except TimeoutError:
                if attempt < max_retries - 1:
                    # P1-10e fix: Retry with exponential backoff
                    logger.warning(
                        f"[{self.agent_id}] Mailbox full, retrying ({attempt + 1}/{max_retries})",
                        extra={"message_type": message.message_type},
                    )
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    # P1-10e fix: Only drop after all retries exhausted
                    logger.error(
                        f"[{self.agent_id}] Mailbox full after {max_retries} retries, message dropped",
                        extra={"message_type": message.message_type},
                    )
                    self.error_count += 1

    async def _process_mailbox(self) -> None:
        """Process messages from mailbox in a loop with continuous persistence."""
        logger.info(f"[{self.agent_id}] Starting mailbox processing")

        while self._running:
            try:
                # Get message from mailbox with timeout
                message = await asyncio.wait_for(
                    self.mailbox.get(),
                    timeout=1.0,
                )

                self.message_count += 1
                self._messages_since_persist += 1  # P0-1: Track for auto-persist
                self.last_activity = datetime.now(UTC).isoformat()

                # Process message
                await self.process_message(message)

                # P0-1: Auto-persist if interval configured and threshold reached
                if self._persistence_interval and self._messages_since_persist >= self._persistence_interval:
                    await self.save_state()
                    self._messages_since_persist = 0
                    logger.debug(
                        f"[{self.agent_id}] State persisted after {self._persistence_interval} messages",
                        extra={"total_messages": self.message_count}
                    )

                # Mark as done
                self.mailbox.task_done()

            except TimeoutError:
                # No messages, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_count += 1
                logger.error(
                    f"[{self.agent_id}] Error processing message: {e}",
                    exc_info=True,
                )

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process an incoming message.

        Default implementation routes via registered _message_handlers.
        Subclasses can override for custom routing logic.

        ZERO-02: Pre-execution validation is performed before handler execution.

        Args:
            message: Actor message to process
        """
        # ZERO-02: Pre-execution validation if ValidationMixin is available
        if hasattr(self, "validate_input"):
            is_valid, sanitized_content = await self.validate_input(
                input_data=message.content,
                operation=f"handle_{message.message_type}",
                source_id=message.sender,
            )
            if not is_valid:
                logger.warning(
                    f"[{self.agent_id}] ZERO-02 validation rejected message",
                    extra={
                        "message_type": message.message_type,
                        "sender": message.sender,
                    },
                )
                self.error_count += 1
                return
            # Update message content with sanitized version
            message.content = sanitized_content

        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                result = await handler(message)
                # Publish result if handler returns a dict and event mesh is available
                if result and isinstance(result, dict) and result.get("status") != "error":
                    reply_to = message.content.get("reply_to") if message.content else None
                    await self.send(
                        topic=reply_to or f"results.{message.message_type}",
                        content=result,
                        message_type=f"{message.message_type}_response",
                        correlation_id=message.correlation_id,
                    )
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error in handler for {message.message_type}: {e}",
                    exc_info=True,
                )
                self.error_count += 1
        else:
            logger.warning(
                f"[{self.agent_id}] No handler for message type: {message.message_type}"
            )

    async def broadcast(
        self,
        content: dict[str, Any],
        message_type: str = "broadcast",
    ) -> None:
        """
        Broadcast a message to all actors.

        Args:
            content: Message content
            message_type: Message type identifier
        """
        # Use event mesh broadcast if available
        event_mesh = self.get_state("_event_mesh")
        if event_mesh is not None:
            try:
                await event_mesh.broadcast_json({
                    "type": message_type,
                    "from": self.agent_id,
                    "content": content,
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                logger.info(
                    f"[{self.agent_id}] Broadcast sent via event mesh",
                    extra={"message_type": message_type},
                )
                return
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Event mesh broadcast failed: {e}",
                    extra={"message_type": message_type},
                )

        # Fallback: Broadcast to all actors via registry
        actor_registry = self._get_actor_registry()
        if actor_registry is not None:
            message = ActorMessage(
                sender=self.agent_id,
                message_type=message_type,
                content={
                    "message_type": message_type,
                    "content": content,
                    "sender": self.agent_id,
                },
                timestamp=datetime.now(UTC).isoformat(),
            )
            sent_count = 0
            for reg_actor_id, reg_actor in actor_registry.items():
                if reg_actor_id != self.agent_id:  # Don't send to self
                    try:
                        await reg_actor.put_message(message)
                        sent_count += 1
                    except Exception as e:
                        logger.error(
                            f"[{self.agent_id}] Broadcast to {reg_actor_id} failed: {e}",
                            extra={"message_type": message_type},
                        )
            logger.info(
                f"[{self.agent_id}] Broadcast sent to {sent_count} actors via registry",
                extra={"message_type": message_type},
            )
            return

        # Last resort: topic-based broadcast
        await self.send(
            topic="broadcast",
            content={
                "message_type": message_type,
                "content": content,
                "sender": self.agent_id,
            },
            message_type=message_type,
        )

    # Default message handlers with Zero-Trust validation
    async def _handle_health_check(self, message: ActorMessage) -> None:
        """Handle health check requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("health_check", message.content)
            if validated:
                reply_topic = validated.reply_to
            else:
                reply_topic = message.content.get("reply_to", "health")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Health check validation failed: {e}")
            return

        status = self.get_status()

        await self.send(
            topic=reply_topic,
            content={
                "message_type": "health_response",
                "status": {
                    "agent_id": status.agent_id,
                    "state": status.state.value,
                    "message_count": status.message_count,
                    "error_count": status.error_count,
                },
            },
            correlation_id=message.correlation_id,
        )

    async def _handle_suspend(self, message: ActorMessage) -> None:
        """Handle suspend requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            self._validate_message_content("suspend", message.content)
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Suspend validation failed: {e}")
            return
        await self.suspend()

    async def _handle_resume(self, message: ActorMessage) -> None:
        """Handle resume requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            self._validate_message_content("resume", message.content)
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Resume validation failed: {e}")
            return
        await self.resume()

    async def _handle_terminate(self, message: ActorMessage) -> None:
        """Handle terminate requests with validation."""
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("terminate", message.content)
            if validated and validated.reason:
                logger.info(f"[{self.agent_id}] Termination requested: {validated.reason}")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Terminate validation failed: {e}")
            return
        await self.terminate()

    async def _handle_collective_task(self, message: ActorMessage) -> None:
        """
        Handle collective task contribution requests with validation.

        This handler processes collective task requests and returns contributions.
        Subclasses can override this method to provide custom contribution logic.

        Args:
            message: ActorMessage with collective task details
        """
        # P2-7 fix: Validate input before processing
        try:
            validated = self._validate_message_content("collective_task", message.content)
            if validated:
                task_id = validated.task_id
                task_type = validated.task_type
                description = validated.description
                input_data = validated.input_data
                protocol = validated.protocol
                reply_to = validated.reply_to
            else:
                # Fallback to unvalidated access
                task_id = message.content.get("task_id")
                task_type = message.content.get("task_type")
                description = message.content.get("description")
                input_data = message.content.get("input_data", {})
                protocol = message.content.get("protocol", {})
                reply_to = message.content.get("reply_to")
        except ValueError as e:
            logger.error(f"[{self.agent_id}] Collective task validation failed: {e}")
            return

        logger.info(
            f"[{self.agent_id}] Received collective task",
            extra={
                "task_id": task_id,
                "task_type": task_type,
                "description": description,
            }
        )

        # Generate contribution (subclasses should override for custom logic)
        contribution = await self._generate_collective_contribution(
            task_id=task_id,
            task_type=task_type,
            description=description,
            input_data=input_data,
            protocol=protocol
        )

        # Send response if reply_to is provided
        if reply_to:
            await self.send(
                topic=reply_to,
                content={
                    "message_type": "collective_task_response",
                    "task_id": task_id,
                    "correlation_id": message.correlation_id,
                    **contribution
                },
                correlation_id=message.correlation_id,
            )

    async def _generate_collective_contribution(
        self,
        task_id: str,
        task_type: str,
        description: str,
        input_data: dict[str, Any],
        protocol: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate contribution for a collective task.

        Subclasses should override this method to provide custom contribution logic.
        Default implementation uses LLM if available, otherwise returns fallback.

        Args:
            task_id: Task identifier
            task_type: Type of task
            description: Task description
            input_data: Task input data
            protocol: Communication protocol

        Returns:
            Dict with contribution and confidence
        """
        # Try using LLM if available
        if hasattr(self, "swarms_agent") and self.swarms_agent is not None:
            try:
                prompt = f"""You are participating in a collective task.

Task Details:
- Task ID: {task_id}
- Task Type: {task_type}
- Description: {description}
- Input Data: {input_data}

Please provide your analysis and recommendation for this collective task."""

                response = await self.run_with_llm(prompt, timeout=60)
                return {
                    "contribution": {
                        "analysis": response,
                        "recommendation": "llm_generated",
                        "method": "run_with_llm"
                    },
                    "confidence": 0.75
                }
            except Exception as e:
                logger.error(f"[{self.agent_id}] LLM contribution error: {e}")

        # Fallback contribution
        return {
            "contribution": {
                "analysis": f"Analysis from {self.name} for task: {description}",
                "recommendation": f"{self.name}_recommendation",
                "method": "fallback"
            },
            "confidence": 0.6
        }

    def _get_actor_registry(self) -> dict[str, "AgentActor"] | None:
        """
        Get global actor registry from supervisor.

        This enables message delivery by accessing the supervisor's actor registry.

        Returns:
            Actor registry dict or None if supervisor not available
        """
        try:
            from heretek_swarm.actors.supervisor import get_supervisor
            supervisor = get_supervisor()
            if supervisor and hasattr(supervisor, "actors"):
                return supervisor.actors
        except (ImportError, Exception):
            logger.warning("Failed to retrieve supervisor actors", exc_info=True)
        return None

    async def run_with_llm(self, prompt: str, timeout: int = 60, **kwargs) -> str:
        """
        Run a prompt through the Swarms agent (if available).

        Args:
            prompt: Input prompt
            timeout: Timeout in seconds (default: 60)
            **kwargs: Additional arguments for agent run

        Returns:
            Agent response

        Raises:
            RuntimeError: If no Swarms agent configured
            asyncio.TimeoutError: If LLM call times out
        """
        if self.swarms_agent is None:
            raise RuntimeError("No Swarms agent configured")

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    self.swarms_agent.run,
                    prompt,
                    **kwargs,
                ),
                timeout=timeout,
            )
        except TimeoutError:
            logger.error(f"[{self.agent_id}] LLM call timed out after {timeout}s")
            raise
        except Exception as e:
            logger.error(f"[{self.agent_id}] LLM call failed: {e}", exc_info=True)
            raise

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to maintain actor liveness via NATS."""
        while self._running:
            try:
                self.last_activity = datetime.now(UTC).isoformat()

                # Publish heartbeat to NATS event mesh for Steward monitoring
                if self._event_mesh is not None:
                    heartbeat_data = {
                        "agent_id": self.agent_id,
                        "actor_type": getattr(self, "actor_type", "AgentActor"),
                        "state": self.state.value if hasattr(self, "state") else "active",
                        "timestamp": self.last_activity,
                        "error_count": getattr(self, "error_count", 0),
                        "mailbox_size": self.mailbox.qsize() if hasattr(self, "mailbox") else 0,
                    }
                    try:
                        await self._event_mesh.publish(
                            f"system.health.heartbeat.{self.agent_id}",
                            heartbeat_data,
                        )
                        logger.debug(
                            f"[{self.agent_id}] Heartbeat published",
                            extra={"state": heartbeat_data["state"]},
                        )
                    except Exception as e:
                        logger.warning(
                            f"[{self.agent_id}] Failed to publish heartbeat: {e}"
                        )

                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_id}] Heartbeat loop error: {e}")


# Bind message handling methods to AgentActor
AgentActor.send = AgentActorMessageHandling.send
AgentActor._queue_message = AgentActorMessageHandling._queue_message
AgentActor.send_to_actor = AgentActorMessageHandling.send_to_actor
AgentActor.send_with_reply = AgentActorMessageHandling.send_with_reply
AgentActor.put_message = AgentActorMessageHandling.put_message
AgentActor._process_mailbox = AgentActorMessageHandling._process_mailbox
AgentActor.process_message = AgentActorMessageHandling.process_message
AgentActor.broadcast = AgentActorMessageHandling.broadcast
AgentActor._handle_health_check = AgentActorMessageHandling._handle_health_check
AgentActor._handle_suspend = AgentActorMessageHandling._handle_suspend
AgentActor._handle_resume = AgentActorMessageHandling._handle_resume
AgentActor._handle_terminate = AgentActorMessageHandling._handle_terminate
AgentActor._handle_collective_task = AgentActorMessageHandling._handle_collective_task
AgentActor._generate_collective_contribution = AgentActorMessageHandling._generate_collective_contribution
AgentActor._get_actor_registry = AgentActorMessageHandling._get_actor_registry
AgentActor.run_with_llm = AgentActorMessageHandling.run_with_llm
AgentActor._heartbeat_loop = AgentActorMessageHandling._heartbeat_loop
