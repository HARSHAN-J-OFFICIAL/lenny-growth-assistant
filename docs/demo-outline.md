# Video Demonstration Outline — The Lenny Growth Assistant
**Target Duration:** 2 minutes 45 seconds (Camera-enabled YouTube demonstration)  
**Presenter:** Forward Deployed Engineer / AI Solutions Architect  
**Objective:** Provide a fast-paced, high-density walkthrough of the live application running on local Ollama, demonstrating transcript grounding, verifiable citations, session persistence, the Ship 30 writing skill, and the sandboxed artifact viewer.

---

## Chronological Demo Script (00:00 – 02:45)

### 1. The Business Problem & Product Overview (00:00 – 00:25 | 25s)
- **Visual:** Presenter on camera + Fullscreen switch to SIGNAL — The Lenny Growth Studio interface (`http://localhost:5173`).
- **Spoken:** 
  > *"Product managers and startup founders make million-dollar decisions daily, yet the world's most tactical product wisdom is locked away in hundreds of hours of conversational podcast audio. Most generic AI chatbots hallucinate generic advice without verifiable source evidence. This is SIGNAL — The Lenny Growth Studio: an executive AI workspace grounded in 303 complete Lenny's Podcast episodes, powered by a hybrid retrieval engine, the official Pi Coding Agent SDK, and local Ollama execution."*
- **Screen Action:** Point out the distinctive Deep Slate and Warm Paper 3-panel layout, the active session indicators, and the status bar showing 303 episodes / 32,209 indexed chunks.

---

### 2. Live Grounded Query & Source Tapes (00:25 – 00:55 | 30s)
- **Visual:** Chat Composer.
- **Screen Action:** Type and submit: *"What does Elena Verna recommend about product-led growth?"*
- **Spoken:**
  > *"Let's ask about Elena Verna's product-led growth playbook. Notice how the agent executes a hybrid semantic and BM25 search over the 303 episodes. Within seconds, we receive a tactical, grounded answer detailing pipeline accountability and retention loops."*
- **Screen Action:** Expand the **Source Tapes** tray for episode *"Elena Verna 2.0"*, showing the exact guest badge, raw RRF score (`RRF: 0.0302`), and click the YouTube timestamp link (`https://www.youtube.com/...&t=407s`) to show the video opening at the exact quotation moment.
- **Spoken:**
  > *"Every assertion is anchored in verifiable podcast evidence. Clicking this timestamp link opens YouTube directly at second 407 where Elena speaks these exact words."*

---

### 3. Conversational Continuity & Multi-Turn Session Persistence (00:55 – 01:25 | 30s)
- **Visual:** Chat thread.
- **Screen Action:** Type follow-up: *"What is her advice on retention loops versus acquisition?"*
- **Spoken:**
  > *"We ask a contextual follow-up. The assistant maintains conversational memory across turns. Now watch: I'll rename this session to 'PLG Executive Strategy' and hit refresh on the browser."*
- **Screen Action:** Inline rename conversation via pencil icon to `'PLG Executive Strategy'`, press Enter, then press `F5` / hard reload.
- **Spoken:**
  > *"Upon reload, the session title, full chat history, citations, and model metadata immediately restore from our Docker PostgreSQL database."*

---

### 4. Local Ollama & Cloud Provider Switching (01:25 – 01:45 | 20s)
- **Visual:** Header Model Switcher dropdown.
- **Screen Action:** Click the Model Selector; toggle from `llama3.2` to `qwen2.5:1.5b` or demonstrate the live Groq Cloud toggle (`openai/gpt-oss-20b`).
- **Spoken:**
  > *"The assistant supports seamless local and cloud provider routing. Right here, we can switch between Llama 3.2 and Qwen 2.5 running on our local Ollama daemon, or route to Groq Cloud for ultra-fast free cloud inference. Cloud providers like OpenAI and Anthropic are also integrated with transparent fallback if unconfigured."*

---

### 5. Ship 30 Writing Engine & Sandboxed Artifact Studio (01:45 – 02:25 | 40s)
- **Visual:** Header "Ship 30 Essay" button.
- **Screen Action:** Click "Ship 30 Essay" button in header. Select topic *"Finding Product-Market Fit in B2B SaaS"* and click *"Generate & Save Artifact"*.
- **Spoken:**
  > *"Now let's demonstrate our specialized writing skill: the Ship 30 for 30 digital writing engine. The assistant retrieves relevant insights from Todd Jackson and Geoff Moore, and generates a structured, ~1,250-word atomic essay with a 1-3-1 hook, bold lead-ins, grounded pillars, and an actionable 7-day checklist."*
- **Screen Action:** Show the essay appearing in the right-hand **Artifact Studio**:
  1. Toggle between **Warm Paper Preview** and **Source** (`<pre><code>`).
  2. Click **Copy** button (showing the emerald checkmark feedback).
  3. Click **Download** button.
  4. Drag the horizontal resizing handle to expand the artifact pane.
- **Spoken:**
  > *"The essay opens in our sandboxed Artifact Studio. The viewer runs inside an iframe with an empty sandbox attribute and a strict Content Security Policy, completely neutralizing script execution and external network leaks while keeping rendering pristine."*

---

### 6. Architectural Trade-Off & Conclusion (02:25 – 02:45 | 20s)
- **Visual:** Presenter on camera + Architecture diagram in `docs/architecture.md`.
- **Spoken:**
  > *"One key architectural trade-off we made was using a pre-computed hybrid RRF index rather than an online vector database service like Pinecone. This allowed zero cloud egress costs, 100% offline local privacy for PMs, and sub-50ms retrieval latency across all 32,209 chunks.*
  > 
  > *SIGNAL is fully containerized, tested across 88 backend automated tests and 24 Chrome end-to-end workflows, and ready for production deployment. Thank you!"*

---

## Production Recording Checklist
- [ ] Screen resolution set to 1920x1080 (1080p).
- [ ] Docker PostgreSQL and local Ollama daemon verified running beforehand.
- [ ] Clean test session initialized in the UI.
- [ ] Browser zoom level set to 100% with dark mode active.
- [ ] Audio input checked for clear vocal quality with minimal background noise.
- [ ] Strictly adhere to the 2m 45s target duration.
