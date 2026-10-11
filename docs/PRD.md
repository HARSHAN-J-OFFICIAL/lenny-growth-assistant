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

### 1.2 Measurable Success Metrics

| Metric Dimension | Success Metric Target | Justification |
| :--- | :--- | :--- |
| **Grounded Accuracy** | **≥ 95%** of factual claims include verified transcript citations; **0%** unsupported hallucinations (model explicitly states when context is missing). | Builds client trust in executive decision-making. |
| **Artifact Utility** | **≥ 70%** of artifact queries yield a rendered view without requiring external tooling. | Measures workflow speedup for PMs generating docs. |
| **Local Inference Latency** | **< 3.5s** Time to First Token (TTFT) on local Ollama running on standard developer workstation. | Ensures a responsive, pleasant local evaluation experience. |
| **Evaluator Time-to-Run** | **< 5 minutes** from fresh `git clone` to fully interactive local app via single command. | Core Forward Deployed operational standard. |

---

### 1.3 Assumptions & Constraints
1. **Transcripts Corpus**: Utilizing the canonical open-source transcript repository from ChatPRD (`ChatPRD/lennys-podcast-transcripts`).
2. **Local Environment Mandatory**: The evaluator must be able to run the demo fully offline using Ollama without needing paid cloud API keys.
3. **Storage Persistence**: PostgreSQL (compatible with local Postgres Docker, Supabase, or Railway) stores sessions, chat messages, artifacts, and query logs.
4. **HTML Security Isolation**: Generated HTML/CSS artifacts must be treated as untrusted and isolated via sandboxed iframes (`sandbox=""`) with restrictive CSP to prevent Cross-Site Scripting (XSS).

---

### 1.4 Scope Choices

#### In Scope (V1 / Submission)
- Full-stack conversational web application (FastAPI backend + Modern React/TypeScript frontend with SIGNAL design system).
- Local Ollama LLM integration (`llama3.2` / `qwen2.5:1.5b`) + Free-Tier Cloud LLM (Groq `openai/gpt-oss-20b`) + Commercial Cloud LLMs (Anthropic Claude Sonnet 4.6 / OpenAI GPT-4o).
- Official Pi Coding Agent SDK (`@earendil-works/pi-coding-agent@1.1.0`) with sandboxed domain tools.
- Seamless UI model switcher with real-time health indicator and transparent fallback.
- Hybrid/semantic transcript search and RAG engine with guest and episode citation.
- Interactive dual-pane **Artifact Studio** (Claude Artifacts style) with live HTML/CSS sandboxed rendering and Warm Paper Markdown previews.
- Dedicated **Ship 30 for 30 Content Generation Skill** (1,250-word atomic essay generator with floating brief modal).
- Multi-session persistence in PostgreSQL.
- One-command startup via `docker compose` or local run script (`run_dev.ps1`).
- Automated API, retrieval, and regression test suites.

#### Intentionally Out of Scope (V1)
- *Multi-tenant user authentication (SSO / OAuth)*: Kept simple to session IDs to reduce evaluation setup friction.
- *Voice audio ingestion*: Transcripts are pre-ingested rather than raw audio parsing to prioritize latency and stability.
- *Fine-tuning*: RAG and in-context skills provide superior accuracy, freshness, and citation traceability compared to fine-tuning.

---

### 1.5 Risks & Trade-Offs Matrix

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Hallucination on unmentioned topics** | High | System prompt strictly enforces: *"If the provided transcripts do not contain the answer, explicitly state that Lenny has not covered this topic."* |
| **Local model token limit / context truncation** | Medium | Smart transcript chunking (overlapping 180-word conversational chunks with guest metadata) + hybrid retrieval (top-k semantic + BM25 keyword rerank via RRF). |
| **Untrusted HTML execution in Artifact Viewer** | Critical | Render HTML inside an isolated `iframe` with `sandbox=""` (empty sandbox blocking all scripts, parent DOM access, and forms) and restrictive Content Security Policy (`default-src 'none'`). |
| **Cloud API cost & rate limits** | Low | Defaults to local Ollama and free-tier Groq Cloud; fallback logic handles rate limits gracefully with user notification. |
| **Cold start / Ollama daemon latency** | Medium | Backend startup health-check probes Ollama endpoint and warms up model cache on boot. |

