# Product Requirements Document (PRD)
## Project: The Lenny Growth Assistant
**Author / Role:** Forward Deployed Engineer (FDE)  
**Target Delivery:** October 12, 2026 EOD  
**Status:** **VERIFIED / PRODUCTION READY**  
**Assessment Phase:** Phase 4 — Evaluator Handoff & Deployment  

---

## 1. Executive Summary & Forward Deployment Brief

### 1.1 User & Problem Definition
- **Target User**: Product Managers (PMs), Growth Leads, Founders, and Product Marketing Managers who seek battle-tested product wisdom, frameworks, and growth playbooks.
- **Problem Statement**: Lenny’s Podcast contains thousands of hours of high-signal interviews with world-class product operators (e.g., Shreyas Doshi, Elena Verna, Brian Chesky, Gustaf Alströmer). However:
  1. *Search friction*: Operators cannot easily pinpoint actionable tactics across hundreds of transcript hours.
  2. *Synthesizing burden*: Turning raw interview insights into executive-ready frameworks, launch checklists, or viral essays takes hours of manual synthesis.
  3. *Hallucination risk*: Generic LLM queries generate generic advice instead of the exact, battle-tested methodology shared by specific guest experts.
- **The Solution**: “The Lenny Growth Assistant” (visual identity: **SIGNAL — The Lenny Growth Studio**, *"Turn conversations into clarity."*) is an enterprise-grade conversational AI research and publishing platform that:
  - Ingests and strictly grounds answers in Lenny’s Podcast transcripts with explicit source citations.
  - Automatically structures actionable outputs as native in-app **Artifacts** (Markdown tables, PRD drafts, interactive HTML/CSS mockups).
  - Encodes a specialized **Ship 30 for 30 Skill** to translate deep product conversations into viral, ~1,250-word atomic essays.
  - Offers a zero-code **Model Toggle** between Local LLMs (Ollama `llama3.2` / `qwen2.5:1.5b`), Free-Tier Cloud LLMs (Groq LPU `openai/gpt-oss-20b`), and Enterprise Cloud LLMs (Anthropic Claude / OpenAI).

---

### 1.2 Measurable Success Metrics (Design Targets vs. Validation Status)

| Metric Dimension | Design Target | Evaluated State | Validation Status | Justification |
| :--- | :--- | :--- | :---: | :--- |
| **Grounded Accuracy** | **≥ 95%** of factual assertions supported by transcript excerpts; graceful refusal on out-of-domain queries. | 4/4 passing representative test cases in `backend/tests/test_grounding.py` (Brian Chesky, Elena Verna, Shreyas Doshi, out-of-domain refusal). | **QUALITATIVELY VALIDATED** *(Note: No large-scale automated empirical percentage benchmark has been conducted)* | Builds evaluator trust in factual podcast advice without hallucinations. |
| **Hallucination Mitigation** | Minimize ungrounded claims via strict context anchoring (`EVIDENCE_THRESHOLD = 0.012`). | Model returns explicit `insufficient_evidence` fallback on queries not covered by Lenny's guests. | **VALIDATED PROTOCOL** *(Note: Probabilistic models cannot guarantee absolute zero hallucination)* | Prevents fabricating frameworks not spoken by guests. |
| **Artifact Utility & Formatting** | **≥ 70%** of artifact queries yield a structured document; Ship 30 essays target **1,150–1,350 words**. | Generates atomic essays with 1-3-1 hook rhythm, bold lead-ins, and 7-day tactical checklists (`tests/test_skills_api.py`). | **VALIDATED PATTERN** | Accelerates PM publishing and tactical synthesis. |
| **Local Retrieval Latency** | **< 100ms** hybrid search across entire chunk corpus. | Fast sub-second search using NumPy dot products over 32,209 FastEmbed vectors + BM25Okapi lexical matching. | **DESIGN TARGET** *(Empirical sub-50ms benchmark remains unverified)* | Sub-100ms retrieval ensures instant context delivery to LLM. |
| **Evaluator Container Boot** | **< 2 minutes** to build and boot all 4 services via Docker Compose. | Observed at ~75s on developer workstation with pre-cached Docker layers. | **SINGLE-RUN ESTIMATE** | Zero-friction evaluator setup. |
| **Corpus Acquisition & Indexing** | Quick mode: **< 60s**; Full build disclosed. | Quick mode (`--max-episodes 10`): ~42s. Full index (303 episodes, 32,209 chunks): ~31 minutes on CPU. Requires host Python. | **DOCUMENTED BENCHMARK** | Distinguishes fast container boot from CPU vector embedding. |

---

### 1.3 Architecture Rationale: Login-Free Assessment Design & Session Isolation

