/**
 * CLI Runner for Pi Coding Agent SDK
 * Reads JSON input from a file or stdin, executes agent turn, and outputs JSON.
 */

import fs from "node:fs";
import { runPiAgentExecution } from "./pi_agent.mjs";

async function main() {
  let rawInput = "";

  const fileIdx = process.argv.indexOf("--file");
  const argIdx = process.argv.indexOf("--input");

  if (fileIdx !== -1 && process.argv[fileIdx + 1]) {
    rawInput = fs.readFileSync(process.argv[fileIdx + 1], "utf8");
  } else if (argIdx !== -1 && process.argv[argIdx + 1]) {
    rawInput = process.argv[argIdx + 1];
  } else {
    // Read from stdin
    const chunks = [];
    for await (const chunk of process.stdin) {
      chunks.push(chunk);
    }
    rawInput = Buffer.concat(chunks).toString("utf8");
  }

  if (!rawInput.trim()) {
    console.error(JSON.stringify({ error: "No input payload provided" }));
    process.exit(1);
  }

  const payload = JSON.parse(rawInput);
  const result = await runPiAgentExecution({
    message: payload.message,
    modelName: payload.model_name || "llama3.2",
    provider: payload.model_provider || "ollama",
    fastApiUrl: payload.fastapi_url || process.env.FASTAPI_URL || "http://127.0.0.1:8000",
    timeoutMs: payload.timeout_ms || 90000,
  });

  console.log(JSON.stringify(result));
}

main().catch((err) => {
  console.error(JSON.stringify({ error: err.message, stack: err.stack }));
  process.exit(1);
});
