"""
Pi Coding Agent SDK Architectural Evaluation & Compatibility Bridge.

Architectural Analysis:
- Evaluation: The Pi Coding Agent SDK (@earendil-works/pi-coding-agent) is an open-source,
  minimalist Node.js / TypeScript agent harness.
- Runtime Compatibility: Because the core application backend is a Python 3.12 / FastAPI
  server running with SQLAlchemy 2.0 and native FastEmbed ONNX, running Node.js CLI processes
  in-process is not natively supported without cross-process IPC.
- Security & Sandboxing: Pi Coding Agent natively provides filesystem (read/write/edit)
  and shell execution (bash) capabilities. In accordance with Requirement 8:
  "Disable all unnecessary filesystem and shell-execution tools in user-facing agent sessions",
  all user sessions must strictly disallow arbitrary shell execution and host file mutations.
- Architecture Decision:
  1. The core backend utilizes a native, zero-overhead Python Agent Orchestrator
     (app.services.agent_orchestrator.AgentOrchestrator) implementing tool-calling loops,
     strictly sandboxed domain tools, and multi-provider model routing.
  2. This PiAgentBridge provides an RPC/protocol adapter allowing external Pi Agent instances
     or developer tooling to query the Lenny Growth Assistant knowledge base safely without
     exposing unsandboxed host primitives.
"""

import logging
from typing import Any, Dict, List, Optional
from app.services.agent_tools import (
    AGENT_TOOL_SCHEMAS,
    execute_agent_tool,
    verify_sandboxing,
    SecuritySandboxingViolation,
)

logger = logging.getLogger("lenny.pi_agent_bridge")


class PiAgentCompatibilityBridge:
    """
    Protocol adapter providing Pi Agent SDK-compliant tool specifications
    and sandboxed execution for external or subprocess RPC invocations.
    """

    def __init__(self):
        # Verify that all tools comply with sandboxing policies
        verify_sandboxing()
        self.registered_schemas = AGENT_TOOL_SCHEMAS

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return tool declarations formatted for agent orchestration.
        Guaranteed to contain zero shell or filesystem tools.
        """
        return self.registered_schemas

    def handle_rpc_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an RPC tool call dispatched by an agent orchestrator.
        Enforces strict sandboxing rules.
        """
        try:
            result = execute_agent_tool(tool_name=tool_name, arguments=parameters)
            return {
                "status": "success",
                "tool": tool_name,
                "result": result,
            }
        except SecuritySandboxingViolation as sec_err:
            logger.error(f"Sandboxing violation blocked: {sec_err}")
            return {
                "status": "security_violation",
                "tool": tool_name,
                "error": str(sec_err),
            }
        except Exception as exc:
            logger.error(f"Tool execution failed for '{tool_name}': {exc}")
            return {
                "status": "error",
                "tool": tool_name,
                "error": str(exc),
            }


# Singleton instance for system-wide access
pi_agent_bridge = PiAgentCompatibilityBridge()
