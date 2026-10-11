"""
Lexical search index using BM25Okapi for precise keyword and entity retrieval.
"""

import re
from typing import List, Optional, Tuple
from rank_bm25 import BM25Okapi

from app.services.chunker import TranscriptChunk

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_\-\.\']+")


def tokenize_text(text: str) -> List[str]:
    """Tokenize and lowercase text for BM25 lexical indexing."""
    return [token.lower() for token in TOKEN_PATTERN.findall(text) if len(token) > 1]


class LexicalStore:
    """
    BM25Okapi inverted index for keyword and exact terminology search.
    """

    def __init__(self) -> None:
        self.chunks: List[TranscriptChunk] = []
        self._bm25: Optional[BM25Okapi] = None
        self._tokenized_corpus: List[List[str]] = []

    def is_available(self) -> bool:
        """Check if BM25 index is populated."""
        return self._bm25 is not None and len(self.chunks) > 0

    def build_index(self, chunks: List[TranscriptChunk]) -> int:
        """
        Build the BM25 index from a collection of chunks.
        """
        if not chunks:
            self.chunks = []
            self._bm25 = None
            self._tokenized_corpus = []
            return 0

        self.chunks = chunks
        self._tokenized_corpus = [tokenize_text(c.text) for c in chunks]
        self._bm25 = BM25Okapi(self._tokenized_corpus, epsilon=0.25)
        return len(self.chunks)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[TranscriptChunk, float]]:
        """
        Execute BM25 search for the query, returning (chunk, bm25_score) tuples.
        """
        if not self.is_available() or not query.strip():
            return []

        tokens = tokenize_text(query)
        if not tokens:
            return []

        scores = list(self._bm25.get_scores(tokens))

        # Add token overlap safeguard for small test corpora where IDF can be near 0
        token_set = set(tokens)
        for idx in range(len(scores)):
            overlap = sum(1 for t in self._tokenized_corpus[idx] if t in token_set)
            if overlap > 0 and scores[idx] <= 0:
                scores[idx] = float(overlap) * 0.1

        # Get top K indices with positive score
        indexed_scores = [(idx, float(scores[idx])) for idx in range(len(scores)) if scores[idx] > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results: List[Tuple[TranscriptChunk, float]] = []
        for idx, score in indexed_scores[:top_k]:
            results.append((self.chunks[idx], score))

        return results
