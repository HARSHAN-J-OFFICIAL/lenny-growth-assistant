"""
CLI tool for ingesting Lenny's Podcast transcripts into the hybrid knowledge base.
Usage:
    python ingest.py                     # Index all 303 episodes
    python ingest.py --max-episodes 10   # Index first 10 episodes for testing
    python ingest.py --status            # Show current index status
"""

import argparse
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.ingestion_manager import ingestion_manager


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Lenny's Podcast transcripts into hybrid RAG index.")
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=None,
        help="Maximum number of episodes to index (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild index even if existing index is present",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check and display current index status without re-indexing",
    )
    args = parser.parse_args()

    if args.status:
        ingestion_manager.initialize()
        status = ingestion_manager.get_status()
        print("\n=== Lenny Knowledge Base Status ===")
        print(f"State: {status.ingestion_state}")
        print(f"Indexed Episodes: {status.indexed_episodes_count}")
        print(f"Indexed Chunks:   {status.indexed_chunks_count}")
        print(f"Indexed Topics:   {status.indexed_topics_count}")
        print(f"Embedding Model:  {status.embedding_model} (dim={status.vector_dim})")
        print(f"Storage Size:     {status.index_storage_bytes / (1024 * 1024):.2f} MB")
        print(f"Last Indexed At:  {status.last_indexed_at}")
        if status.warnings:
            print(f"Warnings:         {status.warnings}")
        return

    print("=================================================================")
    print("  Lenny Growth Assistant — Knowledge Ingestion & Index Pipeline")
    print("=================================================================")
    if args.max_episodes:
        print(f"Indexing mode: Subset ({args.max_episodes} episodes)")
    else:
        print("Indexing mode: Full Dataset (all 303 episodes)")

    t0 = time.perf_counter()
    result = ingestion_manager.ingest_dataset(
        max_episodes=args.max_episodes,
        force_rebuild=args.force,
    )
    total_time = round(time.perf_counter() - t0, 2)

    if result.get("status") == "error":
        print("\n[ERROR] Ingestion Failed!")
        print(f"Detail: {result.get('message', 'Transcript corpus not found.')}")
        print("\nAction Required:")
        print("1. Acquire the open transcripts corpus by running:")
        print("   python scripts/download_transcripts.py")
        print("2. Or manually clone the dataset:")
        print("   git clone https://github.com/ChatPRD/lennys-podcast-transcripts data/transcripts")
        print("3. Then re-run this command: python ingest.py\n")
        sys.exit(1)

    print("\n---------------- Ingestion Summary ----------------")
    print(f"Status:            {result.get('status')}")
    print(f"Episodes Indexed:  {result.get('indexed_episodes')}")
    print(f"Chunks Indexed:    {result.get('indexed_chunks')}")
    print(f"Topics Mapped:     {result.get('indexed_topics')}")
    print(f"Execution Time:    {total_time}s ({result.get('duration_sec')}s internal)")
    print(f"Storage Location:  {result.get('storage_dir')}")
    print("---------------------------------------------------\n")

    # Run a quick sanity search
    print("[Verification] Testing search query...")
    test_query = "What are the key metrics for product-market fit?"
    search_res = ingestion_manager.retriever.search(test_query, top_k=3)
    print(f"Query: '{test_query}'")
    print(f"Evidence Status: {search_res.evidence_status.value}")
    print(f"Retrieved Passages: {len(search_res.passages)}")
    for i, p in enumerate(search_res.passages, 1):
        print(f"  [{i}] {p.guest} ({p.episode_title}) [RRF: {p.score:.4f}]")
        print(f"      Citation URL: {p.timestamp_url}")
        print(f"      Text: {p.text[:120]}...\n")


if __name__ == "__main__":
    main()
