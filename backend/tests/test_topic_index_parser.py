"""
Unit tests for topic index taxonomy parser and query matching.
"""

from pathlib import Path
from app.services.topic_index_parser import TopicIndexRegistry


def test_topic_index_loading_and_matching() -> None:
    """Test loading topic markdown files and matching user queries."""
    index_dir = Path("data/transcripts/index")
    if not index_dir.exists():
        index_dir = Path("../data/transcripts/index")

    assert index_dir.exists(), "Topic index directory must exist"

    registry = TopicIndexRegistry()
    loaded_count = registry.load_from_directory(index_dir)

    assert loaded_count > 50, f"Expected > 50 topic indexes, found {loaded_count}"
    assert "product-led-growth" in registry.topics
    assert "ab-testing" in registry.topics

    # Check episode links for product-led growth
    plg_episodes = registry.get_episodes_for_topic("product-led-growth")
    assert len(plg_episodes) > 5

    # Check query matching
    matched = registry.match_topics_for_query("How do I implement product-led growth?")
    assert "product-led-growth" in matched