---

## 2. Core Functional Requirements

### 2.1 Backend API (FastAPI)
- `POST /api/v1/chat`: Streaming or standard chat completion taking `session_id`, `message`, `model_provider` (ollama | anthropic | openai), and optional `skill` trigger.
- `GET /api/v1/sessions`: List all user sessions.
- `POST /api/v1/sessions`: Create a new independent session context.
- `GET /api/v1/sessions/{id}/history`: Retrieve full transcript of session.
- `GET /api/v1/artifacts/{id}`: Retrieve rendered artifact details.
- `GET /api/v1/health`: Health probe reporting API status, DB connection, Ollama availability, and loaded models.

### 2.2 Model Orchestration Layer
- Configurable abstraction layer (`LLMProvider`) supporting:
  - Local Ollama via HTTP client (`http://localhost:11434/api/generate` or `/api/chat`).
  - Cloud Anthropic Claude (`anthropic` SDK) and OpenAI (`openai` SDK).
- Dynamic model toggle without server restart.

### 2.3 Transcript Ingestion & Hybrid RAG Engine (Phase 1B Completed & Verified)
- **Knowledge Base Scope**: 303 complete podcast episodes and 89 curated topic indexes parsed from `data/transcripts/`.
- **Intelligent Conversational Chunker**: Preserves speaker boundaries and continuous dialogue turns with rolling windows (180 words, 35 words overlap). Total indexed chunks: 32,209.
- **Tri-Signal Hybrid Retrieval Engine**:
  1. Dense Semantic Search: ONNX-accelerated `BAAI/bge-small-en-v1.5` embeddings (384-dim, normalized).
  2. Lexical Search: `BM25Okapi` with token smoothing for precise entity and terminology matching.
  3. Curated Topic Taxonomy Boosting: Direct graph linkages across 89 topic indices.
  4. Ranking: Reciprocal Rank Fusion ($RRF$, $k=60$) with adjacent turn deduplication.
- **Strict Evidence & Grounding Protocol**:
  - Response states: `relevant_evidence_found`, `insufficient_evidence`, `empty_knowledge_base`, `index_unavailable`, `invalid_query`, `retrieval_failure`.
  - Multi-signal verification via non-stopword query term coverage and semantic confidence thresholds.
  - Zero hallucination guarantee: Returns `insufficient_evidence` when topics are unmentioned without falsifying claims.
  - Verbatim citations: Guarantees exact quote excerpts, speaker name, guest, episode title, and verified YouTube deep-link URLs (`&t={s}s`).
- **REST API Endpoints**:
  - `POST /api/v1/retrieval/search`: Search request with optional topic filter and top_k; returns ranked passages, citation metadata, and diagnostics.
  - `GET /api/v1/knowledge/status`: Real-time operational diagnostics reporting document/chunk counts, index memory state, storage size, and timestamps.

### 2.4 "Ship 30 for 30" Skill Engine
Encodes the core writing principles of Dickie Bush & Nicolas Cole:
- **Headline / Hook**: Clear problem or curiosity gap.
- **The 1-3-1 Cadence**: Short introductory rhythm for skimmability.
- **Bold Lead-ins**: Headings and bold prefixes on every takeaway.
- **Length**: Target ~1,250 words structured into 3-5 distinct pillars.
- **Strict Evidence**: Every pillar must attribute specific anecdotes to the interviewed guests.

### 2.5 In-App Dual-Pane Artifact Viewer
- When response contains structured documents, diagrams, or HTML/CSS mockups, extract artifact into an interactive side pane.
- Supports tabs: **Preview** (live render) and **Code** (syntax highlighted with copy-to-clipboard).
- Sandbox container for HTML rendering.

---

## 3. Non-Functional Requirements
- **Performance**: P95 response time < 10s for full grounded generation; TTFT < 2s for local stream.
- **Reliability**: Graceful degradation if Ollama or Cloud API is offline.
- **Maintainability**: Clean PEP 8 Python, type hints (`pydantic`), modular architecture.
- **Observability**: Structured JSON logging with trace IDs.