To optimize for an evaluator who needs to run and inspect the system quickly, this submission intentionally avoids authentication barriers:
1. **Login-Free by Design**: Requiring user registration, email verification, or third-party OAuth would add unnecessary setup friction and violate the brief's focus on operational simplicity.
2. **Session Context vs. User Accounts**:
   - The application manages **Conversation Sessions** (`sessions` table in PostgreSQL), each maintaining completely independent multi-turn message history, model configurations, and artifacts.
   - User and environment metadata is captured at the conversation turn level (`MessageModel.metadata_payload` JSONB) to track client timestamps, model providers, and skill flags.
   - **Production Roadmap**: In a multi-tenant enterprise deployment, a dedicated `users` table, JWT Bearer authentication, and row-level security (RLS) policies would isolate sessions by tenant ID.

---

### 1.4 Assumptions & Constraints
1. **Transcripts Corpus**: Sourced from the community archive repository ([ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)) for evaluation purposes. Raw transcripts and vector indexes are excluded from Git to respect redistribution rights and avoid repository bloat.
2. **Host Python Required for Ingestion**: Host Python 3.12 is required to run `scripts/download_transcripts.py` and `backend/ingest.py` before launching Docker. Docker Compose mounts `./data` into containers read-only.
3. **Local Environment Viability**: The evaluator can run the demo fully offline using Ollama without needing paid cloud API keys.
4. **Storage Persistence**: PostgreSQL stores sessions, chat messages, artifacts, and metadata.
5. **HTML Security Isolation**: Generated HTML/CSS artifacts are isolated via an empty `sandbox=""` iframe and a strict Content Security Policy (`default-src 'none'`) blocking all scripts and parent DOM access.

---

### 1.5 Scope Choices

#### In Scope (V1 / Submission)
- Full-stack conversational web application (FastAPI backend + Modern React/TypeScript frontend with SIGNAL design system).
- Local Ollama LLM integration (`llama3.2` / `qwen2.5:1.5b`) + Free-Tier Cloud LLM (Groq `openai/gpt-oss-20b`) + Commercial Cloud LLMs (Anthropic Claude / OpenAI GPT-4o).
- Genuine Pi Coding Agent SDK (`@earendil-works/pi-coding-agent@1.1.0`) with sandboxed domain tools.
- Seamless UI model switcher with real-time health indicator and transparent fallback.
- Hybrid transcript search combining FastEmbed dense semantic vectors (NumPy dot product) and BM25Okapi lexical matching with Reciprocal Rank Fusion (RRF).
- Interactive dual-pane **Artifact Studio** with live HTML/CSS sandboxed rendering (`sandbox=""`) and Warm Paper Markdown previews.
- Dedicated **Ship 30 for 30 Content Generation Skill** (atomic essay generator with floating brief modal).
- Multi-session persistence in PostgreSQL.
- Automated API, retrieval, and regression test suites.

#### Intentionally Out of Scope (V1)
- *Multi-tenant user authentication (SSO / OAuth)*: Kept simple to session UUIDs to reduce evaluation setup friction.
- *Voice audio ingestion*: Transcripts are pre-ingested rather than raw audio parsing to prioritize latency and stability.
- *Fine-tuning*: RAG and in-context skills provide superior accuracy, freshness, and citation traceability compared to fine-tuning.

---

### 1.6 Risks & Trade-Offs Matrix

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Hallucination on unmentioned topics** | High | Grounding protocol strictly returns `insufficient_evidence` when topics are unmentioned, with prompt instructions to refuse rather than invent. |
| **Local model token limit / context truncation** | Medium | Smart transcript chunking (overlapping 180-word conversational chunks with guest metadata) + hybrid retrieval (FastEmbed + BM25 combined via RRF). |
| **Untrusted HTML execution in Artifact Viewer** | Critical | Render HTML inside an isolated `iframe` with `sandbox=""` (empty sandbox blocking all scripts, parent DOM access, and forms) and restrictive Content Security Policy (`default-src 'none'`). |
| **Cloud API cost & rate limits** | Low | Defaults to local Ollama and free-tier Groq Cloud; fallback logic handles rate limits gracefully with user notification. |
| **Cold start / Ollama daemon latency** | Medium | Backend startup health-check probes Ollama endpoint and warms up model cache on boot. |

---

## 2. User Journeys & Interaction Flows

### Journey 1: Tactical PM Research & Grounded Retrieval
1. **User Entry**: User opens the web application (`http://localhost:5173`), landing on the SIGNAL research desk with Warm Paper canvas.
2. **Prompt Dispatch**: User clicks a starter prompt (e.g., *"What did Brian Chesky say about founder mode?"*) or types a custom question into the prompt composer.
3. **Hybrid RAG Execution**:
   - Backend evaluates query across 32,209 chunks using FastEmbed dense vectors and BM25Okapi lexical scoring.
   - If non-stopword query overlap meets `EVIDENCE_THRESHOLD = 0.012`, top passages are synthesized into the LLM context.
