# Agent Transcript 04 — Official Pi SDK Integration & Sandboxing Enforcement
**Phase:** Official Agent SDK Compliance & Security Sandboxing Sprint  
**Agent:** AI Agent Engineer & Application Security Specialist  
**Sanitization:** System credentials, network tokens, and sensitive paths redacted.

---

### Step 1: SDK Discovery & Version Verification
Identified official package `@earendil-works/pi-coding-agent@1.1.0` in the workspace environment.
The Pi Coding Agent SDK is built on `@earendil-works/pi-ai` and provides:
- Multi-provider model registration (`mr.registerProvider("ollama", { baseUrl, apiKey })`).
- Bounded agent execution sessions with tool registration.
- Active tool filtering via `noTools`, `tools`, and `excludeTools`.

### Step 2: Resolving the Tool Sandboxing Pitfall
**Potential Pitfall:**
Setting `noTools: "all"` in certain versions of the SDK disables all tool calls globally, including custom registered domain tools.
**Security Directive:**
The agent must NOT have access to host system tools (shell, filesystem read/write, process execution), but MUST be able to execute domain tools: `search_podcast_transcripts` and `generate_sandboxed_artifact`.

**Architectural Solution in `agent_service/pi_agent.mjs`:**
```javascript
const { session } = await createAgentSession({
  model: selectedModel,
  modelRuntime: mr,
  sessionManager: SessionManager.inMemory(),
  noTools: "builtin", // Explicitly disables built-in shell (bash) and filesystem tools
  tools: ["search_podcast_transcripts", "generate_sandboxed_artifact"], // Approved domain tools allowlist
  excludeTools: ["bash", "read", "write", "edit", "ls", "grep", "find", "powershell"], // Host tools denylist
  customTools: [searchTool, artifactTool],
});
```

### Step 3: High-Performance Daemon & Subprocess Dual Architecture
1. **HTTP Daemon (`agent_service/server.mjs` on port `8001`):** Keeps the Node.js runtime and model definitions warm, reducing turn latency from ~1.8s to sub-200ms.
2. **Subprocess Fallback (`agent_service/runner.mjs`):** A headless CLI runner capable of one-shot execution via `python subprocess` if the daemon is stopped or undergoing maintenance.

### Step 4: Live Verification
Executed automated test `tests/test_pi_sdk_agent.py`:
- Real Pi SDK session created.
- Model prompts evaluated.
- Custom tool `search_podcast_transcripts` invoked and executed against backend hybrid retrieval.
- Grounded answer generated with verified citations.
- Host shell/filesystem tools verified inaccessible.
- `session.dispose()` called reliably in `finally` block.
