"""
Parser for Lenny's Podcast topic index markdown taxonomy.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class TopicDefinition:
    """A topic index definition with linked episodes."""
    slug: str
    title: str
    episode_slugs: List[str] = field(default_factory=list)


EPISODE_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(\.\./episodes/([^/]+)/transcript\.md\)")


class TopicIndexRegistry:
    """
    Registry indexing topic taxonomies and bidirectional episode relationships.
    """

    def __init__(self) -> None:
        self.topics: Dict[str, TopicDefinition] = {}
        self.topic_to_episodes: Dict[str, List[str]] = {}
        self.episode_to_topics: Dict[str, List[str]] = {}
        self.topic_keywords: Dict[str, Set[str]] = {}

    def load_from_directory(self, index_dir: Path) -> int:
        """
        Parse all markdown topic files in data/transcripts/index/.
        Returns count of loaded topic indices.
        """
        if not index_dir.is_dir():
            return 0

        self.topics.clear()
        self.topic_to_episodes.clear()
        self.episode_to_topics.clear()
        self.topic_keywords.clear()

        for md_file in sorted(index_dir.glob("*.md")):
            # Skip README and master episodes overview
            if md_file.name.lower() in ["readme.md", "episodes.md"]:
                continue

            slug = md_file.stem.lower()
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            title = slug.replace("-", " ").title()
            # Extract title from first heading
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line.replace("# ", "").strip()
                    break

            # Extract episode slugs
            episode_slugs: List[str] = []
            for match in EPISODE_LINK_PATTERN.finditer(content):
                ep_slug = match.group(2).strip()
                if ep_slug not in episode_slugs:
                    episode_slugs.append(ep_slug)

            topic_def = TopicDefinition(
                slug=slug,
                title=title,
                episode_slugs=episode_slugs,
            )
            self.topics[slug] = topic_def
            self.topic_to_episodes[slug] = episode_slugs

            for ep_slug in episode_slugs:
                if ep_slug not in self.episode_to_topics:
                    self.episode_to_topics[ep_slug] = []
                if slug not in self.episode_to_topics[ep_slug]:
                    self.episode_to_topics[ep_slug].append(slug)

            # Store keywords for matching
            keywords = set(re.findall(r"[a-z0-9]+", title.lower()))
            keywords.add(slug)
            keywords.add(slug.replace("-", " "))
            self.topic_keywords[slug] = keywords

        return len(self.topics)

    def get_topics_for_episode(self, episode_slug: str) -> List[str]:
        """Return list of topic slugs linked to an episode."""
        return self.episode_to_topics.get(episode_slug, [])

    def get_episodes_for_topic(self, topic_slug: str) -> List[str]:
        """Return list of episode slugs tagged under a topic."""
        return self.topic_to_episodes.get(topic_slug, [])

    def match_topics_for_query(self, query: str) -> List[str]:
        """
        Identify topic slugs that match key concepts in the user query.
        """
        q_lower = query.lower()
        query_words = set(re.findall(r"[a-z0-9]+", q_lower))
        matched: List[str] = []

        for slug, keywords in self.topic_keywords.items():
            slug_phrase = slug.replace("-", " ")
            if slug_phrase in q_lower or slug in q_lower:
                matched.append(slug)
            elif any(k in query_words for k in keywords if len(k) > 3):
                matched.append(slug)

        return matched
