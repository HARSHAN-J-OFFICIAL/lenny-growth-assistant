"""
Parser extracting structured sandboxed artifacts (PRDs, tables, mockups) from model responses.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple

# Pattern matching :::artifact{title="..." type="..."} ... ::: or end of string
ARTIFACT_DIRECTIVE_PATTERN = re.compile(
    r":::artifact\{title=[\"'](.*?)[\"']\s+type=[\"'](.*?)[\"']\}\s*\n(.*?)(?:\n:::|\Z)",
    re.DOTALL,
)

# Fallback pattern for fenced code blocks with explicit artifact comments
# Example: ```html <!-- artifact: title="User Journey" type="html" --> ... ```
FENCED_ARTIFACT_PATTERN = re.compile(
    r"```(html|svg|markdown|json|css|code)\s*\n<!--\s*artifact:\s*title=[\"'](.*?)[\"']\s*-->\s*\n(.*?)(?:\n```|\Z)",
    re.DOTALL,
)


@dataclass
class ExtractedArtifact:
    """An artifact extracted from model response text."""
    title: str
    artifact_type: str
    content: str


def extract_artifacts(raw_text: str) -> Tuple[str, List[ExtractedArtifact]]:
    """
    Extracts all structured artifacts from model response text.
    Returns (cleaned_text, extracted_artifacts).
    """
    artifacts: List[ExtractedArtifact] = []

    # 1. Match directive pattern :::artifact{...} ... :::
    def directive_replacer(match: re.Match) -> str:
        title = match.group(1).strip()
        art_type = match.group(2).strip().lower()
        content = match.group(3).strip()
        artifacts.append(ExtractedArtifact(title=title, artifact_type=art_type, content=content))
        return f"\n> 📄 **Artifact Generated**: *{title}* (View in Artifacts Panel)\n"

    cleaned_text = ARTIFACT_DIRECTIVE_PATTERN.sub(directive_replacer, raw_text)

    # 2. Match fenced artifact pattern
    def fenced_replacer(match: re.Match) -> str:
        art_type = match.group(1).strip().lower()
        title = match.group(2).strip()
        content = match.group(3).strip()
        artifacts.append(ExtractedArtifact(title=title, artifact_type=art_type, content=content))
        return f"\n> 📄 **Artifact Generated**: *{title}* (View in Artifacts Panel)\n"

    cleaned_text = FENCED_ARTIFACT_PATTERN.sub(fenced_replacer, cleaned_text)

    return cleaned_text.strip(), artifacts
