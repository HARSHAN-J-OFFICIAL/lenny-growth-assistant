/**
 * Lightweight HTTP server for Pi Coding Agent SDK Service
 * Listens on port 8001 by default.
 */

import http from "node:http";
import { runPiAgentExecution } from "./pi_agent.mjs";

const PORT = parseInt(process.env.AGENT_SERVICE_PORT || "8001", 10);

const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  // Health endpoint
  if (req.method === "GET" && url.pathname === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        status: "ok",
        service: "lenny-pi-agent-service",
        sdk: "@earendil-works/pi-coding-agent",
        version: "1.1.0",
        timestamp: new Date().toISOString(),
      })
    );
    return;
  }

  // Chat endpoint
  if (req.method === "POST" && url.pathname === "/chat") {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });

    req.on("end", async () => {
      try {
        const payload = JSON.parse(body || "{}");
        if (!payload.message) {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: "Missing required 'message' field" }));
          return;
        }

        const result = await runPiAgentExecution({
          message: payload.message,
          modelName: payload.model_name || "llama3.2",
          provider: payload.model_provider || "ollama",
          fastApiUrl: payload.fastapi_url || process.env.FASTAPI_URL || "http://127.0.0.1:8000",
          timeoutMs: payload.timeout_ms || 90000,
        });

        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(result));
      } catch (err) {
        console.error("[Pi Agent Server] Error handling request:", err);
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: err.message, stack: err.stack }));
      }
    });
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Not Found" }));
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`[Pi Agent Server] Listening on http://127.0.0.1:${PORT}`);
});
