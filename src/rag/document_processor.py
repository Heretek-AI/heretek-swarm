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

logger = structlog.get_logger(__name__)


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
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
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
    
    def detect_type(self, file_path: Union[str, Path]) -> DocumentType:
        """Detect document type from file extension."""
        ext = Path(file_path).suffix.lower()
        return self._supported_extensions.get(ext, DocumentType.UNKNOWN)
    
    def generate_id(self, content: str, source: str) -> str:
        """Generate unique ID for document or chunk."""
        hash_input = f"{source}:{content[:100]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    async def process_file(
        self,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessedDocument:
        """
        Process a file and return chunked document.
        
        Args:
            file_path: Path to the file
            metadata: Optional metadata to attach
            
        Returns:
            ProcessedDocument with chunks
        """
        import time
        start_time = time.time()
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB > {self.config.max_file_size_mb}MB"
            )
        
        # Detect type and load content
        doc_type = self.detect_type(path)
        content = await self._load_file(path, doc_type)
        
        # Process content
        processed = await self.process_content(
            content=content,
            source_path=str(path),
            doc_type=doc_type,
            metadata=metadata,
        )
        
        # Add processing time
        processed.processing_time_ms = (time.time() - start_time) * 1000
        
        return processed
    
    async def process_content(
        self,
        content: str,
        source_path: str,
        doc_type: DocumentType = DocumentType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessedDocument:
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
        start_time = time.time()
        
        # Clean content based on type
        cleaned = self._clean_content(content, doc_type)
        
        # Extract metadata if enabled
        doc_metadata = metadata or {}
        if self.config.extract_metadata:
            doc_metadata.update(self._extract_metadata(cleaned, doc_type))
        
        # Generate document ID
        doc_id = self.generate_id(cleaned, source_path)
        
        # Chunk the content
        chunks = self._chunk_content(
            content=cleaned,
            document_id=doc_id,
            source_path=source_path,
            doc_type=doc_type,
        )
        
        # Limit chunks
        if len(chunks) > self.config.max_chunks_per_document:
            logger.warning(
                "chunks_limited",
                source=source_path,
                original=len(chunks),
                limit=self.config.max_chunks_per_document,
            )
            chunks = chunks[:self.config.max_chunks_per_document]
        
        # Calculate statistics
        total_chars = len(cleaned)
        total_lines = cleaned.count("\n") + 1
        
        return ProcessedDocument(
            id=doc_id,
            source_path=source_path,
            source_type=doc_type,
            chunks=chunks,
            title=doc_metadata.get("title"),
            author=doc_metadata.get("author"),
            total_characters=total_chars,
            total_lines=total_lines,
            total_chunks=len(chunks),
            processing_time_ms=(time.time() - start_time) * 1000,
            chunk_strategy=self.config.chunk_strategy,
        )
    
    async def _load_file(self, path: Path, doc_type: DocumentType) -> str:
        """Load file content based on type."""
        if doc_type == DocumentType.PDF:
            # PDF requires special handling
            try:
                import pypdf
                reader = pypdf.PdfReader(str(path))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            except ImportError:
                logger.warning("pypdf not installed, cannot process PDF")
                raise ImportError("Install pypdf to process PDF files")
        
        # Default text loading
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    
    def _clean_content(self, content: str, doc_type: DocumentType) -> str:
        """Clean and normalize content."""
        # HTML cleaning
        if doc_type == DocumentType.HTML and self.config.clean_html:
            content = self._strip_html(content)
        
        # Whitespace normalization
        if self.config.normalize_whitespace:
            content = self._normalize_whitespace(content)
        
        # URL removal
        if self.config.remove_urls:
            content = self._remove_urls(content)
        
        return content.strip()
    
    def _strip_html(self, content: str) -> str:
        """Strip HTML tags and extract text."""
        # Simple regex-based HTML stripping
        # For production, consider using BeautifulSoup
        content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
        content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
        content = re.sub(r"<[^>]+>", " ", content)
        content = re.sub(r"&nbsp;", " ", content)
        content = re.sub(r"&[a-z]+;", "", content)
        return content
    
    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in content."""
        # Replace multiple spaces with single space
        content = re.sub(r"[ \t]+", " ", content)
        # Replace multiple newlines with double newline
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content
    
    def _remove_urls(self, content: str) -> str:
        """Remove URLs from content."""
        url_pattern = r"https?://[^\s]+"
        return re.sub(url_pattern, "", content)
    
    def _extract_metadata(
        self,
        content: str,
        doc_type: DocumentType,
    ) -> Dict[str, Any]:
        """Extract metadata from content."""
        metadata = {}
        
        # Extract title from first line or heading
        lines = content.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            # Markdown heading
            if first_line.startswith("#"):
                metadata["title"] = first_line.lstrip("# ").strip()
            elif len(first_line) < 100:
                metadata["title"] = first_line
        
        # Extract keywords if enabled
        if self.config.extract_keywords:
            metadata["keywords"] = self._extract_keywords(content)
        
        return metadata
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content using simple frequency analysis."""
        # Simple keyword extraction based on word frequency
        # For production, consider using KeyBERT or similar
        words = re.findall(r"\b[a-zA-Z]{4,}\b", content.lower())
        
        # Filter common words
        stop_words = {
            "this", "that", "these", "those", "with", "from", "have",
            "been", "were", "they", "their", "what", "when", "where",
            "which", "while", "about", "would", "could", "should",
        }
        words = [w for w in words if w not in stop_words]
        
        # Count frequency
        from collections import Counter
        word_counts = Counter(words)
        
        # Return top keywords
        return [w for w, _ in word_counts.most_common(self.config.keyword_count)]
    
    def _chunk_content(
        self,
        content: str,
        document_id: str,
        source_path: str,
        doc_type: DocumentType,
    ) -> List[DocumentChunk]:
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
    
    def _chunk_recursive(
        self,
        content: str,
        document_id: str,
        source_path: str,
        doc_type: DocumentType,
    ) -> List[DocumentChunk]:
        """
        Recursively chunk content by paragraphs, then sentences.
        
        Pattern stolen from LangChain's RecursiveCharacterTextSplitter.
        """
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split("\n\n")
        
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for para in paragraphs:
            # If paragraph alone exceeds chunk size, split by sentences
            if len(para) > self.config.chunk_size:
                sentences = self._split_sentences(para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > self.config.chunk_size:
                        if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
                            chunk = self._create_chunk(
                                content=current_chunk.strip(),
                                document_id=document_id,
                                source_path=source_path,
                                doc_type=doc_type,
                                chunk_index=chunk_index,
                                start_char=current_start,
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                        
                        # Start new chunk with overlap
                        if self.config.chunk_overlap > 0 and current_chunk:
                            overlap_text = current_chunk[-self.config.chunk_overlap:]
                            current_chunk = overlap_text + " " + sentence
                        else:
                            current_chunk = sentence
                        current_start = current_start + len(current_chunk) - len(sentence)
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                # Check if adding paragraph exceeds chunk size
                if len(current_chunk) + len(para) + 2 > self.config.chunk_size:
                    if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
                        chunk = self._create_chunk(
                            content=current_chunk.strip(),
                            document_id=document_id,
                            source_path=source_path,
                            doc_type=doc_type,
                            chunk_index=chunk_index,
                            start_char=current_start,
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                    
                    # Start new chunk with overlap
                    if self.config.chunk_overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-self.config.chunk_overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para
                    current_start = current_start + len(current_chunk) - len(para)
                else:
                    current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                document_id=document_id,
                source_path=source_path,
                doc_type=doc_type,
                chunk_index=chunk_index,
                start_char=current_start,
            )
            chunks.append(chunk)
        
        # Update total chunks count
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total
        
        return chunks
    
    def _chunk_fixed_size(
        self,
        content: str,
        document_id: str,
        source_path: str,
        doc_type: DocumentType,
    ) -> List[DocumentChunk]:
        """Chunk content by fixed character size."""
        chunks = []
        
        for i in range(0, len(content), self.config.chunk_size - self.config.chunk_overlap):
            chunk_content = content[i:i + self.config.chunk_size]
            
            if len(chunk_content) >= self.config.min_chunk_size:
                chunk = self._create_chunk(
                    content=chunk_content,
                    document_id=document_id,
                    source_path=source_path,
                    doc_type=doc_type,
                    chunk_index=len(chunks),
                    start_char=i,
                )
                chunks.append(chunk)
        
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total
        
        return chunks
    
    def _chunk_by_sentence(
        self,
        content: str,
        document_id: str,
        source_path: str,
        doc_type: DocumentType,
    ) -> List[DocumentChunk]:
        """Chunk content by sentence boundaries."""
        chunks = []
        sentences = self._split_sentences(content)
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > self.config.chunk_size:
                if current_chunk:
                    chunk = self._create_chunk(
                        content=current_chunk.strip(),
                        document_id=document_id,
                        source_path=source_path,
                        doc_type=doc_type,
                        chunk_index=chunk_index,
                        start_char=0,
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                document_id=document_id,
                source_path=source_path,
                doc_type=doc_type,
                chunk_index=chunk_index,
                start_char=0,
            )
            chunks.append(chunk)
        
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        # For production, consider using spaCy or nltk
        sentence_endings = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_chunk(
        self,
        content: str,
        document_id: str,
        source_path: str,
        doc_type: DocumentType,
        chunk_index: int,
        start_char: int,
    ) -> DocumentChunk:
        """Create a document chunk."""
        chunk_id = self.generate_id(content, f"{document_id}:{chunk_index}")
        
        return DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            total_chunks=0,  # Updated later
            source_path=source_path,
            source_type=doc_type,
            start_char=start_char,
            end_char=start_char + len(content),
            metadata={
                "char_count": len(content),
                "word_count": len(content.split()),
            },
        )
