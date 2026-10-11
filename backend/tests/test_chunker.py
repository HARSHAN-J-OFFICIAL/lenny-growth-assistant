"""
Unit tests for intelligent transcript chunking.
"""

from pathlib import Path
from app.services.chunker import TranscriptChunker, build_timestamp_url
from app.services.transcript_parser import parse_transcript_file


def test_build_timestamp_url() -> None:
    """Verify YouTube timestamp link creation."""
    url = build_timestamp_url("4ef0juAMqoE", None, 61)
    assert url == "https://www.youtube.com/watch?v=4ef0juAMqoE&t=61s"


def test_chunker_preserves_speaker_and_timestamps() -> None:
    """Verify chunking maintains speaker identity, timestamps, and ordering."""
    sample_path = Path("data/transcripts/episodes/brian-chesky/transcript.md")
    if not sample_path.exists():
        sample_path = Path("../data/transcripts/episodes/brian-chesky/transcript.md")

    parsed = parse_transcript_file(sample_path)
    assert parsed is not None

    chunker = TranscriptChunker(target_words=150, overlap_words=30)
    chunks = chunker.chunk_transcript(parsed, topic_tags=["leadership", "culture"])

    assert len(chunks) > 5
    for c in chunks:
        assert c.episode_slug == "brian-chesky"
        assert c.guest == "Brian Chesky"
        assert c.start_seconds <= c.end_seconds
        assert len(c.text) > 0
        assert "leadership" in c.topic_tags
        assert c.timestamp_url is not None
        assert f"&t={c.start_seconds}s" in c.timestamp_url
