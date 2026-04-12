"""Document processor stub for RAG pipeline compatibility."""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class DocumentType(Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    TEXT = "text"
    JSON = "json"


class ChunkStrategy(Enum):
    FIXED = "fixed"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"


@dataclass
class ProcessingConfig:
    chunk_size: int = 512
    chunk_overlap: int = 50
    strategy: ChunkStrategy = ChunkStrategy.FIXED
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessedDocument:
    id: str
    content: str
    chunks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    document_type: DocumentType = DocumentType.TEXT


class DocumentProcessor:
    """Document processing and chunking."""

    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()

    def detect_type(self, filename: str) -> DocumentType:
        """Detect document type from filename."""
        if filename.endswith((".md", ".markdown")):
            return DocumentType.MARKDOWN
        elif filename.endswith(".pdf"):
            return DocumentType.PDF
        elif filename.endswith((".html", ".htm")):
            return DocumentType.HTML
        elif filename.endswith(".json"):
            return DocumentType.JSON
        return DocumentType.TEXT

    def process(self, content: str, doc_type: DocumentType = DocumentType.TEXT) -> ProcessedDocument:
        """Process document into chunks."""
        chunks = self._chunk(content)
        return ProcessedDocument(
            id="doc_001",
            content=content,
            chunks=chunks,
            document_type=doc_type
        )

    def _chunk(self, content: str) -> List[str]:
        """Split content into chunks."""
        if self.config.strategy == ChunkStrategy.FIXED:
            return self._fixed_chunk(content)
        return [content]

    def _fixed_chunk(self, content: str) -> List[str]:
        """Fixed-size chunking."""
        chunks = []
        for i in range(0, len(content), self.config.chunk_size - self.config.chunk_overlap):
            chunk = content[i:i + self.config.chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks if chunks else [content]
