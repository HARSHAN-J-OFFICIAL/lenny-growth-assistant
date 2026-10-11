"""
Robust transcript file parser extracting YAML frontmatter, metadata, and speaker turns.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class TranscriptTurn:
    """A single speaker turn with timestamp."""
    speaker: str
    timestamp_str: str
    timestamp_seconds: int
    text: str


@dataclass
class TranscriptMetadata:
    """Extracted episode metadata."""
    slug: str
    guest: str
    title: str
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    publish_date: Optional[str] = None
    duration: Optional[str] = None
    duration_seconds: Optional[float] = None
    keywords: List[str] = field(default_factory=list)
    description: Optional[str] = None
    source_file: str = ""
    content_hash: str = ""


@dataclass
class ParsedTranscript:
    """Complete parsed transcript representation."""
    metadata: TranscriptMetadata
    turns: List[TranscriptTurn] = field(default_factory=list)
    raw_body: str = ""


# Regular expressions for speaker turns
# Matches: "Speaker Name (00:01:23): Dialogue text" or "(00:01:23): Dialogue text"
TURN_PATTERN = re.compile(
    r"^(?:([A-Za-z0-9\s\.\'\-\/]+?)\s*)?\(((\d{1,2}:)?\d{1,2}:\d{2})\):\s*(.*)$"
)


def parse_timestamp_to_seconds(ts_str: str) -> int:
    """
    Convert timestamp format HH:MM:SS or MM:SS to integer seconds.
    Example: '01:13:28' -> 4408, '01:05' -> 65.
    """
    parts = ts_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:
            return int(parts[0])
    except ValueError:
        return 0
    return 0


def format_seconds_to_timestamp(seconds: int) -> str:
    """Convert integer seconds to formatted HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def calculate_file_hash(content: str) -> str:
    """Calculate SHA-256 hash of transcript content for change detection."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_transcript_file(file_path: Path) -> Optional[ParsedTranscript]:
    """
    Parse a single transcript.md file, extracting YAML frontmatter and speaker turns.
    """
    if not file_path.is_file():
        return None

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    slug = file_path.parent.name
    content_hash = calculate_file_hash(content)

    frontmatter_dict: Dict[str, Any] = {}
    body_text = content

    # Check for YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_frontmatter = parts[1]
            body_text = parts[2]
            try:
                loaded = yaml.safe_load(raw_frontmatter)
                if isinstance(loaded, dict):
                    frontmatter_dict = loaded
            except Exception:
                frontmatter_dict = {}

    guest = str(frontmatter_dict.get("guest") or slug.replace("-", " ").title())
    title = str(frontmatter_dict.get("title") or f"Lenny's Podcast with {guest}")
    youtube_url = frontmatter_dict.get("youtube_url")
    video_id = frontmatter_dict.get("video_id")
    publish_date = str(frontmatter_dict.get("publish_date")) if frontmatter_dict.get("publish_date") else None
    duration = str(frontmatter_dict.get("duration")) if frontmatter_dict.get("duration") else None

    dur_sec = frontmatter_dict.get("duration_seconds")
    duration_seconds: Optional[float] = float(dur_sec) if dur_sec is not None else None

    raw_keywords = frontmatter_dict.get("keywords") or []
    keywords: List[str] = [str(k) for k in raw_keywords] if isinstance(raw_keywords, list) else []
    description = str(frontmatter_dict.get("description") or "").strip() or None

    metadata = TranscriptMetadata(
        slug=slug,
        guest=guest,
        title=title,
        youtube_url=str(youtube_url) if youtube_url else None,
        video_id=str(video_id) if video_id else None,
        publish_date=publish_date,
        duration=duration,
        duration_seconds=duration_seconds,
        keywords=keywords,
        description=description,
        source_file=file_path.name,
        content_hash=content_hash,
    )

    # Parse speaker turns from body
    turns: List[TranscriptTurn] = []
    lines = body_text.splitlines()

    current_speaker = guest
    current_ts_str = "00:00:00"
    current_ts_sec = 0
    current_paragraphs: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Skip markdown titles like "# Title" or "## Transcript"
        if stripped.startswith("#"):
            continue

        match = TURN_PATTERN.match(stripped)
        if match:
            # If we had a previous turn accumulating, save it
            if current_paragraphs:
                text_block = " ".join(current_paragraphs).strip()
                if text_block:
                    turns.append(TranscriptTurn(
                        speaker=current_speaker,
                        timestamp_str=current_ts_str,
                        timestamp_seconds=current_ts_sec,
                        text=text_block,
                    ))
                current_paragraphs = []

            speaker_match = match.group(1)
            ts_match = match.group(2)
            dialogue_text = match.group(4)

            if speaker_match:
                current_speaker = speaker_match.strip()

            current_ts_str = ts_match.strip()
            current_ts_sec = parse_timestamp_to_seconds(current_ts_str)

            if dialogue_text and dialogue_text.strip():
                current_paragraphs.append(dialogue_text.strip())
        else:
            # Continuing paragraph of current speaker
            current_paragraphs.append(stripped)

    # Flush final turn
    if current_paragraphs:
        text_block = " ".join(current_paragraphs).strip()
        if text_block:
            turns.append(TranscriptTurn(
                speaker=current_speaker,
                timestamp_str=current_ts_str,
                timestamp_seconds=current_ts_sec,
                text=text_block,
            ))

    return ParsedTranscript(
        metadata=metadata,
        turns=turns,
        raw_body=body_text.strip(),
    )
