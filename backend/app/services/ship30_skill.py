"""
Ship 30 for 30 Skill Engine for generating viral, executive-ready atomic essays (~1,250 words).
Encodes the exact digital writing architecture established by Dickie Bush & Nicolas Cole.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from app.services.ingestion_manager import ingestion_manager
from app.services.llm_provider import generate_completion
from app.services.artifact_extractor import extract_artifacts

logger = logging.getLogger("lenny.skills.ship30")

SHIP_30_SYSTEM_PROMPT = """You are a master digital writer trained in the "Ship 30 for 30" atomic essay methodology (by Dickie Bush & Nicolas Cole) and a world-class Product Growth Strategist.

Your mission is to transform tactical insights from Lenny's Podcast into an expansive, compelling long-form atomic essay (~1,250 words) that product leaders, founders, and growth operators will bookmark and share.

You must follow these 8 Core Ship 30 for 30 Principles:
1. **The Irresistible Headline**: Craft an attention-grabbing, curiosity-piquing headline that promises a concrete outcome (e.g. "How Brian Chesky Rebuilt Airbnb: The 5 'Founder Mode' Rules Every CEO Needs").
2. **The 1-3-1 Cadence Hook**:
   - 1 single punchy opening sentence that challenges conventional wisdom.
   - 3 short sentences building tension, identifying the hidden trap, and giving context.
   - 1 definitive sentence that pivots into the solution.
3. **Clear Narrative Progression**: Take the reader on a journey from Status Quo Pain -> The Turning Point Epiphany -> The Core Framework -> Actionable Execution.
4. **Short, Breathable Paragraphs**: Keep paragraphs to 1-3 sentences. Never write dense walls of text. Rhythm and whitespace matter.
5. **Structured Sections & Distinct Subheadings**: Use clear H2/H3 subheadings to guide skimmers through the piece.
6. **Selective Bold Lead-ins**: EVERY major point or takeaway MUST begin with a **Bold Lead-in** (e.g., **The Trap:**, **The Secret:**, **The Framework:**, **The Hard Truth:**, **The Action:**).
7. **Scannable Pillars with Guest Grounding**:
   - Organize into 3 to 5 core pillars.
   - Ground every claim directly in the provided podcast transcript excerpts.
   - Attribute quotes and tactics directly to the guest (e.g., Brian Chesky, Elena Verna, Shreyas Doshi).
8. **Actionable Takeaways & Execution Checklist**: Conclude with a concrete, numbered summary checklist that the reader can execute this week.

Output Format:
Wrap the full essay inside an artifact block:
:::artifact{title="Ship 30 Essay: <Title>" type="markdown"}
# <Headline>

<1-3-1 Hook>

<Narrative Progression & Core Pillars with Bold Lead-ins>

