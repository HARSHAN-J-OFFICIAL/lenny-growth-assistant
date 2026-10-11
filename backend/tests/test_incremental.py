"""
Tests for incremental update detection and change tracking.
"""

import hashlib
from pathlib import Path
from app.services.transcript_parser import parse_transcript_file


SAMPLE_EPISODE_TEXT_V1 = """---
title: "Sample Episode"
guest: "Jane Doe"
youtube_url: "https://www.youtube.com/watch?v=sample123"
---

Jane Doe (00:00:10): Welcome Jane.
Lenny Rachitsky (00:00:15): Thank you Lenny.
"""

SAMPLE_EPISODE_TEXT_V2 = """---
title: "Sample Episode Updated"
guest: "Jane Doe"
youtube_url: "https://www.youtube.com/watch?v=sample123"
---

Jane Doe (00:00:10): Welcome Jane to the podcast.
Lenny Rachitsky (00:00:15): Thank you Lenny, excited to be here.
"""


def test_deterministic_content_hash(tmp_path: Path) -> None:
    """Verify SHA-256 content hash is deterministic for unchanged files."""
    file_path = tmp_path / "transcript.md"
    file_path.write_text(SAMPLE_EPISODE_TEXT_V1, encoding="utf-8")

    parsed_1a = parse_transcript_file(file_path)
    parsed_1b = parse_transcript_file(file_path)

    assert parsed_1a is not None
    assert parsed_1b is not None
    assert parsed_1a.metadata.content_hash == parsed_1b.metadata.content_hash

    expected_hash = hashlib.sha256(SAMPLE_EPISODE_TEXT_V1.encode("utf-8")).hexdigest()
    assert parsed_1a.metadata.content_hash == expected_hash


def test_content_change_detection(tmp_path: Path) -> None:
    """Verify file modification produces a new hash triggering change detection."""
    f1 = tmp_path / "ep1" / "transcript.md"
    f1.parent.mkdir(parents=True)
    f1.write_text(SAMPLE_EPISODE_TEXT_V1, encoding="utf-8")

    f2 = tmp_path / "ep2" / "transcript.md"
    f2.parent.mkdir(parents=True)
    f2.write_text(SAMPLE_EPISODE_TEXT_V2, encoding="utf-8")

    parsed_v1 = parse_transcript_file(f1)
    parsed_v2 = parse_transcript_file(f2)

    assert parsed_v1 is not None
    assert parsed_v2 is not None
    assert parsed_v1.metadata.content_hash != parsed_v2.metadata.content_hash
