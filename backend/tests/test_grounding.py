"""
Grounding and citation verification tests against the live index.
Validates:
1. Verifiable product-management questions return relevant citations and verified URLs.
2. Unrelated questions return INSUFFICIENT_EVIDENCE without hallucinating facts.
"""

from app.schemas.retrieval import EvidenceStatus
from app.services.ingestion_manager import ingestion_manager


def setup_module() -> None:
    """Ensure persistent indices are loaded before running grounding tests."""
    ingestion_manager.initialize()


def test_grounding_brian_chesky_details() -> None:
    """Verify retrieval returns Brian Chesky on being in the details and micromanagement."""
    query = "Brian Chesky being in the details and micromanagement playbook"
    res = ingestion_manager.retriever.search(query, top_k=3)

    assert res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND
    assert len(res.passages) > 0
    top = res.passages[0]
    assert "Brian Chesky" in top.guest or "Brian Chesky" in top.speaker or "chesky" in top.episode_slug
    assert top.timestamp_url is not None
    assert "youtube.com" in top.timestamp_url
    assert top.text is not None and len(top.text) > 20


def test_grounding_elena_verna_plg() -> None:
    """Verify retrieval returns Elena Verna on product-led growth."""
    query = "Elena Verna product-led growth and sales"
    res = ingestion_manager.retriever.search(query, top_k=3)

    assert res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND
    assert len(res.passages) > 0
    top = res.passages[0]
    assert "Elena Verna" in top.guest or "Elena Verna" in top.speaker or "elena" in top.episode_slug
    assert top.timestamp_url is not None
    assert "youtube.com" in top.timestamp_url


def test_grounding_shreyas_doshi() -> None:
    """Verify retrieval returns Shreyas Doshi on PM prioritization / frameworks."""
    query = "Shreyas Doshi product management prioritization"
    res = ingestion_manager.retriever.search(query, top_k=3)

    assert res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND
    assert len(res.passages) > 0
    top = res.passages[0]
    assert "Shreyas Doshi" in top.guest or "Shreyas Doshi" in top.speaker or "shreyas" in top.episode_slug
    assert top.timestamp_url is not None


def test_unrelated_query_insufficient_evidence() -> None:
    """Verify retrieval returns INSUFFICIENT_EVIDENCE for off-topic query."""
    query = "Quantum chromodynamics gluon plasma hadron decay rate"
    res = ingestion_manager.retriever.search(query, top_k=3)

    assert res.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert "insufficient_grounding" in res.diagnostics.get("grounding_reason", "")


def test_grounding_first_name_known_guest() -> None:
    """Verify short first-name query for known guest resolves to RELEVANT_EVIDENCE_FOUND."""
    query = "Who is Elena?"
    res = ingestion_manager.retriever.search(query, top_k=3)

    assert res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND
    assert len(res.passages) > 0
    top = res.passages[0]
    assert "Elena" in top.guest or "Elena" in top.speaker or "elena" in top.episode_slug
    assert top.timestamp_url is not None


def test_grounding_hiring_product_managers() -> None:
    """Verify genuine research query on hiring PMs returns RELEVANT_EVIDENCE_FOUND with verified passages."""
    query = "What is the best way to hire product managers?"
    res = ingestion_manager.retriever.search(query, top_k=3)

    assert res.evidence_status == EvidenceStatus.RELEVANT_EVIDENCE_FOUND
    assert len(res.passages) > 0
    # Top passage must have a valid non-zero semantic score now that lexical candidates are accurately evaluated
    assert res.passages[0].semantic_score is not None
    assert res.passages[0].semantic_score > 0.40


def test_grounding_nonexistent_person_zyzyx() -> None:
    """Verify querying an entity absent from the transcripts returns INSUFFICIENT_EVIDENCE."""
    query = "Who is Zyzyx McQwerty?"
    res = ingestion_manager.retriever.search(query, top_k=3)

    assert res.evidence_status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert "insufficient_grounding" in res.diagnostics.get("grounding_reason", "")
