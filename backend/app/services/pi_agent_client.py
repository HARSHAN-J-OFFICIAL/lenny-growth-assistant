"""
Pi Coding Agent SDK Client & Process Bridge.
Coordinates execution of the official @earendil-works/pi-coding-agent SDK service,
supporting both HTTP daemon dispatch and direct Node.js subprocess fallback.
"""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.agent_orchestrator import AgentExecutionResult
from app.services.artifact_extractor import ExtractedArtifact

logger = logging.getLogger("lenny.agent.pi_client")

AGENT_SERVICE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "agent_service"
AGENT_SERVICE_URL = os.environ.get("AGENT_SERVICE_URL", "http://127.0.0.1:8001")


class PiAgentClient:
    """Client for genuine @earendil-works/pi-coding-agent SDK execution."""

    def __init__(self, service_url: str = AGENT_SERVICE_URL, service_dir: Path = AGENT_SERVICE_DIR):
        self.service_url = service_url
        self.service_dir = service_dir

    async def is_service_alive(self) -> bool:
        """Check if HTTP daemon is active."""
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{self.service_url}/health")
                return res.status_code == 200
        except Exception:
            return False

    async def run(
        self,
        message: str,
        provider: str = "ollama",
        model_name: Optional[str] = None,
        skill: Optional[str] = None,
        timeout_seconds: float = 90.0,
    ) -> AgentExecutionResult:
        """
        Execute request via genuine Pi Coding Agent SDK.
        First attempts HTTP worker; falls back to Node subprocess.
        """
        payload = {
            "message": message,
            "model_provider": provider or "ollama",
            "model_name": model_name or settings.OLLAMA_DEFAULT_MODEL,
            "skill": skill,
            "fastapi_url": f"http://127.0.0.1:{settings.PORT if hasattr(settings, 'PORT') else 8000}",
            "timeout_ms": int(timeout_seconds * 1000),
        }

        # Attempt 1: HTTP Worker (fast check with 1.0s connect timeout)
        try:
            http_timeout = httpx.Timeout(timeout_seconds, connect=1.0)
            async with httpx.AsyncClient(timeout=http_timeout) as client:
                logger.info(f"Dispatching to Pi Agent HTTP service at {self.service_url}/chat...")
                response = await client.post(f"{self.service_url}/chat", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_result(data, provider, model_name)
                else:
                    logger.warning(f"Pi Agent HTTP service returned {response.status_code}: {response.text}")
        except httpx.ConnectError:
            logger.info("Pi Agent HTTP server not reachable; running via Node.js runner subprocess...")
        except Exception as e:
            logger.warning(f"Pi Agent HTTP call failed: {e}; falling back to Node.js subprocess...")

        # Attempt 2: Node.js Subprocess Fallback
        return await self._run_subprocess(payload, timeout_seconds)

    async def _run_subprocess(self, payload: Dict[str, Any], timeout_seconds: float) -> AgentExecutionResult:
        """Execute runner.mjs directly via Node.js subprocess using temp JSON file for Windows compatibility."""
        import tempfile

        runner_file = self.service_dir / "runner.mjs"
        if not runner_file.exists():
            raise FileNotFoundError(f"Pi Agent runner not found at {runner_file}")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(payload, f)
            temp_path = f.name

        try:
            cmd = ["node", str(runner_file), "--file", temp_path]
            logger.info(f"Running Pi Agent subprocess with file {temp_path} in {self.service_dir}...")

            env = os.environ.copy()
            if settings.GROQ_API_KEY:
                env["GROQ_API_KEY"] = settings.GROQ_API_KEY
            if settings.GROQ_MODEL:
                env["GROQ_MODEL"] = settings.GROQ_MODEL
            if settings.GROQ_BASE_URL:
                env["GROQ_BASE_URL"] = settings.GROQ_BASE_URL
            if settings.OPENAI_API_KEY:
                env["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            if settings.ANTHROPIC_API_KEY:
                env["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
            if settings.ANTHROPIC_DEFAULT_MODEL:
                env["ANTHROPIC_DEFAULT_MODEL"] = settings.ANTHROPIC_DEFAULT_MODEL

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.service_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)

            if proc.returncode != 0:
                err_msg = stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"Pi Agent SDK failed with code {proc.returncode}: {err_msg}")

            out_str = stdout.decode("utf-8", errors="replace").strip()
            data = json.loads(out_str)
            return self._parse_result(data, payload["model_provider"], payload["model_name"])
        except asyncio.TimeoutError:
            proc.kill()
            raise TimeoutError(f"Pi Agent SDK subprocess timed out after {timeout_seconds}s")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def _parse_result(self, data: Dict[str, Any], provider: str, model_name: Optional[str]) -> AgentExecutionResult:
        """Parse raw response from Pi Agent SDK into standard AgentExecutionResult."""
        raw_artifacts = data.get("artifacts", [])
        parsed_artifacts = [
            ExtractedArtifact(
                title=a.get("title", "Growth Artifact"),
                artifact_type=a.get("artifact_type", "markdown"),
                content=a.get("content", ""),
            )
            for a in raw_artifacts
        ]

        raw_content = (data.get("content") or "").strip()
        citations = data.get("citations", [])

        if not raw_content or raw_content == "No response generated by agent.":
            if citations:
                top_guest = citations[0].get("guest") or "Lenny's Podcast Guest"
                ep_title = citations[0].get("episode_title") or "the episode"
                raw_content = (
                    f"Based on Lenny's Podcast transcripts, relevant discussions were found featuring **{top_guest}** "
                    f"in \"{ep_title}\". Please refer to the verified source citations below."
                )
            else:
                raw_content = (
                    "I couldn't find evidence regarding this topic in the available Lenny's Podcast transcripts. "
                    "Could you share more context, the full name, or the specific episode you're referring to?"
                )

        return AgentExecutionResult(
            content=raw_content,
            citations=citations,
            artifacts=parsed_artifacts,
            tool_calls_trace=data.get("tool_calls_trace", []),
            provider=data.get("provider", provider),
            model_name=data.get("model_name", model_name or "llama3.2"),
            evidence_status=data.get("evidence_status", "sufficient" if citations else "insufficient"),
            notice=data.get("notice") or f"Executed via genuine Pi Coding Agent SDK ({data.get('sdk_version', '1.1.0')})",
        )


pi_agent_client = PiAgentClient()
