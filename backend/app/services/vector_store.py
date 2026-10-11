"""
Persistent vector index using fastembed and NumPy for dense semantic search.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.config import settings
from app.services.chunker import TranscriptChunk

logger = logging.getLogger("lenny.vector_store")


class VectorStore:
    """
    In-memory vector store with disk persistence, supporting cosine similarity queries.
    """

    def __init__(self, storage_dir: Optional[Path] = None, model_name: Optional[str] = None) -> None:
        self.storage_dir = storage_dir or settings.indices_dir
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None

        self.chunks: List[TranscriptChunk] = []
        self.embeddings: Optional[np.ndarray] = None  # (N, D) float32 normalized

    def _get_model(self):
        """Lazy load the fastembed TextEmbedding model."""
        if self._model is None:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def is_available(self) -> bool:
        """Check if index contains loaded chunks and embeddings."""
        return self.embeddings is not None and len(self.chunks) > 0 and len(self.chunks) == self.embeddings.shape[0]

    def build_index(self, chunks: List[TranscriptChunk], batch_size: int = 128) -> int:
        """
        Embed all chunks and store normalized vectors in memory.
        """
        if not chunks:
            self.chunks = []
            self.embeddings = None
            return 0

        self.chunks = chunks
        texts = [c.text for c in chunks]

        model = self._get_model()
        all_embeddings: List[np.ndarray] = []
        total = len(chunks)
        print(f"[VectorStore] Generating dense embeddings for {total} chunks (batch_size={batch_size})...")

        # Stream embeddings from fastembed generator
        for i, emb in enumerate(model.embed(texts, batch_size=batch_size)):
            all_embeddings.append(emb)
            if (i + 1) % 5000 == 0 or (i + 1) == total:
                print(f"[VectorStore] Embedded {i + 1}/{total} chunks ({((i + 1) / total) * 100:.1f}%)")

        mat = np.array(all_embeddings, dtype=np.float32)
        # L2-normalize vectors for fast cosine similarity via dot product
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        self.embeddings = mat / norms

        print(f"[VectorStore] Index built successfully with shape {self.embeddings.shape}.")
        return len(self.chunks)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[TranscriptChunk, float]]:
        """
        Compute cosine similarity between query and all stored chunk embeddings.
        Returns sorted list of (chunk, cosine_similarity).
        """
        if not self.is_available() or not query.strip():
            return []

        model = self._get_model()
        query_emb_gen = model.embed([query])
        query_vec = next(iter(query_emb_gen)).astype(np.float32)

        # Normalize query vector
        norm = np.linalg.norm(query_vec)
        if norm > 0:
            query_vec = query_vec / norm

        # Dot product with all normalized vectors
        scores = np.dot(self.embeddings, query_vec)

        # Top K indices
        if len(scores) <= top_k:
            top_indices = np.argsort(-scores)
        else:
            top_indices = np.argpartition(-scores, top_k)[:top_k]
            top_indices = top_indices[np.argsort(-scores[top_indices])]

        results: List[Tuple[TranscriptChunk, float]] = []
        for idx in top_indices:
            score = float(scores[idx])
            results.append((self.chunks[idx], score))

        return results

    def save(self) -> None:
        """Persist embeddings matrix and chunk metadata to disk."""
        if not self.is_available():
            return

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        emb_path = self.storage_dir / "embeddings.npy"
        chunks_path = self.storage_dir / "chunks.json"

        # Save numpy matrix
        np.save(str(emb_path), self.embeddings)

        # Save chunk metadata
        chunk_dicts = []
        for c in self.chunks:
            chunk_dicts.append({
                "chunk_id": c.chunk_id,
                "episode_slug": c.episode_slug,
                "episode_title": c.episode_title,
                "guest": c.guest,
                "speaker": c.speaker,
                "start_timestamp": c.start_timestamp,
                "start_seconds": c.start_seconds,
                "end_timestamp": c.end_timestamp,
                "end_seconds": c.end_seconds,
                "timestamp_url": c.timestamp_url,
                "source_file": c.source_file,
                "text": c.text,
                "word_count": c.word_count,
                "char_count": c.char_count,
                "topic_tags": c.topic_tags,
            })

        chunks_path.write_text(json.dumps(chunk_dicts, ensure_ascii=False), encoding="utf-8")

    def load(self) -> bool:
        """Load persistent index from disk if present."""
        emb_path = self.storage_dir / "embeddings.npy"
        chunks_path = self.storage_dir / "chunks.json"

        if not emb_path.exists() or not chunks_path.exists():
            return False

        try:
            self.embeddings = np.load(str(emb_path))
            raw_data = json.loads(chunks_path.read_text(encoding="utf-8"))

            self.chunks = [
                TranscriptChunk(
                    chunk_id=d["chunk_id"],
                    episode_slug=d["episode_slug"],
                    episode_title=d["episode_title"],
                    guest=d["guest"],
                    speaker=d["speaker"],
                    start_timestamp=d["start_timestamp"],
                    start_seconds=d["start_seconds"],
                    end_timestamp=d["end_timestamp"],
                    end_seconds=d["end_seconds"],
                    timestamp_url=d.get("timestamp_url"),
                    source_file=d["source_file"],
                    text=d["text"],
                    word_count=d["word_count"],
                    char_count=d["char_count"],
                    topic_tags=d.get("topic_tags", []),
                )
                for d in raw_data
            ]
            return self.is_available()
        except Exception:
            self.chunks = []
            self.embeddings = None
            return False
