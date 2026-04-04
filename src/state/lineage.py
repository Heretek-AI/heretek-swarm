"""
Message Lineage Tracking System.

Provides complete provenance tracking for all messages in the system,
enabling replay, debugging, and audit capabilities.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

from .base import MessageLineage, MessageType

logger = structlog.get_logger()


class LineageConfig(BaseModel):
    """Configuration for lineage tracking"""
    
    # Storage
    max_lineage_depth: int = Field(default=100, ge=1, le=1000)
    max_children_per_node: int = Field(default=100, ge=1, le=1000)
    max_lineage_entries: int = Field(default=100000, ge=1000)
    
    # Retention
    default_retention_days: int = Field(default=30)
    max_retention_days: int = Field(default=365)
    
    # Performance
    cache_size: int = Field(default=10000)
    batch_persist_size: int = Field(default=100)
    
    # Features
    enable_branching: bool = Field(default=True)
    enable_replay: bool = Field(default=True)
    track_content_hash: bool = Field(default=True)


class LineageNode:
    """
    In-memory node in the lineage tree.
    
    Optimized for fast traversal and lookups.
    """
    
    def __init__(self, lineage: MessageLineage):
        self.lineage = lineage
        self.children: List[UUID] = []
        self.parent: Optional[UUID] = lineage.parent_message_id
        self._lock = asyncio.Lock()
    
    def add_child(self, child_id: UUID) -> None:
        """Add a child message"""
        if child_id not in self.children:
            self.children.append(child_id)
            self.lineage.child_count = len(self.children)
    
    def is_branch_point(self) -> bool:
        """Check if this is a branch point"""
        return len(self.children) > 1 or self.lineage.is_branch_point


class LineageTracker:
    """
    Tracks message lineage across the multi-agent system.
    
    Features:
    - Complete message provenance
    - Branch point detection
    - Ancestry queries
    - Message replay support
    - Integrity verification
    """
    
    def __init__(self, config: Optional[LineageConfig] = None):
        self.config = config or LineageConfig()
        
        # In-memory storage
        self._nodes: Dict[UUID, LineageNode] = {}
        self._conversation_roots: Dict[UUID, UUID] = {}  # conversation_id -> root_message_id
        self._agent_messages: Dict[str, Set[UUID]] = {}  # agent_id -> message_ids
        
        # LRU cache for frequently accessed lineages
        self._cache: Dict[UUID, MessageLineage] = {}
        self._cache_order: List[UUID] = []
        
        # Metrics
        self._total_messages = 0
        self._branch_points = 0
        self._cache_hits = 0
        self._queries = 0
    
    def _compute_hash(self, content: Any) -> str:
        """Compute SHA256 hash of content"""
        import json
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _cache_get(self, message_id: UUID) -> Optional[MessageLineage]:
        """Get from cache"""
        if message_id in self._cache:
            self._cache_hits += 1
            # Update access order
            if message_id in self._cache_order:
                self._cache_order.remove(message_id)
            self._cache_order.append(message_id)
            return self._cache[message_id]
        return None
    
    def _cache_set(self, message_id: UUID, lineage: MessageLineage) -> None:
        """Set in cache with LRU eviction"""
        # Evict if at capacity
        while len(self._cache) >= self.config.cache_size and self._cache_order:
            oldest = self._cache_order.pop(0)
            del self._cache[oldest]
        
        self._cache[message_id] = lineage
        self._cache_order.append(message_id)
    
    async def record_message(
        self,
        content: Any,
        conversation_id: UUID,
        sender_agent_id: str,
        receiver_agent_id: Optional[str] = None,
        message_type: MessageType = MessageType.TASK,
        parent_message_id: Optional[UUID] = None,
        correlation_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageLineage:
        """
        Record a new message in the lineage.
        
        Args:
            content: Message content
            conversation_id: Conversation/session ID
            sender_agent_id: Sending agent
            receiver_agent_id: Receiving agent
            message_type: Type of message
            parent_message_id: Parent message (None for root)
            correlation_id: Correlation ID for related messages
            tags: Tags for categorization
            metadata: Additional metadata
        
        Returns:
            The created lineage entry
        """
        # Compute content hash
        content_hash = self._compute_hash(content) if self.config.track_content_hash else ""
        content_size = len(str(content).encode())
        
        # Determine root and ancestors
        root_message_id: UUID
        ancestor_ids: List[UUID] = []
        depth: int = 0
        
        if parent_message_id:
            parent_node = self._nodes.get(parent_message_id)
            if parent_node:
                root_message_id = parent_node.lineage.root_message_id
                ancestor_ids = parent_node.lineage.ancestor_ids + [parent_message_id]
                depth = parent_node.lineage.depth + 1
                
                # Check depth limit
                if depth > self.config.max_lineage_depth:
                    logger.warning(
                        "lineage_depth_exceeded",
                        message_id=str(parent_message_id),
                        depth=depth
                    )
            else:
                # Parent not found, this becomes root
                root_message_id = uuid4()
        else:
            # This is a root message
            root_message_id = uuid4()
        
        # Create lineage entry
        lineage = MessageLineage(
            message_id=uuid4(),
            conversation_id=conversation_id,
            parent_message_id=parent_message_id,
            root_message_id=root_message_id,
            ancestor_ids=ancestor_ids,
            depth=depth,
            message_type=message_type,
            sender_agent_id=sender_agent_id,
            receiver_agent_id=receiver_agent_id,
            content_hash=content_hash,
            content_size_bytes=content_size,
            correlation_id=correlation_id,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Create node
        node = LineageNode(lineage)
        
        # Update parent's children
        if parent_message_id and parent_message_id in self._nodes:
            parent_node = self._nodes[parent_message_id]
            parent_node.add_child(lineage.message_id)
            
            # Track branch points
            if parent_node.is_branch_point():
                self._branch_points += 1
        
        # Store in memory
        self._nodes[lineage.message_id] = node
        
        # Track conversation root
        if parent_message_id is None:
            self._conversation_roots[conversation_id] = lineage.message_id
        
        # Track by agent
        if sender_agent_id not in self._agent_messages:
            self._agent_messages[sender_agent_id] = set()
        self._agent_messages[sender_agent_id].add(lineage.message_id)
        
        if receiver_agent_id:
            if receiver_agent_id not in self._agent_messages:
                self._agent_messages[receiver_agent_id] = set()
            self._agent_messages[receiver_agent_id].add(lineage.message_id)
        
        # Cache
        self._cache_set(lineage.message_id, lineage)
        
        self._total_messages += 1
        
        logger.debug(
            "message_lineage_recorded",
            message_id=str(lineage.message_id),
            conversation_id=str(conversation_id),
            sender=sender_agent_id,
            receiver=receiver_agent_id,
            depth=depth
        )
        
        return lineage
    
    async def get_lineage(self, message_id: UUID) -> Optional[MessageLineage]:
        """Get lineage for a message"""
        self._queries += 1
        
        # Check cache first
        cached = self._cache_get(message_id)
        if cached:
            return cached
        
        # Look up in nodes
        node = self._nodes.get(message_id)
        if node:
            self._cache_set(message_id, node.lineage)
            return node.lineage
        
        return None
    
    async def get_ancestry(
        self,
        message_id: UUID,
        include_content: bool = False
    ) -> List[MessageLineage]:
        """
        Get complete ancestry of a message.
        
        Returns messages from root to this message.
        """
        lineage = await self.get_lineage(message_id)
        if not lineage:
            return []
        
        # Collect ancestors
        ancestors = []
        
        for ancestor_id in lineage.ancestor_ids:
            ancestor = await self.get_lineage(ancestor_id)
            if ancestor:
                ancestors.append(ancestor)
        
        # Add this message
        ancestors.append(lineage)
        
        return ancestors
    
    async def get_descendants(
        self,
        message_id: UUID,
        max_depth: int = 10
    ) -> List[MessageLineage]:
        """
        Get all descendants of a message.
        
        Performs breadth-first traversal.
        """
        node = self._nodes.get(message_id)
        if not node:
            return []
        
        descendants = []
        visited: Set[UUID] = set()
        queue: List[Tuple[UUID, int]] = [(message_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            current_node = self._nodes.get(current_id)
            
            if current_node:
                if current_id != message_id:
                    descendants.append(current_node.lineage)
                
                for child_id in current_node.children:
                    queue.append((child_id, depth + 1))
        
        return descendants
    
    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        limit: int = 100
    ) -> List[MessageLineage]:
        """Get all messages in a conversation"""
        root_id = self._conversation_roots.get(conversation_id)
        if not root_id:
            return []
        
        # Get all descendants
        all_messages = await self.get_descendants(root_id, max_depth=100)
        
        # Add root
        root = await self.get_lineage(root_id)
        if root:
            all_messages.insert(0, root)
        
        # Sort by creation time
        all_messages.sort(key=lambda m: m.created_at)
        
        return all_messages[:limit]
    
    async def get_agent_messages(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[MessageLineage]:
        """Get messages involving an agent"""
        message_ids = self._agent_messages.get(agent_id, set())
        
        messages = []
        for msg_id in list(message_ids)[:limit]:
            lineage = await self.get_lineage(msg_id)
            if lineage:
                messages.append(lineage)
        
        # Sort by creation time
        messages.sort(key=lambda m: m.created_at, reverse=True)
        
        return messages[:limit]
    
    async def find_branch_points(
        self,
        conversation_id: Optional[UUID] = None
    ) -> List[MessageLineage]:
        """Find all branch points in lineage tree"""
        branch_points = []
        
        for node in self._nodes.values():
            if node.is_branch_point():
                if conversation_id is None or node.lineage.conversation_id == conversation_id:
                    branch_points.append(node.lineage)
        
        return branch_points
    
    async def get_message_path(
        self,
        from_message_id: UUID,
        to_message_id: UUID
    ) -> Optional[List[UUID]]:
        """
        Find path between two messages.
        
        Returns list of message IDs from from_message_id to to_message_id,
        or None if no path exists.
        """
        # Use BFS to find path
        visited: Set[UUID] = set()
        queue: List[Tuple[UUID, List[UUID]]] = [(from_message_id, [from_message_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id == to_message_id:
                return path
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Check ancestors
            lineage = await self.get_lineage(current_id)
            if lineage:
                for ancestor_id in lineage.ancestor_ids:
                    if ancestor_id not in visited:
                        queue.append((ancestor_id, path + [ancestor_id]))
            
            # Check descendants
            node = self._nodes.get(current_id)
            if node:
                for child_id in node.children:
                    if child_id not in visited:
                        queue.append((child_id, path + [child_id]))
        
        return None
    
    async def mark_delivered(self, message_id: UUID) -> bool:
        """Mark a message as delivered"""
        node = self._nodes.get(message_id)
        if node:
            node.lineage.delivered_at = datetime.utcnow()
            return True
        return False
    
    async def mark_processed(self, message_id: UUID) -> bool:
        """Mark a message as processed"""
        node = self._nodes.get(message_id)
        if node:
            node.lineage.processed_at = datetime.utcnow()
            return True
        return False
    
    async def verify_integrity(self, message_id: UUID) -> bool:
        """Verify integrity of a message and its ancestors"""
        lineage = await self.get_lineage(message_id)
        if not lineage:
            return False
        
        # Verify ancestors exist
        for ancestor_id in lineage.ancestor_ids:
            if ancestor_id not in self._nodes:
                logger.warning(
                    "lineage_integrity_missing_ancestor",
                    message_id=str(message_id),
                    missing_ancestor=str(ancestor_id)
                )
                return False
        
        # Verify parent exists if specified
        if lineage.parent_message_id:
            if lineage.parent_message_id not in self._nodes:
                logger.warning(
                    "lineage_integrity_missing_parent",
                    message_id=str(message_id),
                    parent_id=str(lineage.parent_message_id)
                )
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get lineage statistics"""
        avg_depth = 0.0
        max_depth = 0
        
        if self._nodes:
            depths = [n.lineage.depth for n in self._nodes.values()]
            avg_depth = sum(depths) / len(depths)
            max_depth = max(depths)
        
        cache_hit_rate = (
            self._cache_hits / self._queries if self._queries > 0 else 0
        )
        
        return {
            "total_messages": self._total_messages,
            "active_messages": len(self._nodes),
            "conversations": len(self._conversation_roots),
            "branch_points": self._branch_points,
            "avg_depth": avg_depth,
            "max_depth": max_depth,
            "cache_size": len(self._cache),
            "cache_hit_rate": cache_hit_rate,
            "total_queries": self._queries,
        }
    
    async def cleanup_expired(self, days: int = 30) -> int:
        """Remove expired lineage entries"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        to_remove = []
        for message_id, node in self._nodes.items():
            if node.lineage.created_at < cutoff:
                to_remove.append(message_id)
        
        for message_id in to_remove:
            del self._nodes[message_id]
            self._cache.pop(message_id, None)
        
        logger.info(
            "lineage_cleanup_completed",
            removed_count=len(to_remove)
        )
        
        return len(to_remove)
