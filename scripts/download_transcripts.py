"""
Transcript Acquisition Script for The Lenny Growth Assistant.

Retrieves official transcripts from the open community repository:
https://github.com/ChatPRD/lennys-podcast-transcripts

Usage:
    python scripts/download_transcripts.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/ChatPRD/lennys-podcast-transcripts.git"
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = WORKSPACE_ROOT / "data" / "transcripts"


def main():
    print("=================================================================")
    print("  Lenny Growth Assistant — Transcript Acquisition Tool")
    print("=================================================================")
    print(f"Target directory: {TARGET_DIR}")

    episodes_dir = TARGET_DIR / "episodes"
    if episodes_dir.exists() and any(episodes_dir.iterdir()):
        count = len(list(episodes_dir.glob("*/transcript.md")))
        print(f"✓ Transcripts already present! Found {count} episodes in {episodes_dir}.")
        print("  To re-index: python backend/ingest.py")
        return

    print(f"Acquiring transcripts from {REPO_URL}...")
    try:
        # Check if git is available
        subprocess.run(["git", "--version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("ERROR: Git is not installed or not in PATH.")
        print(f"Please clone manually: git clone {REPO_URL} data/transcripts")
        sys.exit(1)

    TARGET_DIR.parent.mkdir(parents=True, exist_ok=True)

    if TARGET_DIR.exists() and not (episodes_dir.exists()):
        print("Directory data/transcripts exists but episodes folder is missing. Cloning to temp...")
        temp_dir = WORKSPACE_ROOT / "data" / "transcripts_temp"
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", REPO_URL, str(temp_dir)],
                check=True,
            )
            # Copy episodes and index
            if (temp_dir / "episodes").exists():
                shutil.copytree(temp_dir / "episodes", TARGET_DIR / "episodes", dirs_exist_ok=True)
            if (temp_dir / "index").exists():
                shutil.copytree(temp_dir / "index", TARGET_DIR / "index", dirs_exist_ok=True)
            print("✓ Transcripts successfully acquired!")
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(TARGET_DIR)],
            check=True,
        )
        print("✓ Transcripts successfully cloned into data/transcripts!")

    episode_count = len(list((TARGET_DIR / "episodes").glob("*/transcript.md")))
    print(f"✓ Successfully verified {episode_count} episode transcripts.")
    print("Next step: Run `python backend/ingest.py` to build the hybrid search index.")


if __name__ == "__main__":
    main()