<Actionable Takeaways & Next Steps>
:::
"""


class Ship30SkillService:
    """
    Reusable Ship 30 for 30 essay generation service.
    """

    def is_triggered(self, query: str, skill_param: Optional[str] = None) -> bool:
        """Check if query or skill parameter explicitly triggers Ship 30 essay generation."""
        if skill_param and "ship" in skill_param.lower():
            return True
        low = query.lower()
        trigger_keywords = [
            "ship 30", "ship30", "atomic essay", "write an essay",
            "write a viral post", "write a breakdown", "1250 words",
            "essay on", "publish an essay",
        ]
        return any(k in low for k in trigger_keywords)

    async def generate_essay(
        self,
        topic: str,
        provider: str = "ollama",
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute grounded Ship 30 for 30 essay generation:
        1. Retrieve relevant podcast transcripts.
        2. Construct grounded Ship 30 prompt.
        3. Execute LLM completion.
        4. Extract structured markdown artifact.
        """
        logger.info(f"Generating Ship 30 essay on: '{topic}' using {provider}/{model_name}")

        # 1. Retrieve evidence via thread pool
        retrieval_res = await asyncio.to_thread(ingestion_manager.retriever.search, topic, top_k=5)
        citations = []
        evidence_lines = []

        for p in retrieval_res.passages:
            citations.append({
                "guest": p.guest,
                "episode_title": p.episode_title,
                "timestamp_url": p.timestamp_url,
                "start_timestamp": p.start_timestamp,
            })
            evidence_lines.append(
                f"[{p.episode_title} | Guest: {p.guest} | Time: {p.start_timestamp}]\n{p.text}\n"
            )

        context_str = "\n".join(evidence_lines) if evidence_lines else "No specific transcripts found."

        # 2. Build multi-section generation prompts for comprehensive ~1,250-word depth
        part1_prompt = f"""### Verifiable Podcast Evidence:
{context_str}

### Writing Assignment (Part 1 of 2):
Write the FIRST HALF (~600 words) of a comprehensive, publication-ready Ship 30 for 30 atomic essay about: {topic}

Required Structure for Part 1:
1. # The Irresistible Headline (Punchy, outcome-focused)
2. The 1-3-1 Cadence Hook:
   - 1 single opening sentence that shatters conventional wisdom.
   - 3 short sentences building tension, naming the hidden friction, and setting context.
   - 1 definitive sentence pivoting to the solution.
3. ## The Hidden Trap: Why Most Teams Fail at {topic}
   - Break down the status quo pain with short, breathable 1-3 sentence paragraphs.
   - Use bold lead-ins (**The Trap:**, **The Flaw:**, **The Cost:**).
4. ## The Turning Point Epiphany: What the Top 1% Know
   - Introduce the shift in mental models.
5. ## Core Pillar 1 & 2: Grounded Frameworks
   - Ground directly in the podcast transcript quotes and guests above.
   - Use bold lead-ins (**The Principle:**, **The Podcast Evidence:**, **The Play:**).

Deliver deep, tactical, highly scannable content. Do not conclude yet."""

        # 3. Generate Part 1
        raw_part1 = await generate_completion(
            messages=[
                {"role": "system", "content": SHIP_30_SYSTEM_PROMPT},
                {"role": "user", "content": part1_prompt},
            ],
            provider=provider,
            model_name=model_name,
            temperature=0.35,
        )

        # 4. Generate Part 2 (Continuation) to reach ~1,250 target words
        part2_prompt = f"""Here is Part 1 of our Ship 30 for 30 atomic essay on '{topic}':
{raw_part1[-1200:]}

### Verifiable Podcast Evidence:
{context_str}

### Writing Assignment (Part 2 of 2):
Write the SECOND HALF (~600 words) continuing this essay.
Required Structure for Part 2:
1. ## Core Pillar 3 & 4: Tactical Growth Drivers
   - Ground directly in guest advice from Lenny's Podcast excerpts.
   - Use bold lead-ins (**The Rule:**, **The Guest Insight:**, **The Execution:**).
2. ## The 5-Step Operator Implementation Playbook
   - Step 1 through Step 5 detailed tactical workflow.
3. ## The 7-Day Execution Checklist
   - Day-by-day operator guide (Day 1 to Day 7).
4. ## The Hard Truth: Final Takeaway
   - 1-3-1 closing cadence on what separates winners from losers.

Do NOT repeat the headline or hook. Continue seamlessly from Part 1."""

        raw_part2 = await generate_completion(
            messages=[
                {"role": "system", "content": SHIP_30_SYSTEM_PROMPT},
                {"role": "user", "content": part2_prompt},
            ],
            provider=provider,
            model_name=model_name,
            temperature=0.35,
        )

        # 5. Extract and clean full essay
        clean_part1, arts1 = extract_artifacts(raw_part1)
        part1_text = arts1[0].content if arts1 else raw_part1.strip()

        clean_part2, arts2 = extract_artifacts(raw_part2)
        part2_text = arts2[0].content if arts2 else raw_part2.strip()

        # Combine both halves into a single master essay
        full_essay = f"{part1_text.strip()}\n\n{part2_text.strip()}".strip()

        # Remove duplicate headlines or directives if any
        full_essay = full_essay.replace(":::artifact", "").replace(":::", "").strip()

        # Extract title/headline
        lines = [line.strip() for line in full_essay.split("\n") if line.strip()]
        headline = lines[0].lstrip("#").strip() if lines else f"The Ultimate Playbook for {topic}"

        # Calculate exact verified word count
        words_list = full_essay.split()
        actual_word_count = len(words_list)
        logger.info(f"Generated Ship 30 essay: {actual_word_count} words ({len(full_essay)} characters)")

        guest_names = list({p.guest for p in retrieval_res.passages if p.guest})

        return {
            "topic": topic,
            "content": full_essay,
            "essay": full_essay,
            "headline": headline,
            "word_count": actual_word_count,
            "guest_references": guest_names or ["Lenny's Podcast Guests"],
            "artifacts": [
                {
                    "title": f"Ship 30 Essay: {headline}",
                    "artifact_type": "markdown",
                    "content": full_essay,
                }
            ],
            "citations": citations,
            "provider": provider,
            "model_name": model_name or "llama3.2",
            "evidence_status": retrieval_res.evidence_status.value,
        }


# Singleton service instance
ship30_service = Ship30SkillService()


def is_ship30_requested(query: str, skill_param: Optional[str] = None) -> bool:
    """Helper preserving backward compatibility."""
    return ship30_service.is_triggered(query, skill_param)