4. **Citation Rendering**: The response streams in, accompanied by cassette-styled Source Tape cards displaying the guest name, episode title, and timestamped YouTube link (`&t={s}s`).
5. **Refusal Path**: If the user asks about an unmentioned subject (e.g., quantum chromodynamics), the system displays an explicit refusal notice indicating Lenny has not covered the topic.

### Journey 2: Ship 30 for 30 Long-Form Essay Generation
1. **Modal Brief**: User clicks *"Write a Ship 30 essay"* or presses `Alt+S` to open the Ship 30 writing modal.
2. **Topic & Hook Selection**: User enters a topic or selects an editorial hook card (e.g., *"Founder Mode vs Manager Mode by Brian Chesky"*).
3. **Skill Execution**: Backend invokes `ship30_skill.py`, combining relevant transcript evidence with Dickie Bush & Nicolas Cole's 1-3-1 hook cadence, bold lead-ins, and actionable 7-day checklists.
4. **Studio Publication**: The resulting ~1,250-word essay is extracted into the right-hand **Artifact Studio**, rendered in editorial serif prose with real-time word count and markdown download.

### Journey 3: Artifact Inspection & Sandboxed HTML Preview
1. **Artifact Generation**: An agentic or direct query requesting interactive UI generates an HTML artifact block.
2. **Extraction & Splitting**: `artifact_extractor.py` detects the artifact directive, stores it in PostgreSQL, and pops open the right panel.
3. **Tab Toggle**: User toggles between **Preview** and **Source** tabs.
4. **Security Isolation**: In Preview mode, content is injected into an `iframe` with `sandbox=""` and `CSP: default-src 'none'`. All JavaScript execution and DOM access are strictly prohibited.
5. **Clipboard & Export**: User copies clean markdown or downloads the raw asset.

---

## 3. Acceptance Criteria

- **AC-1 (Grounded Retrieval & Citations)**: All factual claims must be attributable to transcript passages. Each citation card must contain guest name, episode title, and verified YouTube link with timestamp.
- **AC-2 (Graceful Refusal on Missing Evidence)**: Queries covering unmentioned topics must return `insufficient_evidence` without fabricating guest names or quotes.
- **AC-3 (Multi-Provider Model Switching)**: The UI header model dropdown must allow switching between Local Ollama (`llama3.2`, `qwen2.5:1.5b`) and Cloud Groq (`openai/gpt-oss-20b`) without restarting the server.
- **AC-4 (Authentic Pi Agent SDK Execution)**: The agent microservice must run using `@earendil-works/pi-coding-agent@1.1.0` with shell/file tools disabled (`noTools: "all"`).
- **AC-5 (Ship 30 for 30 Essay Generation)**: Triggering the Ship 30 skill must produce structured atomic essays adhering to the 1-3-1 cadence with bold lead-ins and guest citations.
- **AC-6 (Secure Sandboxed Artifact Rendering)**: HTML artifacts rendered in `ArtifactViewer.tsx` must utilize `sandbox=""` and CSP `default-src 'none'`.
- **AC-7 (PostgreSQL Persistence)**: Conversations, messages, citations, artifacts, and user/turn metadata must persist across browser reloads.
- **AC-8 (Observability & Diagnostics)**: Backend requests must include `X-Request-ID` correlation, route latency logging in milliseconds, and comprehensive health status via `/api/v1/health`.

---

## 4. Implementation Plan & Completed Milestones

- **Phase 1: Knowledge Pipeline & Ingestion Engine** *(COMPLETED)*
  - 303 episodes parsed, 62,272 turns extracted, 32,209 chunks indexed with FastEmbed (`bge-small-en-v1.5`) and BM25Okapi.
- **Phase 2: Hybrid RAG & Grounded Chat API** *(COMPLETED)*
  - FastAPI `/api/v1/chat` and `/api/v1/retrieval/search` endpoints with RRF reranking and evidence thresholds.
- **Phase 3: Database Persistence & Docker Topology** *(COMPLETED)*
  - PostgreSQL 16 schema with async SQLAlchemy, session cascades, and Docker Compose 4-service topology.
- **Phase 4: Agent SDK & Editorial UI Transformation** *(COMPLETED)*
  - Integration of `@earendil-works/pi-coding-agent@1.1.0` daemon, sandboxed tools, and SIGNAL Warm Paper editorial design system.
- **Phase 5: Secure Release & Evaluator Verification** *(COMPLETED)*
  - Clean GitHub release under `HARSHAN-J-OFFICIAL/lenny-growth-assistant` with zero credential leaks and automated test suites.

---

## 5. Non-Functional Requirements & Observability

- **Performance**: Sub-second local retrieval; TTFT < 3.5s on local Ollama; instant Groq cloud inference.
- **Reliability**: Graceful degradation when Ollama daemon or Cloud API is offline, falling back cleanly.
- **Observability**: Formatted standard text logging with microsecond timestamps, `[request_id]` correlation tokens, endpoint path, HTTP status, and duration in milliseconds.
