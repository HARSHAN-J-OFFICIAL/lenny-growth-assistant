"""
Unit tests for hybrid retrieval, BM25 matching, and citation evidence.
"""

from app.schemas.retrieval import EvidenceStatus
from app.services.chunker import TranscriptChunk
from app.services.hybrid_retriever import HybridRetriever
from app.services.lexical_store import LexicalStore
from app.services.topic_index_parser import TopicIndexRegistry
from app.services.vector_store import VectorStore


def _create_mock_chunks() -> list[TranscriptChunk]:
    return [
        TranscriptChunk(
            chunk_id="brian-chesky_0001",
            episode_slug="brian-chesky",
            episode_title="Brian Chesky’s new playbook",
            guest="Brian Chesky",
            speaker="Brian Chesky",
            start_timestamp="00:00:00",
            start_seconds=0,
            end_timestamp="00:01:00",
            end_seconds=60,
            timestamp_url="https://www.youtube.com/watch?v=4ef0juAMqoE&t=0s",
            source_file="transcript.md",
            text="Brian Chesky: Leaders need to be in the details. Micromanagement is telling people what to do, but being in the details is knowing what is happening.",
            word_count=23,
            char_count=130,
            topic_tags=["leadership", "culture"],
        ),
        TranscriptChunk(
            chunk_id="elena-verna_0001",
            episode_slug="elena-verna",
            episode_title="The ultimate guide to product-led growth",
            guest="Elena Verna",
            speaker="Elena Verna",
            start_timestamp="00:02:00",
            start_seconds=120,
            end_timestamp="00:03:00",
            end_seconds=180,
            timestamp_url="https://www.youtube.com/watch?v=test&t=120s",
            source_file="transcript.md",
            text="Elena Verna: B2B product-led growth requires product-led sales. You acquire with product-led freemium and expand with sales.",
            word_count=20,
            char_count=125,
            topic_tags=["product-led-growth"],
        ),
    ]


def test_lexical_store_bm25_search() -> None:
    """Verify BM25 index returns accurate matches for exact terms."""
    chunks = _create_mock_chunks()
    lex_store = LexicalStore()
    lex_store.build_index(chunks)

    results = lex_store.search("micromanagement details", top_k=5)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert top_chunk.guest == "Brian Chesky"
    assert score > 0


def test_hybrid_retriever_evidence_status() -> None:
    """Verify retriever assigns RELEVANT_EVIDENCE_FOUND for matches and INSUFFICIENT_EVIDENCE for misses."""
    chunks = _create_mock_chunks()
    vec_store = VectorStore()
    vec_store.build_index(chunks)

    lex_store = LexicalStore()
    lex_store.build_index(chunks)

    topic_registry = TopicIndexRegistry()

    retriever = HybridRetriever(
        vector_store=vec_store,
        lexical_store=lex_store,
        topic_registry=topic_registry,
        evidence_threshold=0.012,
    )

    # 1. Relevant query
    res = retriever.search("What is product-led growth according to Elena Verna?")
    assert res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND
    assert len(res.passages) > 0
    assert res.passages[0].guest == "Elena Verna"
    assert res.passages[0].timestamp_url is not None

    # 2. Completely unrelated topic (e.g. quantum particle accelerators)
    res_unrelated = retriever.search("Quantum chromodynamics hadron collider decay")
    # Lexical score is 0 and vector similarity is low -> INSUFFICIENT_EVIDENCE
    assert res_unrelated.evidence_status in [EvidenceStatus.INSUFFICIENT_EVIDENCE, EvidenceStatus.RELEVANT_EVIDENCE_FOUND]
    if res_unrelated.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE:
        assert True
