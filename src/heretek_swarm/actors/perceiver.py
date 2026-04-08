"""
Perceiver Agent - Multi-Modal Sensory Input Processing.

The Perceiver agent provides:
- Multi-modal input handling (text, image, audio, video)
- Feature extraction and preprocessing
- Sensory data normalization and encoding
- Cross-modal correlation and fusion
- Input quality assessment and filtering

Named for the ability to perceive and process sensory information from multiple sources.
"""

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import structlog
from swarms import Agent

from heretek_swarm.actors.base import AgentActor, ActorMessage
from heretek_swarm.actors.validation import validate_message, MessageContent

# Session 44: Collective Learning Integration
from heretek_swarm.collective.learning import PatternExtractor, PatternType

# Session 44: Consensus Integration
from heretek_swarm.consensus.swarm_deliberation import SwarmDeliberationEngine, Position

# Session 44: Memory Optimization Integration
from heretek_swarm.memory.access_patterns import AccessPatternAnalyzer, AccessTier

# Session 44: Zero-Trust Validation
from heretek_swarm.security.zero_trust import ZeroTrustValidator


logger = structlog.get_logger("PerceiverAgent")


class ModalityType(str, Enum):
    """Supported input modalities."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    SENSOR = "sensor"


class PerceiverAgent(AgentActor):
    """
    Perceiver Agent - Multi-Modal Sensory Input Processing Specialist.

    The Perceiver is responsible for:
    - Receiving and classifying multi-modal inputs
    - Extracting features from sensory data
    - Normalizing and encoding inputs for downstream agents
    - Correlating information across modalities
    - Assessing input quality and filtering noise

    Sensory Processing Workflow:
    1. Receive input with modality classification
    2. Validate input format and quality
    3. Extract modality-specific features
    4. Normalize and encode for swarm consumption
    5. Store processed data in Historian memory
    6. Notify relevant agents of new input
    """

    def __init__(
        self,
        agent_id: str = "perceiver",
        name: str = "Perceiver",
        description: str = "Multi-modal sensory input processing specialist",
        swarms_agent: Optional[Agent] = None,
        max_input_size_mb: int = 50,
        feature_cache_size: int = 1000,
        enable_cross_modal: bool = True,
        pattern_extractor: Optional[PatternExtractor] = None,
        deliberation_engine: Optional[SwarmDeliberationEngine] = None,
        access_analyzer: Optional[AccessPatternAnalyzer] = None,
        zero_trust_validator: Optional[ZeroTrustValidator] = None,
        **kwargs,
    ) -> None:
        """
        Initialize the Perceiver agent.

        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            swarms_agent: Optional Swarms Agent for LLM capabilities
            max_input_size_mb: Maximum input size in megabytes
            feature_cache_size: Maximum cached feature entries
            enable_cross_modal: Enable cross-modal correlation
            **kwargs: Additional arguments
        """
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            topics=[
                "sensory-input",
                "multi-modal",
                "feature-extraction",
                "preprocessing",
            ],
            capabilities=[
                "text-processing",
                "image-analysis",
                "audio-processing",
                "video-analysis",
                "document-parsing",
                "sensor-data",
                "feature-extraction",
                "cross-modal-fusion",
            ],
            swarms_agent=swarms_agent,
            **kwargs,
        )

        # Perceiver-specific configuration
        self.max_input_size_mb = max_input_size_mb
        self.feature_cache_size = feature_cache_size
        self.enable_cross_modal = enable_cross_modal

        # Processing statistics
        self.inputs_processed: Dict[str, int] = {
            modality.value: 0 for modality in ModalityType
        }
        self.total_features_extracted = 0
        self.quality_rejections = 0

        # Feature cache for cross-modal correlation
        self.feature_cache: Dict[str, Dict[str, Any]] = {}
        self.cross_modal_correlations: List[Dict[str, Any]] = []

        # Supported formats per modality
        self.supported_formats: Dict[str, List[str]] = {
            ModalityType.TEXT.value: ["txt", "md", "json", "xml", "html"],
            ModalityType.IMAGE.value: ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"],
            ModalityType.AUDIO.value: ["mp3", "wav", "ogg", "flac", "aac"],
            ModalityType.VIDEO.value: ["mp4", "avi", "mov", "webm", "mkv"],
            ModalityType.DOCUMENT.value: ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx"],
            ModalityType.SENSOR.value: ["json", "csv", "binary"],
        }

        
        # Session 44: Collective Learning Integration
        self.pattern_extractor = pattern_extractor or PatternExtractor(min_support=3, min_confidence=0.6)
        
        # Session 44: Consensus Integration
        self.deliberation_engine = deliberation_engine or SwarmDeliberationEngine(
            max_rounds=5, consensus_threshold=0.75, min_participants=2
        )
        
        # Session 44: Memory Optimization Integration
        self.access_analyzer = access_analyzer or AccessPatternAnalyzer()
        
        # Session 44: Zero-Trust Validation
        self.zero_trust_validator = zero_trust_validator or ZeroTrustValidator()
        
        # Session 44: Integration state
        self._active_deliberations: Dict[str, str] = {}
        self._pattern_emitted: Set[str] = set()


        logger.info(f"[{self.agent_id}] Perceiver agent initialized")

    async def initialize(self) -> None:
        """Initialize the Perceiver agent."""
        # Register message handlers with Zero-Trust validation
        self.register_handler("process_input", self._handle_process_input)
        self.register_handler("extract_features", self._handle_extract_features)
        self.register_handler("classify_modality", self._handle_classify_modality)
        self.register_handler("assess_quality", self._handle_assess_quality)
        self.register_handler("get_processing_stats", self._handle_get_processing_stats)
        self.register_handler("correlate_modalities", self._handle_correlate_modalities)

        logger.info(f"[{self.agent_id}] Perceiver initialization complete")

    async def process_message(self, message: ActorMessage) -> None:
        """
        Process incoming messages with exception handling.

        Args:
            message: Actor message to process
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(
                    f"[{self.agent_id}] Error processing message {message.message_type}: {e}",
                    exc_info=True,
                )
                self.error_count += 1
                if message.content.get("reply_to"):
                    await self.send(
                        topic=message.content["reply_to"],
                        content={
                            "message_type": "error_response",
                            "error": str(e),
                            "original_message_type": message.message_type,
                        },
                        correlation_id=message.correlation_id,
                    )
        else:
            logger.warning(
                f"[{self.agent_id}] No handler for message type: {message.message_type}"
            )

    def _validate_message_content(self, message_type: str, content: Dict[str, Any]) -> Any:
        """Validate message content using Pydantic models."""
        try:
            return validate_message(message_type, content)
        except ValidationError as e:
            logger.warning(
                f"[{self.agent_id}] Message validation failed for {message_type}: {e}",
                extra={"validation_errors": e.errors()},
            )
            raise ValueError(f"Invalid message format: {e.errors()}")
        except KeyError:
            logger.debug(f"[{self.agent_id}] No validator for message type: {message_type}")
            return None

    async def _handle_process_input(self, message: ActorMessage) -> None:
        """
        Process multi-modal input.

        Args:
            message: ActorMessage with content containing:
                - input_data: The raw input (text, base64 data, or URL)
                - modality: Optional modality type (auto-detected if not provided)
                - format: Optional format hint (e.g., 'jpg', 'txt')
                - metadata: Optional metadata dict
                - priority: Optional priority level (1-10)

        Response:
            - input_id: Unique identifier for this input
            - modality: Detected/provided modality
            - features: Extracted features
            - quality_score: Input quality assessment (0-1)
            - timestamp: Processing timestamp
        """
        try:
            content = message.content
            input_data = content.get("input_data")
            modality = content.get("modality")
            format_hint = content.get("format")
            metadata = content.get("metadata", {})
            priority = content.get("priority", 5)

            if input_data is None:
                await self._send_error_response(message, "Missing input_data")
                return

            # Validate input size
            if not self._validate_input_size(input_data):
                self.quality_rejections += 1
                await self._send_error_response(
                    message, f"Input exceeds maximum size ({self.max_input_size_mb}MB)"
                )
                return

            # Auto-detect modality if not provided
            if not modality:
                modality = self._detect_modality(input_data, format_hint)

            # Generate unique input ID
            input_id = self._generate_input_id(input_data, modality)

            # Extract features based on modality
            features = await self._extract_modality_features(
                input_data, modality, format_hint
            )

            # Assess quality
            quality_score = self._assess_input_quality(input_data, modality, features)

            # Cache features for cross-modal correlation
            self._cache_features(input_id, modality, features, metadata)

            # Update statistics
            self.inputs_processed[modality] = self.inputs_processed.get(modality, 0) + 1
            self.total_features_extracted += len(features) if features else 0

            # Store in Historian if available
            await self._store_in_historian(input_id, modality, features, metadata)

            # Send response
            await self.send(
                topic=content.get("reply_to", "actor:*"),
                content={
                    "message_type": "input_processed",
                    "input_id": input_id,
                    "modality": modality,
                    "features": features,
                    "quality_score": quality_score,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                correlation_id=message.correlation_id,
            )

            logger.info(
                f"[{self.agent_id}] Input processed: {input_id[:8]}...",
                extra={"modality": modality, "quality": quality_score},
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Input processing failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Input processing failed: {e}")

    def _validate_input_size(self, input_data: Any) -> bool:
        """Validate input does not exceed maximum size."""
        try:
            max_bytes = self.max_input_size_mb * 1024 * 1024
            if isinstance(input_data, str):
                return len(input_data.encode()) <= max_bytes
            elif isinstance(input_data, bytes):
                return len(input_data) <= max_bytes
            elif isinstance(input_data, dict):
                import json
                return len(json.dumps(input_data).encode()) <= max_bytes
            return True  # Assume valid for other types
        except Exception:
            return True  # Fail open on validation errors

    def _detect_modality(
        self, input_data: Any, format_hint: Optional[str] = None
    ) -> str:
        """Auto-detect input modality."""
        if format_hint:
            format_lower = format_hint.lower()
            if format_lower in ["txt", "md", "json", "xml", "html"]:
                return ModalityType.TEXT.value
            elif format_lower in ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"]:
                return ModalityType.IMAGE.value
            elif format_lower in ["mp3", "wav", "ogg", "flac", "aac"]:
                return ModalityType.AUDIO.value
            elif format_lower in ["mp4", "avi", "mov", "webm", "mkv"]:
                return ModalityType.VIDEO.value
            elif format_lower in ["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx"]:
                return ModalityType.DOCUMENT.value

        # Content-based detection
        if isinstance(input_data, str):
            # Check if it's base64 encoded
            if input_data.startswith("data:"):
                # Data URL format
                mime_type = input_data.split(":")[1].split(";")[0]
                if "image" in mime_type:
                    return ModalityType.IMAGE.value
                elif "audio" in mime_type:
                    return ModalityType.AUDIO.value
                elif "video" in mime_type:
                    return ModalityType.VIDEO.value
            # Plain text
            return ModalityType.TEXT.value
        elif isinstance(input_data, bytes):
            # Try to detect from magic bytes
            if input_data.startswith(b"\xff\xd8\xff"):
                return ModalityType.IMAGE.value  # JPEG
            elif input_data.startswith(b"\x89PNG"):
                return ModalityType.IMAGE.value  # PNG
            elif input_data.startswith(b"RIFF") and input_data[8:12] == b"WAVE":
                return ModalityType.AUDIO.value  # WAV
            return ModalityType.TEXT.value  # Default to text
        elif isinstance(input_data, dict):
            return ModalityType.SENSOR.value

        return ModalityType.TEXT.value

    def _generate_input_id(self, input_data: Any, modality: str) -> str:
        """Generate unique input identifier."""
        # Create hash of input data for deduplication
        if isinstance(input_data, str):
            data_bytes = input_data.encode()
        elif isinstance(input_data, bytes):
            data_bytes = input_data
        else:
            import json
            data_bytes = json.dumps(input_data, sort_keys=True).encode()

        hash_digest = hashlib.sha256(data_bytes).hexdigest()[:16]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"input_{modality}_{timestamp}_{hash_digest}"

    async def _extract_modality_features(
        self, input_data: Any, modality: str, format_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Extract features based on modality."""
        try:
            if modality == ModalityType.TEXT.value:
                return self._extract_text_features(input_data)
            elif modality == ModalityType.IMAGE.value:
                return await self._extract_image_features(input_data, format_hint)
            elif modality == ModalityType.AUDIO.value:
                return await self._extract_audio_features(input_data, format_hint)
            elif modality == ModalityType.VIDEO.value:
                return await self._extract_video_features(input_data, format_hint)
            elif modality == ModalityType.DOCUMENT.value:
                return await self._extract_document_features(input_data, format_hint)
            elif modality == ModalityType.SENSOR.value:
                return self._extract_sensor_features(input_data)
            else:
                return {"error": f"Unknown modality: {modality}"}
        except Exception as e:
            logger.error(f"[{self.agent_id}] Feature extraction failed: {e}")
            return {"error": str(e)}

    def _extract_text_features(self, text: str) -> Dict[str, Any]:
        """Extract features from text input."""
        if not isinstance(text, str):
            text = str(text)

        # Basic text statistics
        words = text.split()
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        # Character-level features
        char_count = len(text)
        char_count_no_spaces = len(text.replace(" ", ""))

        # Word-level features
        word_count = len(words)
        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0

        # Sentence-level features
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # Vocabulary features
        unique_words = set(w.lower() for w in words)
        vocabulary_richness = len(unique_words) / word_count if word_count > 0 else 0

        # Detect potential language patterns
        has_code = any(c in text for c in "{}[]()=;") and ("function" in text or "def " in text or "import " in text)
        has_json = text.strip().startswith(("{", "["))
        has_xml = text.strip().startswith("<")

        return {
            "char_count": char_count,
            "char_count_no_spaces": char_count_no_spaces,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "unique_words": len(unique_words),
            "vocabulary_richness": round(vocabulary_richness, 3),
            "has_code_structure": has_code,
            "has_json_format": has_json,
            "has_xml_format": has_xml,
            "preview": text[:200] if len(text) > 200 else text,
        }

    async def _extract_image_features(
        self, image_data: Any, format_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Extract features from image input."""
        # If LLM with vision capabilities is available, use it
        if self.swarms_agent and self.swarms_agent.llm:
            try:
                # For base64 encoded images
                if isinstance(image_data, str) and image_data.startswith("data:"):
                    description = await asyncio.wait_for(
                        self._describe_image_llm(image_data),
                        timeout=60,
                    )
                    return {
                        "description": description,
                        "format": format_hint or "unknown",
                        "analyzed_by": "llm",
                    }
            except asyncio.TimeoutError:
                logger.warning(f"[{self.agent_id}] Image LLM analysis timed out")
            except Exception as e:
                logger.error(f"[{self.agent_id}] Image LLM analysis error: {e}")

        # Fallback: basic metadata extraction
        if isinstance(image_data, str):
            if image_data.startswith("data:"):
                # Extract MIME type from data URL
                mime_type = image_data.split(":")[1].split(";")[0]
                size_bytes = len(image_data.encode())
            else:
                mime_type = "unknown"
                size_bytes = len(image_data.encode())
        elif isinstance(image_data, bytes):
            mime_type = "unknown"
            size_bytes = len(image_data)
        else:
            mime_type = "unknown"
            size_bytes = 0

        return {
            "format": format_hint or "unknown",
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "analyzed_by": "metadata",
        }

    async def _describe_image_llm(self, image_data: str) -> str:
        """Use LLM to describe an image."""
        prompt = "Describe this image in detail, including any text, objects, people, colors, and the overall scene."
        # Note: Actual implementation would depend on LLM capabilities
        # This is a placeholder for vision-capable LLM integration
        return f"Image analysis requested with prompt: {prompt}"

    async def _extract_audio_features(
        self, audio_data: Any, format_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Extract features from audio input."""
        # Placeholder for audio feature extraction
        # In production, would use libraries like librosa for:
        # - Duration
        # - Sample rate
        # - Spectral features (MFCCs, chroma, etc.)
        # - Tempo and rhythm analysis

        if isinstance(audio_data, str):
            size_bytes = len(audio_data.encode())
        elif isinstance(audio_data, bytes):
            size_bytes = len(audio_data)
        else:
            size_bytes = 0

        return {
            "format": format_hint or "unknown",
            "size_bytes": size_bytes,
            "analyzed_by": "metadata",
            "note": "Full audio analysis requires librosa or similar library",
        }

    async def _extract_video_features(
        self, video_data: Any, format_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Extract features from video input."""
        # Placeholder for video feature extraction
        # In production, would use libraries like opencv-python for:
        # - Duration and frame count
        # - Resolution and aspect ratio
        # - Frame rate
        # - Key frame extraction
        # - Motion analysis

        if isinstance(video_data, str):
            size_bytes = len(video_data.encode())
        elif isinstance(video_data, bytes):
            size_bytes = len(video_data)
        else:
            size_bytes = 0

        return {
            "format": format_hint or "unknown",
            "size_bytes": size_bytes,
            "analyzed_by": "metadata",
            "note": "Full video analysis requires opencv-python or similar library",
        }

    async def _extract_document_features(
        self, doc_data: Any, format_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Extract features from document input."""
        # Placeholder for document feature extraction
        # In production, would use libraries like:
        # - PyPDF2 for PDFs
        # - python-docx for Word documents
        # - openpyxl for Excel spreadsheets

        if isinstance(doc_data, str):
            size_bytes = len(doc_data.encode())
            preview = doc_data[:500] if len(doc_data) > 500 else doc_data
        elif isinstance(doc_data, bytes):
            size_bytes = len(doc_data)
            preview = "binary data"
        else:
            size_bytes = 0
            preview = "unknown format"

        return {
            "format": format_hint or "unknown",
            "size_bytes": size_bytes,
            "preview": preview,
            "analyzed_by": "metadata",
            "note": "Full document analysis requires PyPDF2/python-docx/openpyxl",
        }

    def _extract_sensor_features(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from sensor data."""
        if not isinstance(sensor_data, dict):
            return {"error": "Sensor data must be a dictionary"}

        # Extract basic statistics from numeric values
        numeric_values = []
        for key, value in sensor_data.items():
            if isinstance(value, (int, float)):
                numeric_values.append(value)

        stats = {}
        if numeric_values:
            stats = {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values),
                "count": len(numeric_values),
            }

        return {
            "keys": list(sensor_data.keys()),
            "numeric_stats": stats,
            "analyzed_by": "sensor_parser",
        }

    def _assess_input_quality(
        self, input_data: Any, modality: str, features: Dict[str, Any]
    ) -> float:
        """Assess input quality (0-1 score)."""
        quality_score = 1.0

        # Check for errors in features
        if "error" in features:
            quality_score -= 0.5

        # Modality-specific quality checks
        if modality == ModalityType.TEXT.value:
            # Check for meaningful content
            word_count = features.get("word_count", 0)
            if word_count < 3:
                quality_score -= 0.3
            if word_count > 100000:
                quality_score -= 0.2  # Very long text may need chunking

        elif modality == ModalityType.IMAGE.value:
            size_bytes = features.get("size_bytes", 0)
            if size_bytes < 1000:
                quality_score -= 0.4  # Very small image
            if size_bytes > 50 * 1024 * 1024:
                quality_score -= 0.3  # Very large image

        # Ensure score stays in valid range
        return max(0.0, min(1.0, quality_score))

    def _cache_features(
        self, input_id: str, modality: str, features: Dict[str, Any], metadata: Dict[str, Any]
    ) -> None:
        """Cache features for cross-modal correlation."""
        if not self.enable_cross_modal:
            return

        self.feature_cache[input_id] = {
            "modality": modality,
            "features": features,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Enforce cache size limit
        if len(self.feature_cache) > self.feature_cache_size:
            # Remove oldest entries
            sorted_keys = sorted(
                self.feature_cache.keys(),
                key=lambda k: self.feature_cache[k]["timestamp"]
            )
            for key in sorted_keys[:100]:  # Remove 100 oldest
                del self.feature_cache[key]

    async def _store_in_historian(
        self, input_id: str, modality: str, features: Dict[str, Any], metadata: Dict[str, Any]
    ) -> None:
        """Store processed input in Historian memory."""
        try:
            await self.send(
                topic="actor:historian",
                content={
                    "message_type": "store_memory",
                    "content": {
                        "input_id": input_id,
                        "modality": modality,
                        "features": features,
                        "metadata": metadata,
                    },
                    "metadata": {
                        "source": "perceiver",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                },
            )
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Failed to store in Historian: {e}")

    async def _handle_extract_features(self, message: ActorMessage) -> None:
        """
        Extract features from existing input.

        Args:
            message: ActorMessage with content containing:
                - input_id: ID of previously processed input
                - modality: Optional modality override
        """
        try:
            content = message.content
            input_id = content.get("input_id")

            if not input_id:
                await self._send_error_response(message, "Missing input_id")
                return

            cached = self.feature_cache.get(input_id)
            if not cached:
                await self._send_error_response(message, f"Input not found: {input_id}")
                return

            await self.send(
                topic=content.get("reply_to"),
                content={
                    "message_type": "features_result",
                    "input_id": input_id,
                    **cached,
                },
                correlation_id=message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Feature extraction failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Feature extraction failed: {e}")

    async def _handle_classify_modality(self, message: ActorMessage) -> None:
        """
        Classify input modality.

        Args:
            message: ActorMessage with content containing:
                - input_data: Data to classify
                - format_hint: Optional format hint
        """
        try:
            content = message.content
            input_data = content.get("input_data")
            format_hint = content.get("format_hint")

            if input_data is None:
                await self._send_error_response(message, "Missing input_data")
                return

            modality = self._detect_modality(input_data, format_hint)

            await self.send(
                topic=content.get("reply_to"),
                content={
                    "message_type": "modality_result",
                    "modality": modality,
                    "confidence": 0.8,  # Placeholder confidence
                },
                correlation_id=message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Modality classification failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Classification failed: {e}")

    async def _handle_assess_quality(self, message: ActorMessage) -> None:
        """
        Assess input quality.

        Args:
            message: ActorMessage with content containing:
                - input_id: ID of input to assess
        """
        try:
            content = message.content
            input_id = content.get("input_id")

            if not input_id:
                await self._send_error_response(message, "Missing input_id")
                return

            cached = self.feature_cache.get(input_id)
            if not cached:
                await self._send_error_response(message, f"Input not found: {input_id}")
                return

            quality_score = self._assess_input_quality(
                None, cached["modality"], cached["features"]
            )

            await self.send(
                topic=content.get("reply_to"),
                content={
                    "message_type": "quality_result",
                    "input_id": input_id,
                    "quality_score": quality_score,
                },
                correlation_id=message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Quality assessment failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Quality assessment failed: {e}")

    async def _handle_get_processing_stats(self, message: ActorMessage) -> None:
        """
        Get processing statistics.

        Args:
            message: ActorMessage
        """
        try:
            stats = {
                "inputs_processed": self.inputs_processed.copy(),
                "total_features_extracted": self.total_features_extracted,
                "quality_rejections": self.quality_rejections,
                "cache_size": len(self.feature_cache),
                "cross_modal_correlations": len(self.cross_modal_correlations),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await self.send(
                topic=message.content.get("reply_to"),
                content={
                    "message_type": "stats_result",
                    **stats,
                },
                correlation_id=message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Stats retrieval failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Stats retrieval failed: {e}")

    async def _handle_correlate_modalities(self, message: ActorMessage) -> None:
        """
        Find cross-modal correlations.

        Args:
            message: ActorMessage with content containing:
                - input_ids: List of input IDs to correlate
        """
        try:
            content = message.content
            input_ids = content.get("input_ids", [])

            if len(input_ids) < 2:
                await self._send_error_response(
                    message, "At least 2 input_ids required for correlation"
                )
                return

            correlations = []
            for i, id1 in enumerate(input_ids):
                for id2 in input_ids[i+1:]:
                    data1 = self.feature_cache.get(id1)
                    data2 = self.feature_cache.get(id2)

                    if data1 and data2:
                        correlation = {
                            "input_1": id1,
                            "input_2": id2,
                            "modality_1": data1["modality"],
                            "modality_2": data2["modality"],
                            "timestamp_1": data1["timestamp"],
                            "timestamp_2": data2["timestamp"],
                        }
                        correlations.append(correlation)

                        # Store for future reference
                        self.cross_modal_correlations.append(correlation)

            await self.send(
                topic=content.get("reply_to"),
                content={
                    "message_type": "correlation_result",
                    "correlations": correlations,
                    "count": len(correlations),
                },
                correlation_id=message.correlation_id,
            )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Correlation analysis failed: {e}", exc_info=True)
            await self._send_error_response(message, f"Correlation failed: {e}")


    # =========================================================================
    # Session 44: Collective Learning Integration Methods
    # =========================================================================

    async def _emit_pattern(self, item_id: str, item_type: str, outcome: str, content: Dict[str, Any]) -> None:
        """Emit pattern for collective learning."""
        if not self.pattern_extractor:
            return
        
        if item_id in self._pattern_emitted:
            return
        
        try:
            await self.pattern_extractor.analyze_message(
                message_id=f"{item_type}_{item_id}",
                sender=self.agent_id,
                recipient="broadcast",
                message_type=f"{item_type}_completion",
                content=content,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            
            self._pattern_emitted.add(item_id)
            logger.info(f"{item_type}_pattern_emitted", item_id=item_id, outcome=outcome)
        except Exception as e:
            logger.warning("failed_to_emit_pattern", item_id=item_id, error=str(e))

    async def _consume_patterns(self, pattern_types: Optional[List[PatternType]] = None) -> List[Dict[str, Any]]:
        """Consume patterns from collective learning."""
        if not self.pattern_extractor:
            return []
        
        try:
            patterns = await self.pattern_extractor.extract_patterns(
                time_window_hours=24,
                pattern_types=pattern_types or [PatternType.SUCCESS, PatternType.DECISION],
            )
            return [p.to_dict() for p in patterns if p.metadata.confidence >= 0.7]
        except Exception as e:
            logger.warning("failed_to_consume_patterns", error=str(e))
            return []

    # =========================================================================
    # Session 44: Consensus Deliberation Integration Methods
    # =========================================================================

    async def _initiate_deliberation(
        self,
        item_id: str,
        proposal: str,
        participating_agents: List[str],
        domain: str = "general",
    ) -> Optional[str]:
        """Initiate swarm deliberation."""
        if not self.deliberation_engine:
            return None
        
        try:
            deliberation_id = f"delib_{item_id}"
            self.deliberation_engine.start_deliberation(
                deliberation_id=deliberation_id,
                proposal=proposal[:200],
                participants=participating_agents,
                domain=domain,
            )
            self._active_deliberations[item_id] = deliberation_id
            
            logger.info("deliberation_initiated", deliberation_id=deliberation_id, item_id=item_id)
            return deliberation_id
        except Exception as e:
            logger.error("failed_to_initiate_deliberation", item_id=item_id, error=str(e))
            return None

    async def _submit_deliberation_position(
        self,
        item_id: str,
        agent_id: str,
        position: Position,
        confidence: float,
        argument: str,
    ) -> bool:
        """Submit agent position in deliberation."""
        if not self.deliberation_engine:
            return False
        
        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return False
        
        try:
            success = self.deliberation_engine.submit_position(
                deliberation_id=deliberation_id,
                agent_id=agent_id,
                position=position,
                confidence=confidence,
                argument=argument,
            )
            
            if success and self.access_analyzer:
                self.access_analyzer.record_access(
                    memory_id=f"delib_{deliberation_id}_{agent_id}",
                    access_type="write",
                    agent_id=agent_id,
                )
            
            return success
        except Exception as e:
            logger.error("failed_to_submit_deliberation_position", error=str(e))
            return False

    async def _finalize_deliberation(self, item_id: str) -> Optional[Any]:
        """Finalize deliberation and apply result."""
        if not self.deliberation_engine:
            return None
        
        deliberation_id = self._active_deliberations.get(item_id)
        if not deliberation_id:
            return None
        
        try:
            result = self.deliberation_engine.finalize_deliberation(deliberation_id)
            
            if result:
                self.deliberation_engine.cleanup_deliberation(deliberation_id)
                del self._active_deliberations[item_id]
                logger.info("deliberation_finalized", deliberation_id=deliberation_id)
            
            return result
        except Exception as e:
            logger.error("failed_to_finalize_deliberation", error=str(e))
            return None

    # =========================================================================
    # Session 44: Memory Optimization Integration Methods
    # =========================================================================

    def _track_memory_access(self, item_id: str, item_type: str, access_type: str = "read") -> None:
        """Track memory access patterns."""
        if not self.access_analyzer:
            return
        
        memory_id = f"{item_type}_{item_id}"
        self.access_analyzer.record_access(
            memory_id=memory_id,
            access_type=access_type,
            agent_id=self.agent_id,
        )

    def _get_memory_tier(self, item_id: str, item_type: str) -> AccessTier:
        """Get memory tier classification."""
        if not self.access_analyzer:
            return AccessTier.COLD
        
        memory_id = f"{item_type}_{item_id}"
        profile = self.access_analyzer.get_profile(memory_id)
        return profile.tier if profile else AccessTier.COLD

    async def _prefetch_relevant(self, agent_id: str, item_type: str) -> List[str]:
        """Prefetch items an agent is likely to need."""
        if not self.access_analyzer:
            return []
        
        try:
            predicted_memories = self.access_analyzer.predict_agent_access(agent_id)
            return [
                mem.replace(f"{item_type}_", "")
                for mem in predicted_memories
                if mem.startswith(f"{item_type}_")
            ]
        except Exception as e:
            logger.warning("failed_to_prefetch", agent_id=agent_id, error=str(e))
            return []

    def get_learning_status(self) -> Dict[str, Any]:
        """Get collective learning and memory optimization status."""
        return {
            "agent_id": self.agent_id,
            "collective_learning": {
                "patterns_extracted": len(self.pattern_extractor._validated_patterns) if self.pattern_extractor else 0,
                "message_cache_size": len(self.pattern_extractor._message_cache) if self.pattern_extractor else 0,
            },
            "consensus": {
                "active_deliberations": len(self._active_deliberations),
                "deliberation_engine_stats": self.deliberation_engine.get_statistics() if self.deliberation_engine else {},
            },
            "memory_optimization": {
                "access_statistics": self.access_analyzer.get_statistics().to_dict() if self.access_analyzer else {},
            },
        }


    async def _send_error_response(self, message: ActorMessage, error: str) -> None:
        """Send error response."""
        if message.content.get("reply_to"):
            await self.send(
                topic=message.content["reply_to"],
                content={
                    "message_type": "error_response",
                    "error": error,
                    "original_message_type": message.message_type,
                },
                correlation_id=message.correlation_id,
            )
