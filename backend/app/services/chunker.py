"""
Intelligent conversational chunking preserving speaker boundaries, timestamps, and context.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from app.services.transcript_parser import (
    ParsedTranscript,
    TranscriptTurn,
    format_seconds_to_timestamp,
)


@dataclass
class TranscriptChunk:
    """A searchable chunk with full citation metadata."""
    chunk_id: str
    episode_slug: str
    episode_title: str
    guest: str
    speaker: str
    start_timestamp: str
    start_seconds: int
    end_timestamp: str
    end_seconds: int
    timestamp_url: Optional[str]
    source_file: str
    text: str
    word_count: int
    char_count: int
    topic_tags: List[str] = field(default_factory=list)


def build_timestamp_url(video_id: Optional[str], youtube_url: Optional[str], seconds: int) -> Optional[str]:
    """
    Construct a direct YouTube URL jump link at the specified timestamp seconds.
    """
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"
    if youtube_url:
        base = youtube_url.split("&t=")[0]
        return f"{base}&t={seconds}s"
    return None


class TranscriptChunker:
    """
    Configurable chunker combining sequential speaker turns into contextual conversational windows.
    """

    def __init__(self, target_words: int = 180, overlap_words: int = 35) -> None:
        self.target_words = target_words
        self.overlap_words = overlap_words

    def chunk_transcript(
        self,
        transcript: ParsedTranscript,
        topic_tags: Optional[List[str]] = None,
    ) -> List[TranscriptChunk]:
        """
        Transform a parsed transcript into a series of overlapping conversational chunks.
        """
        if not transcript.turns:
            return []

        meta = transcript.metadata
        tags = topic_tags or []
        chunks: List[TranscriptChunk] = []
        chunk_counter = 0

        current_turns: List[TranscriptTurn] = []
        current_word_count = 0

        for turn in transcript.turns:
            turn_words = len(turn.text.split())

            # If a single turn is unusually large (> 350 words), split by paragraphs first
            if turn_words > (self.target_words * 2):
                paragraphs = [p.strip() for p in turn.text.split("\n\n") if p.strip()]
                if len(paragraphs) <= 1:
                    paragraphs = [p.strip() for p in turn.text.split(". ") if p.strip()]

                for para in paragraphs:
                    sub_turn = TranscriptTurn(
                        speaker=turn.speaker,
                        timestamp_str=turn.timestamp_str,
                        timestamp_seconds=turn.timestamp_seconds,
                        text=para,
                    )
                    current_turns.append(sub_turn)
                    current_word_count += len(para.split())

                    if current_word_count >= self.target_words:
                        chunk = self._create_chunk(current_turns, meta, tags, chunk_counter)
                        chunks.append(chunk)
                        chunk_counter += 1
                        current_turns = self._compute_overlap(current_turns)
                        current_word_count = sum(len(t.text.split()) for t in current_turns)
            else:
                current_turns.append(turn)
                current_word_count += turn_words

                if current_word_count >= self.target_words:
                    chunk = self._create_chunk(current_turns, meta, tags, chunk_counter)
                    chunks.append(chunk)
                    chunk_counter += 1
                    current_turns = self._compute_overlap(current_turns)
                    current_word_count = sum(len(t.text.split()) for t in current_turns)

        # Flush any remaining turns
        if current_turns:
            chunk = self._create_chunk(current_turns, meta, tags, chunk_counter)
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        turns: List[TranscriptTurn],
        meta: Any,
        tags: List[str],
        index: int,
    ) -> TranscriptChunk:
        """Create a TranscriptChunk from a list of conversational turns."""
        start_turn = turns[0]
        end_turn = turns[-1]

        # Format turn dialogue with speaker tags for clear reading and attribution
        lines = []
        primary_speakers = set()
        for t in turns:
            lines.append(f"{t.speaker}: {t.text}")
            primary_speakers.add(t.speaker)

        combined_text = "\n\n".join(lines)
        word_count = len(combined_text.split())
        speaker_label = ", ".join(sorted(primary_speakers))

        timestamp_url = build_timestamp_url(meta.video_id, meta.youtube_url, start_turn.timestamp_seconds)

        return TranscriptChunk(
            chunk_id=f"{meta.slug}_{index:04d}",
            episode_slug=meta.slug,
            episode_title=meta.title,
            guest=meta.guest,
            speaker=speaker_label,
            start_timestamp=start_turn.timestamp_str,
            start_seconds=start_turn.timestamp_seconds,
            end_timestamp=end_turn.timestamp_str,
            end_seconds=end_turn.timestamp_seconds,
            timestamp_url=timestamp_url,
            source_file=meta.source_file,
            text=combined_text,
            word_count=word_count,
            char_count=len(combined_text),
            topic_tags=tags,
        )

    def _compute_overlap(self, turns: List[TranscriptTurn]) -> List[TranscriptTurn]:
        """Keep the final turn(s) for conversational continuity."""
        if len(turns) <= 1:
            return []
        # Return at least the last turn if it has sufficient context
        return [turns[-1]]
