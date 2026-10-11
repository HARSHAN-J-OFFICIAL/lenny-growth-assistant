import { createAgentSession, ModelRuntime, SessionManager } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

async function runTest() {
  console.log("Initializing ModelRuntime...");
  const mr = await ModelRuntime.create();
  mr.registerProvider("ollama", {
    baseUrl: "http://127.0.0.1:11434/v1",
    api: "openai-completions",
    apiKey: "ollama",
    models: [
      { id: "llama3.2", name: "Llama 3.2 3B", contextWindow: 8192, input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 } },
      { id: "qwen2.5:1.5b", name: "Qwen 2.5 1.5B", contextWindow: 8192, input: ["text"], cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 } }
    ]
  });

  const searchTool = {
    name: "search_podcast_transcripts",
    label: "Search Lenny Transcripts",
    description: "Search indexed podcast transcripts from Lenny's Podcast for insights and quotes.",
    parameters: Type.Object({
      query: Type.String({ description: "Search query about product management, growth, or startups" })
    }),
    execute: async (toolCallId, params) => {
      console.log(`[Tool Executed] search_podcast_transcripts with query: "${params.query}"`);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              query: params.query,
              results: [
                {
                  guest: "Elena Verna",
                  title: "Product-Led Growth & B2B Growth Strategy",
                  content: "Product-led growth is an go-to-market motion where user acquisition, expansion, and retention are driven primarily by the product itself.",
                  timestamp_url: "https://youtu.be/test?t=120"
                }
              ]
            })
          }
        ],
        details: { count: 1 }
      };
    }
  };

  console.log("Creating Agent Session with genuine Pi Coding Agent SDK...");
  const { session } = await createAgentSession({
    model: mr.getModel("ollama", "llama3.2"),
    modelRuntime: mr,
    sessionManager: SessionManager.inMemory(),
    noTools: "all",
    tools: ["search_podcast_transcripts"],
    customTools: [searchTool],
  });

  console.log("Active tool names:", session.getActiveToolNames());

  session.subscribe((event) => {
    if (event.type === "message_end") {
      console.log("MESSAGE_END payload:", JSON.stringify(event.message, null, 2));
    }
  });

  try {
    console.log("\nPrompting agent with a quick query...");
    await session.prompt("In 2 short sentences, what is Product-Led Growth according to Elena Verna?");
    console.log("\n--- Final Assistant Output ---");
    console.log(session.getLastAssistantText());
  } finally {
    session.dispose();
    console.log("\nSession disposed.");
  }
}

runTest().catch((err) => {
  console.error("Test failed:", err);
  process.exit(1);
});
