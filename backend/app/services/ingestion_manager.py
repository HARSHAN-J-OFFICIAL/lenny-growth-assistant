"""
Central Ingestion Manager coordinating incremental transcript discovery, indexing, and persistence.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.schemas.knowledge import KnowledgeStatusResponse
from app.services.chunker import TranscriptChunk, TranscriptChunker
from app.services.hybrid_retriever import HybridRetriever
from app.services.lexical_store import LexicalStore
from app.services.topic_index_parser import TopicIndexRegistry
from app.services.transcript_parser import parse_transcript_file
from app.services.vector_store import VectorStore

logger = logging.getLogger("lenny.ingestion")


class IngestionManager:
    """
    Coordinates transcript ingestion, incremental change detection, index building, and search serving.
    """

    def __init__(
        self,
        transcripts_dir: Optional[Path] = None,
        indices_dir: Optional[Path] = None,
    ) -> None:
        self.transcripts_dir = transcripts_dir or settings.transcripts_dir
        self.indices_dir = indices_dir or settings.indices_dir

        self.topic_registry = TopicIndexRegistry()
        self.chunker = TranscriptChunker(
            target_words=settings.CHUNK_TARGET_WORDS,
            overlap_words=settings.CHUNK_OVERLAP_WORDS,
        )
        self.vector_store = VectorStore(
            storage_dir=self.indices_dir,
            model_name=settings.EMBEDDING_MODEL_NAME,
        )
        self.lexical_store = LexicalStore()
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            lexical_store=self.lexical_store,
            topic_registry=self.topic_registry,
            rrf_k=settings.RRF_K,
            evidence_threshold=settings.EVIDENCE_THRESHOLD,
        )

        self.state: str = "unindexed"
        self.last_indexed_at: Optional[datetime] = None
        self.file_hashes: Dict[str, str] = {}
        self.warnings: List[str] = []

    def initialize(self) -> bool:
        """
        Attempt to load existing persistent index from disk.
        Returns True if persistent index was successfully loaded.
        """
        # Load topic index taxonomy
        topic_dir = self.transcripts_dir / "index"
        if topic_dir.exists():
            self.topic_registry.load_from_directory(topic_dir)

        # Attempt to load persistent vector store
        if self.vector_store.load():
            # Build BM25 in memory from loaded chunks (fast, < 0.2s)
            self.lexical_store.build_index(self.vector_store.chunks)
            self.state = "ready"
            self._load_manifest()
            return True

        self.state = "unindexed"
        return False

    def ingest_dataset(
        self,
        max_episodes: Optional[int] = None,
        force_rebuild: bool = False,
    ) -> Dict[str, Any]:
        """
        Scan data/transcripts/, extract metadata, chunk dialogue, and build hybrid indices.
        If max_episodes is provided, limits ingestion (useful for quick integration tests).
        """
        start_time = time.perf_counter()
        self.state = "indexing"
        self.warnings.clear()

        # 1. Load topic index taxonomy
        topic_dir = self.transcripts_dir / "index"
        topic_count = 0
        if topic_dir.exists():
            topic_count = self.topic_registry.load_from_directory(topic_dir)
        else:
            self.warnings.append(f"Topic index directory not found at {topic_dir}")

        # 2. Discover transcript files
        episodes_dir = self.transcripts_dir / "episodes"
        if not episodes_dir.exists():
            self.state = "error"
            msg = f"Episodes directory not found at {episodes_dir}. Run 'python scripts/download_transcripts.py' to acquire the corpus from https://github.com/ChatPRD/lennys-podcast-transcripts."
            self.warnings.append(msg)
            return {"status": "error", "message": msg}

        transcript_files = sorted(episodes_dir.glob("*/transcript.md"))
        if max_episodes is not None and max_episodes > 0:
            transcript_files = transcript_files[:max_episodes]

        all_chunks: List[TranscriptChunk] = []
        indexed_episodes = 0
        new_file_hashes: Dict[str, str] = {}

        for t_file in transcript_files:
            parsed = parse_transcript_file(t_file)
            if not parsed or not parsed.turns:
                continue

            slug = parsed.metadata.slug
            new_file_hashes[slug] = parsed.metadata.content_hash

            topic_tags = self.topic_registry.get_topics_for_episode(slug)
            chunks = self.chunker.chunk_transcript(parsed, topic_tags=topic_tags)
            all_chunks.extend(chunks)
            indexed_episodes += 1

        if not all_chunks:
            self.state = "unindexed"
            self.warnings.append("No valid transcript chunks extracted from discovered files")
            return {"status": "empty", "indexed_episodes": 0, "indexed_chunks": 0}

        # 3. Build Vector and Lexical Stores
        self.vector_store.build_index(all_chunks)
        self.lexical_store.build_index(all_chunks)

        # 4. Save persistent artifacts
        self.vector_store.save()
        self.file_hashes = new_file_hashes
        self.last_indexed_at = datetime.now(timezone.utc)
        self.state = "ready"
        self._save_manifest()

        duration_sec = round(time.perf_counter() - start_time, 2)
        return {
            "status": "success",
            "indexed_episodes": indexed_episodes,
            "indexed_chunks": len(all_chunks),
            "indexed_topics": topic_count,
            "duration_sec": duration_sec,
            "storage_dir": str(self.indices_dir),
        }

    def get_status(self) -> KnowledgeStatusResponse:
        """Return the current operational status of the knowledge base."""
        # Calculate index storage size on disk
        storage_bytes = 0
        if self.indices_dir.exists():
            for f in self.indices_dir.iterdir():
                if f.is_file():
                    storage_bytes += f.stat().st_size

        return KnowledgeStatusResponse(
            ingestion_state=self.state,
            indexed_episodes_count=len({c.episode_slug for c in self.vector_store.chunks}),
            indexed_chunks_count=len(self.vector_store.chunks),
            indexed_topics_count=len(self.topic_registry.topics),
            last_indexed_at=self.last_indexed_at,
            embedding_model=settings.EMBEDDING_MODEL_NAME,
            vector_dim=384,
            index_storage_bytes=storage_bytes,
            warnings=list(self.warnings),
        )

    def _save_manifest(self) -> None:
        """Persist state manifest to indices storage directory."""
        self.indices_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.indices_dir / "manifest.json"
        data = {
            "indexed_episodes_count": len({c.episode_slug for c in self.vector_store.chunks}),
            "indexed_chunks_count": len(self.vector_store.chunks),
            "last_indexed_at": self.last_indexed_at.isoformat() if self.last_indexed_at else None,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "file_hashes": self.file_hashes,
        }
        manifest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_manifest(self) -> None:
        """Load state manifest from disk if present."""
        manifest_path = self.indices_dir / "manifest.json"
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.file_hashes = data.get("file_hashes", {})
                if data.get("last_indexed_at"):
                    self.last_indexed_at = datetime.fromisoformat(data["last_indexed_at"])
            except Exception:
                pass


# Global singleton instance for application injection
ingestion_manager = IngestionManager()
