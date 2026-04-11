"""
Document Processor - RAG Document Ingestion System.

Handles document ingestion, chunking, and preparation for vector storage.
Pattern stolen from elizaOS/packages/core/advanced_capabilities/document-ingestion

Features:
- Multiple chunking strategies (recursive, semantic, fixed)
- Metadata extraction
- Content cleaning and normalization
- Support for multiple file formats
"""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog

_logger = structlog.get_logger(__name__)


class ChunkStrategy(Enum):
    """Chunking strategies for document processing."""
    RECURSIVE = "recursive"  # Split by paragraphs, then sentences
    FIXED_SIZE = "fixed_size"  # Fixed character count
    SEMANTIC = "semantic"  # AI-based semantic chunking
    SENTENCE = "sentence"  # Split by sentence boundaries


class DocumentType(Enum):
    """Supported document types."""
    TEXT = "text/plain"
    MARKDOWN = "text/markdown"
    HTML = "text/html"
    CODE = "text/x-code"
    JSON = "application/json"
    CSV = "text/csv"
    PDF = "application/pdf"  # Requires additional processing
    UNKNOWN = "application/octet-stream"


@dataclass
class ProcessingConfig:
    """Configuration for document processing."""

    # Chunking settings
    chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE
    chunk_size: int = 1000  # Target characters per chunk
    chunk_overlap: int = 200  # Overlap between chunks

    # Content processing
    clean_html: bool = True
    normalize_whitespace: bool = True
    remove_urls: bool = False
    min_chunk_size: int = 100  # Minimum characters for a chunk

    # Metadata extraction
    extract_metadata: bool = True
    extract_keywords: bool = False
    keyword_count: int = 10  # Increased to capture more relevant keywords

    # Processing limits
    max_file_size_mb: int = 50
    max_chunks_per_document: int = 1000


@dataclass
class DocumentChunk:
    """A processed chunk of a document."""

    id: str
    document_id: str
    content: str
    chunk_index: int
    total_chunks: int

    # Source information
    source_path: Optional[str] = None
    source_type: DocumentType = DocumentType.TEXT

    # Position information
    start_char: int = 0
    end_char: int = 0
    start_line: Optional[int] = None
    end_line: Optional[int] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "source_path": self.source_path,
            "source_type": self.source_type.value,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "metadata": self.metadata,
            "keywords": self.keywords,
            "created_at": self.created_at,
        }


@dataclass
class ProcessedDocument:
    """Result of processing a document."""

    id: str
    source_path: str
    source_type: DocumentType
    chunks: List[DocumentChunk]

    # Document metadata
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Statistics
    total_characters: int = 0
    total_lines: int = 0
    total_chunks: int = 0

    # Processing metadata
    processing_time_ms: float = 0.0
    chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_path": self.source_path,
            "source_type": self.source_type.value,
            "chunks": [c.to_dict() for c in self.chunks],
            "title": self.title,
            "author": self.author,
            "created_at": self.created_at,
            "total_characters": self.total_characters,
            "total_lines": self.total_lines,
            "total_chunks": self.total_chunks,
            "processing_time_ms": self.processing_time_ms,
            "chunk_strategy": self.chunk_strategy.value,
        }


