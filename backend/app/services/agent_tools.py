"""
Sandboxed Domain Tool Registry for Lenny Growth Assistant Agent Orchestration.
Strictly disallows all filesystem and shell-execution tools in user-facing sessions.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional
from app.services.ingestion_manager import ingestion_manager

logger = logging.getLogger("lenny.agent.tools")

# Strict Security Sandboxing Policy
DISALLOWED_TOOL_KEYWORDS = [
    "shell", "exec", "bash", "cmd", "terminal", "eval", "process",
    "filesystem", "file", "read_file", "write_file", "delete_file",
    "edit_file", "list_dir", "sh", "powershell", "python_eval",
]


class SecuritySandboxingViolation(Exception):
    """Raised when an unauthorized shell, filesystem, or execution tool is invoked."""
    pass


# ==============================================================================
# Domain Tool Implementations
# ==============================================================================

def search_podcast_transcripts(
    query: str,
    top_k: int = 5,
    guest_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search the hybrid vector + BM25 index of 303 Lenny's Podcast episodes
    for relevant quotes, guest frameworks, and timestamped transcripts.
    """
    retriever = ingestion_manager.retriever
    results = retriever.search(query=query, top_k=max(1, min(top_k, 10)))

    if results.evidence_status.value == "insufficient":
        return {
            "query": query,
            "evidence_status": "insufficient",
            "passages_count": 0,
            "passages": [],
            "instruction": (
                "No relevant evidence found in Lenny's Podcast transcripts. "
                "State honestly and clearly that Lenny's Podcast does not cover this topic."
            ),
        }

    passages = []
    for p in results.passages:
        if guest_filter and guest_filter.lower() not in p.guest.lower():
            continue
        passages.append({
            "guest": p.guest,
            "speaker": p.speaker,
            "episode_title": p.episode_title,
            "episode_slug": p.episode_slug,
            "timestamp_url": p.timestamp_url,
            "start_timestamp": p.start_timestamp,
            "score": round(p.score, 4),
            "text": p.text,
        })

    return {
        "query": query,
        "evidence_status": "sufficient",
        "passages_count": len(passages),
        "passages": passages,
    }


def get_topic_insights(topic_name: str) -> Dict[str, Any]:
    """
    Retrieve curated guest recommendations and episode counts from the 89
    curated topic indices (e.g. 'Pricing', 'Product-Led Growth', 'Hiring').
    """
    registry = ingestion_manager.topic_registry
    if not registry.topics:
        index_dir = ingestion_manager.transcripts_dir / "index"
        if index_dir.exists():
            registry.load_from_directory(index_dir)

    # Map common product abbreviations
    normalized_name = topic_name.strip()
    abbreviations = {
        "plg": "product-led-growth",
        "pm": "product-management",
        "ai": "ai",
        "ux": "user-experience",
    }
    target_query = abbreviations.get(normalized_name.lower(), normalized_name)

    matched_slugs = registry.match_topics_for_query(target_query)
    clean_slug = target_query.lower().replace(" ", "-")
    if clean_slug in registry.topics and clean_slug not in matched_slugs:
        matched_slugs.insert(0, clean_slug)

    results = []
    for slug in matched_slugs[:5]:
        topic_def = registry.topics.get(slug)
        if topic_def:
            episodes = registry.get_episodes_for_topic(slug)
            results.append({
                "topic_slug": slug,
                "topic_title": topic_def.title,
                "episode_count": len(episodes),
                "episodes": episodes[:8],
            })

    return {
        "queried_topic": topic_name,
        "matched_topics_count": len(results),
        "topics": results,
    }


def generate_sandboxed_artifact(
    title: str,
    artifact_type: str,
    content: str,
) -> Dict[str, Any]:
    """
    Generate a validated, sandboxed deliverable (markdown, html, svg, code)
    such as a PRD checklist, pricing framework, or growth model.
    """
    valid_types = ["markdown", "html", "svg", "code"]
    clean_type = artifact_type.lower().strip()
    if clean_type not in valid_types:
        clean_type = "markdown"

    formatted_block = f':::artifact{{title="{title}" type="{clean_type}"}}\n{content.strip()}\n:::'
    return {
        "status": "created",
        "title": title,
        "artifact_type": clean_type,
        "formatted_block": formatted_block,
    }


# ==============================================================================
# Tool Registry & JSON Schema Definitions (OpenAI / Ollama Tool Calling Compatible)
# ==============================================================================

AGENT_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_podcast_transcripts",
            "description": (
                "Search the verified dataset of 303 Lenny's Podcast episodes for relevant "
                "transcript passages, guest insights, frameworks, and exact YouTube timestamps."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific search query (e.g. 'Brian Chesky founder mode', 'Elena Verna PLG metrics')",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of passages to retrieve (1-10, default 5)",
                        "default": 5,
                    },
                    "guest_filter": {
                        "type": "string",
                        "description": "Optional name of the podcast guest to restrict search results to",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_topic_insights",
            "description": (
                "Retrieve curated guest lists, episode counts, and key discussion angles "
                "for a specific product topic (e.g., 'Product-Led Growth', 'Pricing', 'Hiring PMs')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_name": {
                        "type": "string",
                        "description": "Topic or keyword (e.g. 'Pricing', 'PLG', 'Interviews')",
                    },
                },
                "required": ["topic_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_sandboxed_artifact",
            "description": (
                "Generate a structured, sandboxed deliverable (markdown checklist, PRD, table, or code snippet). "
                "Creates an interactive artifact in the assistant interface."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Clear descriptive title for the artifact",
                    },
                    "artifact_type": {
                        "type": "string",
                        "enum": ["markdown", "html", "svg", "code"],
                        "description": "Type of artifact to generate",
                    },
                    "content": {
                        "type": "string",
                        "description": "Structured content or body of the artifact",
                    },
                },
                "required": ["title", "artifact_type", "content"],
            },
        },
    },
]

TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "search_podcast_transcripts": search_podcast_transcripts,
    "get_topic_insights": get_topic_insights,
    "generate_sandboxed_artifact": generate_sandboxed_artifact,
}


def verify_sandboxing() -> bool:
    """
    Security verification: confirm that NO filesystem or shell execution tools
    exist in the registered tools whitelist.
    """
    for tool_name in TOOL_REGISTRY:
        lower_name = tool_name.lower()
        for kw in DISALLOWED_TOOL_KEYWORDS:
            if kw in lower_name:
                raise SecuritySandboxingViolation(
                    f"Security Sandboxing Violation: Tool '{tool_name}' contains disallowed capability '{kw}'"
                )
    return True


def execute_agent_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely execute a registered domain tool with arguments.
    Enforces sandboxing checks prior to dispatch.
    """
    # 1. Enforce sandboxing verification
    verify_sandboxing()

    # 2. Check for disallowed keywords in requested tool name
    lower_name = tool_name.lower()
    for kw in DISALLOWED_TOOL_KEYWORDS:
        if kw in lower_name:
            raise SecuritySandboxingViolation(
                f"Unauthorized tool invocation: '{tool_name}' involves forbidden '{kw}' operations."
            )

    # 3. Lookup tool in whitelist registry
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(
            f"Unknown tool '{tool_name}'. Available sandboxed tools: {list(TOOL_REGISTRY.keys())}"
        )

    tool_fn = TOOL_REGISTRY[tool_name]
    logger.info(f"Executing sandboxed agent tool: {tool_name} with args: {arguments}")
    return tool_fn(**arguments)
