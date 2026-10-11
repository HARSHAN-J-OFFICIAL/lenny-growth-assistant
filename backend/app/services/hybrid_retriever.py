"""
Hybrid retrieval engine combining Dense Semantic, BM25 Lexical, and Topic Index Signals with Reciprocal Rank Fusion (RRF).
"""

import time
from typing import Any, Dict, List, Optional, Set, Tuple
from app.core.config import settings
from app.schemas.retrieval import EvidenceStatus, RetrievedPassage, SearchResponse
from app.services.chunker import TranscriptChunk
from app.services.lexical_store import LexicalStore, tokenize_text
from app.services.topic_index_parser import TopicIndexRegistry
from app.services.vector_store import VectorStore

COMMON_STOPWORDS = {
    "what", "how", "why", "when", "where", "which", "who", "whom", "whose",
    "this", "that", "these", "those", "with", "from", "about", "into", "through",
    "after", "over", "between", "out", "against", "during", "without", "before",
    "under", "around", "among", "and", "the", "for", "are", "can", "does", "did",
    "have", "has", "had", "been", "was", "were", "will", "would", "should", "could",
    "their", "they", "them", "your", "you", "our", "its", "not", "some", "any", "like"
}


class HybridRetriever:
    """
    Production-grade hybrid retriever combining Dense Vectors, BM25, and Topic Index signals.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        lexical_store: LexicalStore,
        topic_registry: TopicIndexRegistry,
        rrf_k: int = 60,
        evidence_threshold: float = 0.012,
    ) -> None:
        self.vector_store = vector_store
        self.lexical_store = lexical_store
        self.topic_registry = topic_registry
        self.rrf_k = rrf_k
        self.evidence_threshold = evidence_threshold

    def is_ready(self) -> bool:
        """Check if both vector and lexical stores are populated and ready."""
        return self.vector_store.is_available() and self.lexical_store.is_available()

    def search(
        self,
        query: str,
        top_k: int = 5,
        topic_filter: Optional[str] = None,
        guest_filter: Optional[str] = None,
    ) -> SearchResponse:
        """
        Execute hybrid search across dense vector and lexical indices with RRF merging.
        """
        start_time = time.perf_counter()
        clean_query = query.strip()

        if not clean_query:
            return SearchResponse(
                query=query,
                evidence_status=EvidenceStatus.INVALID_QUERY,
                passages=[],
                total_candidates=0,
                latency_ms=0.0,
                diagnostics={"reason": "Empty or whitespace query provided"},
            )

        if not self.is_ready():
            # Attempt lazy loading from disk if not yet initialized
            if self.vector_store.load():
                self.lexical_store.build_index(self.vector_store.chunks)

            if not self.is_ready():
                if len(self.vector_store.chunks) == 0:
                    return SearchResponse(
                        query=query,
                        evidence_status=EvidenceStatus.EMPTY_KNOWLEDGE_BASE,
                        passages=[],
                        total_candidates=0,
                        latency_ms=0.0,
                        diagnostics={"reason": "Knowledge base has not been ingested yet"},
                    )
                return SearchResponse(
                    query=query,
                    evidence_status=EvidenceStatus.INDEX_UNAVAILABLE,
                    passages=[],
                    total_candidates=0,
                    latency_ms=0.0,
                    diagnostics={"reason": "Retrieval indexes are currently initializing or unavailable"},
                )

        # 1. Topic discovery & episode filters
        matched_topics = self.topic_registry.match_topics_for_query(clean_query)
        boosted_episodes: Set[str] = set()
        for t_slug in matched_topics:
            boosted_episodes.update(self.topic_registry.get_episodes_for_topic(t_slug))

        # Restrict episodes if topic_filter or guest_filter is provided
        allowed_episodes: Optional[Set[str]] = None
        if topic_filter:
            episodes_in_topic = set(self.topic_registry.get_episodes_for_topic(topic_filter.lower()))
            allowed_episodes = episodes_in_topic if allowed_episodes is None else allowed_episodes & episodes_in_topic

        if guest_filter:
            guest_norm = guest_filter.lower().strip()
            # Find matching slugs or guests
            matching_guest_slugs = {
                c.episode_slug for c in self.vector_store.chunks
                if guest_norm in c.guest.lower() or guest_norm in c.episode_slug.lower()
            }
            allowed_episodes = matching_guest_slugs if allowed_episodes is None else allowed_episodes & matching_guest_slugs

        # 2. Retrieve candidates from both systems
        candidate_k = max(top_k * 4, 30)
        semantic_results = self.vector_store.search(clean_query, top_k=candidate_k)
        lexical_results = self.lexical_store.search(clean_query, top_k=candidate_k)

        # 3. Reciprocal Rank Fusion (RRF)
        # chunk_id -> {chunk, rrf_score, semantic_score, lexical_score, semantic_rank, lexical_rank}
        candidate_map: Dict[str, Dict[str, Any]] = {}

        for rank, (chunk, score) in enumerate(semantic_results, start=1):
            if allowed_episodes is not None and chunk.episode_slug not in allowed_episodes:
                continue
            entry = candidate_map.setdefault(chunk.chunk_id, {
                "chunk": chunk,
                "rrf_score": 0.0,
                "semantic_score": score,
                "lexical_score": None,
                "semantic_rank": rank,
                "lexical_rank": None,
            })
            entry["rrf_score"] += 1.0 / (self.rrf_k + rank)

        for rank, (chunk, score) in enumerate(lexical_results, start=1):
            if allowed_episodes is not None and chunk.episode_slug not in allowed_episodes:
                continue
            entry = candidate_map.setdefault(chunk.chunk_id, {
                "chunk": chunk,
                "rrf_score": 0.0,
                "semantic_score": None,
                "lexical_score": score,
                "semantic_rank": None,
                "lexical_rank": rank,
            })
            entry["rrf_score"] += 1.0 / (self.rrf_k + rank)
            entry["lexical_score"] = score
            entry["lexical_rank"] = rank

        # Ensure all lexical candidates have an accurate semantic score rather than None / 0.0
        missing_sem_ids = [cid for cid, d in candidate_map.items() if d["semantic_score"] is None]
        if missing_sem_ids and self.vector_store.is_available():
            computed_sem_scores = self.vector_store.get_chunk_scores(clean_query, missing_sem_ids)
            for cid, s_score in computed_sem_scores.items():
                if cid in candidate_map:
                    candidate_map[cid]["semantic_score"] = s_score

        # 4. Apply topical boost for query-topic overlap
        for chunk_id, data in candidate_map.items():
            ch = data["chunk"]
            if ch.episode_slug in boosted_episodes:
                # Add a modest topical bonus
                data["rrf_score"] += 0.005

        # 5. Sort candidates by RRF score
        sorted_candidates = sorted(
            candidate_map.values(),
            key=lambda x: x["rrf_score"],
            reverse=True,
        )

        # 6. Deduplicate adjacent chunks from the same episode
        deduped_passages: List[RetrievedPassage] = []
        seen_episodes_chunks: Dict[str, List[int]] = {}

        for rank_idx, item in enumerate(sorted_candidates, start=1):
            ch: TranscriptChunk = item["chunk"]
            ep_slug = ch.episode_slug
            chunk_num = int(ch.chunk_id.split("_")[-1]) if "_" in ch.chunk_id else 0

            # If an immediately adjacent chunk was already added, skip to diversify
            existing_chunks = seen_episodes_chunks.get(ep_slug, [])
            if any(abs(chunk_num - ec) <= 1 for ec in existing_chunks):
                continue

            seen_episodes_chunks.setdefault(ep_slug, []).append(chunk_num)

            passage = RetrievedPassage(
                chunk_id=ch.chunk_id,
                episode_slug=ch.episode_slug,
                episode_title=ch.episode_title,
                guest=ch.guest,
                speaker=ch.speaker,
                text=ch.text,
                start_timestamp=ch.start_timestamp,
                start_seconds=ch.start_seconds,
                end_timestamp=ch.end_timestamp,
                end_seconds=ch.end_seconds,
                timestamp_url=ch.timestamp_url,
                source_file=ch.source_file,
                score=round(float(item["rrf_score"]), 6),
                rrf_rank=len(deduped_passages) + 1,
                semantic_score=round(float(item["semantic_score"]), 4) if item["semantic_score"] is not None else None,
                lexical_score=round(float(item["lexical_score"]), 2) if item["lexical_score"] is not None else None,
                topic_tags=ch.topic_tags,
            )
            deduped_passages.append(passage)

            if len(deduped_passages) >= top_k:
                break

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 7. Evaluate Evidence Status & Grounding across top passages
        # A query is grounded if at least one candidate among the top passages demonstrates
        # genuine semantic, lexical, or entity-specific alignment.
        query_tokens = [t for t in tokenize_text(clean_query) if t not in COMMON_STOPWORDS and len(t) > 2]
        unique_q_tokens = set(query_tokens)

        eval_window = deduped_passages[:min(3, len(deduped_passages))] if deduped_passages else []

        best_grounded_passage: Optional[RetrievedPassage] = None
        best_grounding_reason = "insufficient_grounding"
        best_coverage = 0.0

        for p in eval_window:
            sem = p.semantic_score or 0.0
            lex = p.lexical_score or 0.0

            # Compute term coverage of the query's distinct content tokens
            passage_corpus = f"{p.text} {p.episode_title} {p.guest} {p.speaker}".lower()
            passage_tokens = set(tokenize_text(passage_corpus))
            matched_terms = unique_q_tokens.intersection(passage_tokens)
            coverage = len(matched_terms) / len(unique_q_tokens) if unique_q_tokens else 1.0
            if coverage > best_coverage:
                best_coverage = coverage

            # Direct Guest / Speaker / Title Grounding:
            # Check if any content token directly references the interviewed guest, speaker, or title
            entity_in_meta = any(
                t in p.guest.lower() or t in p.speaker.lower() or t in p.episode_title.lower() or t in p.episode_slug.lower()
                for t in unique_q_tokens
            )

            p_grounded = False
            p_reason = ""

            # Grounding criteria:
            # 1. High Semantic Confidence: sem >= 0.70 (handles varied conversational vocabulary)
            # 2. Balanced Hybrid Match: sem >= 0.60 and (coverage >= 0.40 or lex >= 10.0)
            # 3. Strong Lexical & Multi-Term Match: coverage >= 0.60 and lex >= 12.0 and sem >= 0.50
            # 4. Direct Entity/Guest Match: entity_in_meta and coverage >= 0.60 and (sem >= 0.55 or lex >= 8.0)
            if sem >= 0.70:
                p_grounded = True
                p_reason = "high_semantic_confidence"
            elif sem >= 0.60 and (coverage >= 0.40 or lex >= 10.0):
                p_grounded = True
                p_reason = "balanced_hybrid_match"
            elif coverage >= 0.60 and lex >= 12.0 and sem >= 0.50:
                p_grounded = True
                p_reason = "strong_lexical_entity_match"
            elif entity_in_meta and coverage >= 0.60 and (sem >= 0.55 or lex >= 8.0):
                p_grounded = True
                p_reason = "direct_guest_or_topic_match"

            if p_grounded and p.score >= self.evidence_threshold:
                best_grounded_passage = p
                best_grounding_reason = f"{p_reason} (chunk={p.chunk_id}, sem={sem:.3f}, coverage={coverage:.2f}, lex={lex:.1f})"
                break
            else:
                best_grounding_reason = f"insufficient_grounding (chunk={p.chunk_id}, sem={sem:.3f}, coverage={coverage:.2f}, lex={lex:.1f})"

        if best_grounded_passage is not None:
            evidence_status = EvidenceStatus.RELEVANT_EVIDENCE_FOUND
            grounding_reason = best_grounding_reason
            term_coverage = best_coverage
        else:
            evidence_status = EvidenceStatus.INSUFFICIENT_EVIDENCE
            grounding_reason = best_grounding_reason if eval_window else "no_candidate_passages_found"
            term_coverage = best_coverage

        diagnostics = {
            "semantic_candidates_count": len(semantic_results),
            "lexical_candidates_count": len(lexical_results),
            "total_candidates_merged": len(candidate_map),
            "top_rrf_score": deduped_passages[0].score if deduped_passages else 0.0,
            "evidence_threshold": self.evidence_threshold,
            "matched_topics": matched_topics,
            "boosted_episodes_count": len(boosted_episodes),
            "term_coverage": round(term_coverage, 2),
            "grounding_reason": grounding_reason,
            "latency_ms": latency_ms,
        }

        return SearchResponse(
            query=clean_query,
            evidence_status=evidence_status,
            passages=deduped_passages,
            total_candidates=len(candidate_map),
            latency_ms=latency_ms,
            diagnostics=diagnostics,
        )
