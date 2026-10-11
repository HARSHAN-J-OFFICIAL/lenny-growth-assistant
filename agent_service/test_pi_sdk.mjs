import { createAgentSession, SessionManager } from "@earendil-works/pi-coding-agent";

async function main() {
  console.log("Testing createAgentSession from @earendil-works/pi-coding-agent...");
  try {
    const { session } = await createAgentSession({
      sessionManager: SessionManager.inMemory(),
      noTools: "all",
      tools: [],
    });
    console.log("Session created successfully:", Boolean(session));
    if (session) {
      session.dispose();
      console.log("Session disposed successfully.");
    }
  } catch (err) {
    console.error("Error creating session:", err);
  }
}

main();