class DocumentProcessor:
    """
    Document processor for RAG ingestion.
    
    Handles:
    - File loading and content extraction
    - Text cleaning and normalization
    - Chunking with configurable strategies
    - Metadata extraction
    - Integration with vector storage
    
    Pattern stolen from elizaOS document-ingestion plugin.
    """

    def __init__(self, _config: Optional[ProcessingConfig]):
        self.config = config or ProcessingConfig()
        self._supported_extensions = {
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.MARKDOWN,
            ".markdown": DocumentType.MARKDOWN,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML,
            ".json": DocumentType.JSON,
            ".csv": DocumentType.CSV,
            ".py": DocumentType.CODE,
            ".js": DocumentType.CODE,
            ".ts": DocumentType.CODE,
            ".java": DocumentType.CODE,
            ".go": DocumentType.CODE,
            ".rs": DocumentType.CODE,
            ".c": DocumentType.CODE,
            ".cpp": DocumentType.CODE,
            ".h": DocumentType.CODE,
            ".sh": DocumentType.CODE,
            ".yaml": DocumentType.TEXT,
            ".yml": DocumentType.TEXT,
            ".xml": DocumentType.TEXT,
            ".pdf": DocumentType.PDF,
        }

    def detect_type(self, _file_path: Union[str, _Path]) -> DocumentType:
        """Detect document type from file extension."""
        ext = Path(file_path).suffix.lower()
        return self._supported_extensions.get(ext, DocumentType.UNKNOWN)

    def generate_id(self, _content: str, _source: str) -> str:
        """Generate unique ID for document or chunk."""
        _hash_input = f"{source}:{content[:100]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    async def process_file(self, _file_path: Union[str, _Path], _metadata: Optional[Dict[str, _Any]]) -> ProcessedDocument:
        """
        Process a file and return chunked document.
        
        Args:
            file_path: Path to the file
            metadata: Optional metadata to attach
            
        Returns:
            ProcessedDocument with chunks
        """
        import time
        _start_time = time.time()

        _path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file size
        _file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB > {self.config.max_file_size_mb}MB"
            )

        # Detect type and load content
        _doc_type = self.detect_type(path)
        _content = await self._load_file(path, doc_type)

        # Process content
        _processed = await self.process_content(
            _content = content,
            _source_path = str(path),
            _doc_type = doc_type,
            _metadata = metadata,
        )

        # Add processing time
        processed.processing_time_ms = (time.time() - start_time) * 1000

        return processed

    async def process_content(self, _content: str, _source_path: str, _doc_type: DocumentType, _metadata: Optional[Dict[str, _Any]]) -> ProcessedDocument:
        """
        Process raw content and return chunked document.
        
        Args:
            content: Raw text content
            source_path: Source identifier (path or URL)
            doc_type: Document type
            metadata: Optional metadata
            
        Returns:
            ProcessedDocument with chunks
        """
        import time
        _start_time = time.time()

        # Clean content based on type
        _cleaned = self._clean_content(content, doc_type)

        # Extract metadata if enabled
        _doc_metadata = metadata or {}
        if self.config.extract_metadata:
            doc_metadata.update(self._extract_metadata(cleaned, doc_type))

        # Generate document ID
        _doc_id = self.generate_id(cleaned, source_path)

        # Chunk the content
        _chunks = self._chunk_content(
            _content = cleaned,
            _document_id = doc_id,
            _source_path = source_path,
            _doc_type = doc_type,
        )

        # Limit chunks
        if len(chunks) > self.config.max_chunks_per_document:
            logger.warning(
                "chunks_limited",
                _source = source_path,
                _original = len(chunks),
                _limit = self.config.max_chunks_per_document,
            )
            _chunks = chunks[:self.config.max_chunks_per_document]

        # Calculate statistics
        _total_chars = len(cleaned)
        _total_lines = cleaned.count("\n") + 1

        return ProcessedDocument(
            _id = doc_id,
            _source_path = source_path,
            _source_type = doc_type,
            _chunks = chunks,
            _title = doc_metadata.get("title"),
            _author = doc_metadata.get("author"),
            _total_characters = total_chars,
            _total_lines = total_lines,
            total_chunks=len(chunks),
            _processing_time_ms = (time.time() - start_time) * 1000,
            chunk_strategy=self.config.chunk_strategy,
        )

    async def _load_file(self, _path: Path, _doc_type: DocumentType) -> str:
        """Load file content based on type."""
        if doc_type == DocumentType.PDF:
            # PDF requires special handling
            try:
                import pypdf
                _reader = pypdf.PdfReader(str(path))
                _text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                logger.warning("pypdf not installed, cannot process PDF")
                raise ImportError("Install pypdf to process PDF files")

        # Default text loading
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _clean_content(self, _content: str, _doc_type: DocumentType) -> str:
        """Clean and normalize content."""
        # HTML cleaning
        if doc_type == DocumentType.HTML and self.config.clean_html:
            _content = self._strip_html(content)

        # Whitespace normalization
        if self.config.normalize_whitespace:
            _content = self._normalize_whitespace(content)

        # URL removal
        if self.config.remove_urls:
            _content = self._remove_urls(content)

        return content.strip()

    def _strip_html(self, _content: str) -> str:
        """Strip HTML tags and extract text."""
        # Simple regex-based HTML stripping
        # For production, consider using BeautifulSoup
        _content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
        _content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
        _content = re.sub(r"<[^>]+>", " ", content)
        _content = re.sub(r"&nbsp;", " ", content)
        _content = re.sub(r"&[a-z]+;", "", content)
        return content

    def _normalize_whitespace(self, _content: str) -> str:
        """Normalize whitespace in content."""
        # Replace multiple spaces with single space
        _content = re.sub(r"[ \t]+", " ", content)
        # Replace multiple newlines with double newline
        _content = re.sub(r"\n{3,}", "\n\n", content)
        return content

    def _remove_urls(self, _content: str) -> str:
        """Remove URLs from content."""
        _url_pattern = r"https?://[^\s]+"
        return re.sub(url_pattern, "", content)

    def _extract_metadata(self, _content: str, _doc_type: DocumentType) -> Dict[str, Any]:
        """Extract metadata from content."""
        _metadata = {}

        # Extract title from first line or heading
        _lines = content.strip().split("\n")
        if lines:
            _first_line = lines[0].strip()
            # Markdown heading
            if first_line.startswith("#"):
                metadata["title"] = first_line.lstrip("# ").strip()
            elif len(first_line) < 100:
                metadata["title"] = first_line

        # Extract keywords if enabled
        if self.config.extract_keywords:
            metadata["keywords"] = self._extract_keywords(content)

        return metadata

    def _extract_keywords(self, _content: str) -> List[str]:
        """Extract keywords from content using simple frequency analysis."""
        # Simple keyword extraction based on word frequency
        # For production, consider using KeyBERT or similar
        _words = re.findall(r"\b[a-zA-Z]{4,}\b", content.lower())

        # Filter common words
        _stop_words = {
            "this", "that", "these", "those", "with", "from", "have",
            "been", "were", "they", "their", "what", "when", "where",
            "which", "while", "about", "would", "could", "should",
        }
        _words = [w for w in words if w not in stop_words]

        # Count frequency
        from collections import Counter
        _word_counts = Counter(words)

        # Return top keywords
        return [w for w, _ in word_counts.most_common(self.config.keyword_count)]

    def _chunk_content(self, _content: str, _document_id: str, _source_path: str, _doc_type: DocumentType) -> List[DocumentChunk]:
        """Chunk content using configured strategy."""
        if self.config.chunk_strategy == ChunkStrategy.RECURSIVE:
            return self._chunk_recursive(content, document_id, source_path, doc_type)
        elif self.config.chunk_strategy == ChunkStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(content, document_id, source_path, doc_type)
        elif self.config.chunk_strategy == ChunkStrategy.SENTENCE:
            return self._chunk_by_sentence(content, document_id, source_path, doc_type)
        else:
            # Default to recursive
            return self._chunk_recursive(content, document_id, source_path, doc_type)

    def _chunk_recursive(self, _content: str, _document_id: str, _source_path: str, _doc_type: DocumentType) -> List[DocumentChunk]:
        """
        Recursively chunk content by paragraphs, then sentences.
        
        Pattern stolen from LangChain's RecursiveCharacterTextSplitter.
        """
        _chunks = []

        # Split by paragraphs first
        _paragraphs = content.split("\n\n")

        _current_chunk = ""
        _current_start = 0
        _chunk_index = 0

        for para in paragraphs:
            # If paragraph alone exceeds chunk size, split by sentences
            if len(para) > self.config.chunk_size:
                _sentences = self._split_sentences(para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > self.config.chunk_size:
                        if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
                            _chunk = self._create_chunk(
                                _content = current_chunk.strip(),
                                _document_id = document_id,
                                _source_path = source_path,
                                _doc_type = doc_type,
                                _chunk_index = chunk_index,
                                _start_char = current_start,
                            )
                            chunks.append(chunk)
                            chunk_index += 1

                        # Start new chunk with overlap
                        if self.config.chunk_overlap > 0 and current_chunk:
                            _overlap_text = current_chunk[-self.config.chunk_overlap:]
                            _current_chunk = overlap_text + " " + sentence
                        else:
                            _current_chunk = sentence
                        _current_start = current_start + len(current_chunk) - len(sentence)
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                # Check if adding paragraph exceeds chunk size
                if len(current_chunk) + len(para) + 2 > self.config.chunk_size:
                    if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
                        _chunk = self._create_chunk(
                            _content = current_chunk.strip(),
                            _document_id = document_id,
                            _source_path = source_path,
                            _doc_type = doc_type,
                            _chunk_index = chunk_index,
                            _start_char = current_start,
                        )
                        chunks.append(chunk)
                        chunk_index += 1

                    # Start new chunk with overlap
                    if self.config.chunk_overlap > 0 and current_chunk:
                        _overlap_text = current_chunk[-self.config.chunk_overlap:]
                        _current_chunk = overlap_text + "\n\n" + para
                    else:
                        _current_chunk = para
                    _current_start = current_start + len(current_chunk) - len(para)
                else:
                    current_chunk += "\n\n" + para if current_chunk else para

        # Add final chunk
        if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
            _chunk = self._create_chunk(
                _content = current_chunk.strip(),
                _document_id = document_id,
                _source_path = source_path,
                _doc_type = doc_type,
                _chunk_index = chunk_index,
                _start_char = current_start,
            )
            chunks.append(chunk)

        # Update total chunks count
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def _chunk_fixed_size(self, _content: str, _document_id: str, _source_path: str, _doc_type: DocumentType) -> List[DocumentChunk]:
        """Chunk content by fixed character size."""
        _chunks = []

        for i in range(0, len(content), self.config.chunk_size - self.config.chunk_overlap):
            _chunk_content = content[i:i + self.config.chunk_size]

            if len(chunk_content) >= self.config.min_chunk_size:
                _chunk = self._create_chunk(
                    _content = chunk_content,
                    _document_id = document_id,
                    _source_path = source_path,
                    _doc_type = doc_type,
                    _chunk_index = len(chunks),
                    _start_char = i,
                )
                chunks.append(chunk)

        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def _chunk_by_sentence(self, _content: str, _document_id: str, _source_path: str, _doc_type: DocumentType) -> List[DocumentChunk]:
        """Chunk content by sentence boundaries."""
        _chunks = []
        _sentences = self._split_sentences(content)

        _current_chunk = ""
        _chunk_index = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.config.chunk_size:
                if current_chunk:
                    _chunk = self._create_chunk(
                        _content = current_chunk.strip(),
                        _document_id = document_id,
                        _source_path = source_path,
                        _doc_type = doc_type,
                        _chunk_index = chunk_index,
                        _start_char = 0,
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                _current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk:
            _chunk = self._create_chunk(
                _content = current_chunk.strip(),
                _document_id = document_id,
                _source_path = source_path,
                _doc_type = doc_type,
                _chunk_index = chunk_index,
                _start_char = 0,
            )
            chunks.append(chunk)

        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def _split_sentences(self, _text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        # For production, consider using spaCy or nltk
        _sentence_endings = r"(?<=[.!?])\s+"
        _sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def _create_chunk(self, _content: str, _document_id: str, _source_path: str, _doc_type: DocumentType, _chunk_index: int, _start_char: int) -> DocumentChunk:
        """Create a document chunk."""
        _chunk_id = self.generate_id(content, f"{document_id}:{chunk_index}")

        return DocumentChunk(
            _id = chunk_id,
            _document_id = document_id,
            _content = content,
            _chunk_index = chunk_index,
            _total_chunks = 0,  # Updated later
            _source_path = source_path,
            _source_type = doc_type,
            _start_char = start_char,
            _end_char = start_char + len(content),
            _metadata = {
                "char_count": len(content),
                "word_count": len(content.split()),
            },
        )
