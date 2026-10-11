"""
Unit tests for transcript parser and metadata extraction.
"""

from pathlib import Path
from app.services.transcript_parser import (
    format_seconds_to_timestamp,
    parse_timestamp_to_seconds,
    parse_transcript_file,
)


def test_timestamp_conversion_helpers() -> None:
    """Test timestamp parsing to seconds and formatting back."""
    assert parse_timestamp_to_seconds("00:01:23") == 83
    assert parse_timestamp_to_seconds("01:13:28") == 4408
    assert parse_timestamp_to_seconds("00:45") == 45
    assert parse_timestamp_to_seconds("invalid") == 0

    assert format_seconds_to_timestamp(83) == "00:01:23"
    assert format_seconds_to_timestamp(4408) == "01:13:28"


def test_parse_real_transcript_file() -> None:
    """Test parsing an actual podcast transcript from the local dataset."""
    sample_path = Path("data/transcripts/episodes/brian-chesky/transcript.md")
    if not sample_path.exists():
        # Fallback if run from backend/
        sample_path = Path("../data/transcripts/episodes/brian-chesky/transcript.md")

    assert sample_path.exists(), "Brian Chesky transcript file must exist in dataset"
    parsed = parse_transcript_file(sample_path)

    assert parsed is not None
    assert parsed.metadata.guest == "Brian Chesky"
    assert "playbook" in parsed.metadata.title.lower()
    assert parsed.metadata.video_id == "4ef0juAMqoE"
    assert parsed.metadata.youtube_url is not None
    assert parsed.metadata.duration_seconds == 4408.0
    assert len(parsed.metadata.keywords) > 0
    assert len(parsed.turns) > 10

    # Verify first turn has valid timestamp and speaker
    first_turn = parsed.turns[0]
    assert first_turn.speaker == "Brian Chesky"
    assert first_turn.timestamp_str == "00:00:00"
    assert first_turn.timestamp_seconds == 0
    assert "founders" in first_turn.text.lower()
