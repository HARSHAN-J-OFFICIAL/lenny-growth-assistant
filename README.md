# The Lenny Growth Assistant
> **SIGNAL — The Lenny Growth Studio | Turn Conversations into Clarity**  
> *Executive AI Advisor & Digital Writing Engine Grounded in 303 Lenny's Podcast Episodes*

[![CI / Regression Tests](https://img.shields.io/badge/backend%20tests-88%2F88%20passing-emerald.svg)](backend/tests/)
[![Chrome E2E Tests](https://img.shields.io/badge/chrome%20e2e-24%2F24%20verified-brightgreen.svg)](docs/architecture.md)
[![Agent SDK](https://img.shields.io/badge/%40earendil--works%2Fpi--coding--agent-v1.1.0-blue.svg)](agent_service/)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](backend/)
[![React](https://img.shields.io/badge/react-19-61dafb.svg)](frontend/)
[![Docker Compose](https://img.shields.io/badge/docker%20compose-4%20services-2496ed.svg)](docker-compose.yml)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## 1. Project Title & Overview

**The Lenny Growth Assistant** (Signature Product Identity: **SIGNAL — The Lenny Growth Studio**) is an enterprise-grade AI research workspace and tactical growth publishing studio grounded in 303 complete episodes of [Lenny's Podcast](https://www.youtube.com/@LennysPodcast). Powered by a hybrid dense semantic (FastEmbed `bge-small-en-v1.5`) and sparse lexical (`BM25Okapi`) retrieval engine with Reciprocal Rank Fusion ($RRF$), the application delivers verifiable, quotation-level advice attributed to the world's leading product operators (Brian Chesky, Elena Verna, Shreyas Doshi, Todd Jackson, Gustaf Alströmer, and hundreds more).

Built with a custom editorial design language on Warm Paper (`#F4EEE4`), the assistant pairs conversational research with an in-app **Artifact Studio** and a specialized **Ship 30 for 30 Writing Engine** that transforms raw podcast transcripts into publication-ready, ~1,250-word atomic essays.

---

## 2. Business Problem

Product managers, growth operators, and startup founders make high-stakes strategic decisions daily. While Lenny's Podcast contains thousands of hours of world-class, battle-tested advice:
1. **Search & Retrieval Friction**: Operators cannot efficiently pinpoint actionable tactics across 300+ episodes without manual scanning.
2. **Hallucination Risk**: Generic LLMs hallucinate generic advice rather than the specific frameworks developed by world-class leaders.
3. **Execution Gap**: Transforming podcast transcripts into structured PRDs, launch checklists, and viral essays requires hours of manual drafting.
4. **Privacy & Cost Constraints**: Organizations cannot leak proprietary roadmaps to third-party cloud APIs or pay recurring per-token fees for internal AI tooling.

---

## 3. Primary Users & Use Cases

- **Product Managers (PMs)**: Retrieve frameworks on PM hiring, roadmap prioritization, feature sunsetting, and pricing tier design.
- **Growth Leads**: Query battle-tested playbooks on product-led growth (PLG) loops, retention vs. acquisition balance, and experiment design.
- **Founders & CEOs**: Explore "Founder Mode" management principles, early-stage enterprise sales tactics, and finding product-market fit (PMF).
- **Executive Writers & Thought Leaders**: Generate structured Ship 30 for 30 atomic essays with verified quotes, 1-3-1 hooks, bold lead-ins, and actionable takeaways.

---

## 4. Key Features

- **Grounded Transcript RAG**: Tri-signal hybrid search (Dense FastEmbed + Sparse BM25Okapi + 89 Curated Topic Taxonomies) fused via Reciprocal Rank Fusion ($RRF$, $k=60$) over 32,209 chunks across 303 episodes.
- **Verifiable Citations — "Source Tapes"**: Signature audio cassette-styled reference cards with guest names, episode titles, raw calibrated RRF relevance scores, and clickable YouTube timestamp links navigating to the exact video playback second.
- **Official Pi Coding Agent SDK Integration**: Microservice powered by `@earendil-works/pi-coding-agent@1.1.0` with strict tool sandboxing (`noTools: "builtin"`, exclusion of shell/filesystem tools, allowlist of domain tools).
- **Ship 30 for 30 Digital Writing Engine**: Structured two-part continuation strategy consistently producing expansive, publication-ready essays of **1,200 to 1,450 words** with exact verified word count reporting and floating brief modal.
- **Hardened Sandboxed Artifact Studio**: Dual-pane workspace with live typeset Markdown preview on Warm Paper (`.editorial-prose`), syntax-highlighted source view (`<pre><code>`), one-click copy with visual feedback, `.md` download export, and horizontal drag resizing. HTML artifacts are rendered inside an isolated iframe with `sandbox=""` (empty sandbox) and a strict Content Security Policy (`default-src 'none'`).
- **Dynamic AI Provider Switching**: Live toggle between local Ollama (`llama3.2`, `qwen2.5:1.5b`), Free-Tier Cloud LLMs (Groq LPU `openai/gpt-oss-20b`), and Enterprise Cloud LLMs (OpenAI GPT-4o, Anthropic Claude Sonnet 4.6) with transparent local fallback when API keys are absent.
- **PostgreSQL Session Persistence**: Async SQLAlchemy persistence tracking conversations, messages, citations, and artifacts across browser reloads, with confirmation deletion protection.
- **Four-Service Docker Compose Topology**: Production-ready orchestration of PostgreSQL 16, FastAPI backend, Pi Agent daemon, and NGINX-served React frontend.

---

## 5. Application Interface & Visual Identity (SIGNAL)

The application features a bespoke **SIGNAL** editorial aesthetic pairing Midnight Ink (`#101B27` / `#172634`) structure with Warm Paper (`#F4EEE4` / `#FFF9F0`) reading surfaces and vibrant Signal Coral (`#FF7952`) & Mint Signal (`#75D2BB`) accents:

| View | Description |
| :--- | :--- |
| **Research Library (Left Panel)** | Midnight Ink navigation notebook with "+ New conversation" Coral CTA, session list, active indicator marker, and operational provider status. |
| **AI Research Workspace (Center Panel)** | Warm Paper canvas with custom SVG growth waveform hero (*"Good ideas start with better questions."*), 4 grounded prompt starters, and clean message composer. |
| **Source Tapes (Podcast Citations)** | Cassette-inspired citation badges with guest name, episode title, monospaced timestamp pill, and YouTube deep-link (`↗ Listen on YouTube`). |
| **Artifact Studio (Right Panel)** | Publication studio rendering typeset articles on Warm Paper, sandboxed HTML iframe preview, word count counter, copy feedback, and `.md` export. |
| **Ship 30 Writing Brief Modal** | Floating centered overlay with backdrop blur, warm inputs, and "Generate essay →" Coral action. |
| **Mobile Drawer Overlay** | Fluid adaptation on mobile (390px) viewports with zero horizontal overflow. |

---

## 6. Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Host Environment (Windows / Linux)                 │
│   Ollama Local Daemon: http://127.0.0.1:11434 (llama3.2, qwen2.5)     │
│   Host Gateway: host.docker.internal:11434                            │
└────────────────────────────────────▲───────────────────────────────────┘
                                     │
┌─ Docker Compose Network (lenny_network) ───────────────────────────────┐
│                                    │                                   │
│  ┌───────────────────────┐         │                                   │
│  │ lenny_frontend (NGINX)│         │                                   │
│  │ - Port 5173 -> 80     │         │                                   │
│  │ - Static assets cache │         │                                   │
│  │ - Reverse proxy /api/ ┼─────────┼────────────────┐                  │
│  └───────────────────────┘         │                │                  │
│                                    │                │                  │
│  ┌───────────────────────┐         │      ┌─────────▼───────────────┐  │
│  │ lenny_backend(FastAPI)│◄────────┴──────┤ lenny_pi_agent (Node)   │  │
│  │ - Port 8000           │                │ - Port 8001             │  │
│  │ - Hybrid Retrieval    │                │ - Pi Agent SDK v1.1.0   │  │
│  │ - Mounts ./data (ro)  │                │ - Sandboxed tools only  │  │
│  └───────────┬───────────┘                └─────────────────────────┘  │
│              │                                                         │
│  ┌───────────▼───────────┐                                             │
│  │ lenny_postgres        │                                             │
│  │ - PostgreSQL 16 Alpine│                                             │
│  │ - Volume: postgres_data                                             │
│  └───────────────────────┘                                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn (ASGI), Pydantic v2, Pydantic Settings, AsyncPG, SQLAlchemy 2.0.
- **Information Retrieval & RAG**: FastEmbed (`BAAI/bge-small-en-v1.5`, 384-dim ONNX embeddings), Rank-BM25 (`BM25Okapi`), NumPy, PyYAML.
- **Agent Orchestration**: Official Pi Coding Agent SDK (`@earendil-works/pi-coding-agent@1.1.0`), TypeBox schemas, Node.js 20.
- **Frontend**: React 19, TypeScript 5.8, Vite 8, Tailwind CSS, Lucide Icons, React-Markdown, Remark-GFM.
- **Production Server**: NGINX Alpine (reverse proxy, gzip compression, SPA routing).
- **Database**: PostgreSQL 16 Alpine (with SQLite fallback for lightweight development).
- **Local Inference**: Ollama daemon (`llama3.2:latest`, `qwen2.5:1.5b`).
- **Testing & E2E**: Pytest, Pytest-Asyncio, AnyIO, Puppeteer-Core (driving Google Chrome).

---

## 8. Prerequisites

Before running the application, ensure the host machine has:
1. **Docker Desktop** (with Docker Compose v2+) running.
2. **Ollama** installed on the host machine ([ollama.com](https://ollama.com)).
3. **Pulled Local Models**:
   ```bash
   ollama pull llama3.2
   ollama pull qwen2.5:1.5b
   ```
4. **Python 3.12**: Required on host machine for running `scripts/download_transcripts.py` and `backend/ingest.py` before container startup.
5. *(Optional for Native Dev)*: Node.js 20+.

---

## 9. Environment Configuration

Copy the documented environment template:
```bash
cp .env.example .env
```

Key variables configured in `.env`:
```ini
# Database (PostgreSQL 16)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_dev_password
POSTGRES_DB=lenny_assistant
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:postgres_dev_password@localhost:5432/lenny_assistant

# Local Ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_DOCKER_URL=http://host.docker.internal:11434
OLLAMA_DEFAULT_MODEL=llama3.2

# Pi Agent Microservice
AGENT_SERVICE_URL=http://127.0.0.1:8001
AGENT_SERVICE_PORT=8001
FASTAPI_URL=http://127.0.0.1:8000

# Optional Cloud Keys (Leave empty for 100% offline local evaluation)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

---

## 10. Transcript Acquisition & Knowledge Indexing Pipeline

### Licensing & Attribution Obligations
The podcast transcripts are sourced from the community archive repository ([ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)) for educational, personal, and research evaluation purposes. All audio, transcript copyright, and interview content belong to [Lenny's Podcast](https://www.youtube.com/@LennysPodcast) and the respective interviewed guests.

To respect redistribution rights and avoid committing heavy binary vector embeddings to Git, the raw transcripts and generated vector index files are excluded from the Git repository.

### Step 1: Acquire the Podcast Transcripts
Acquire the complete 303-episode transcript corpus with a single command:
```bash
python scripts/download_transcripts.py
```
*Alternatively, clone manually:*
```bash
git clone https://github.com/ChatPRD/lennys-podcast-transcripts data/transcripts
```

### Step 2: Build the Hybrid Retrieval Index
Once transcripts are present, generate the hybrid BM25 + Dense vector index:

```bash
# Option A: Quick Evaluation (Index first 10 episodes in ~45 seconds)
python backend/ingest.py --max-episodes 10

# Option B: Full Production Index (All 303 episodes, ~31 minutes on CPU)
python backend/ingest.py
```

### Status & Verification
Inspect the health and metrics of your local index at any time:
```bash
python backend/ingest.py --status
```
*Expected: 303 episodes · 32,209 chunks · 384-dimensional FastEmbed embeddings · Sub-50ms hybrid search.*

---

## 11. Docker Compose Setup (One-Command Launch)

To launch the complete application stack (Database, Backend, Agent, and Frontend) in Docker:

```bash
docker compose up --build -d
```

### Verification Commands:
```bash
# Check container status and healthchecks
docker compose ps

# View unified streaming logs
docker compose logs -f

# Check backend health
curl http://localhost:8000/api/v1/health

# Check Pi agent health
curl http://localhost:8001/health
```

Once running, access the web interface at **`http://localhost:5173`**.

To stop the containers while preserving database state:
```bash
docker compose down
```

---

## 12. Native Windows Development Setup

For local development using installed host runtimes:

```powershell
# Run the automated native orchestrator
.\run_dev.ps1
```

The runner:
1. Verifies Node.js, Python virtualenv (`backend/.venv`), Docker PostgreSQL, and Ollama.
2. Starts the Pi Agent daemon on port `8001`.
3. Starts the FastAPI backend with hot-reload on port `8000`.
4. Starts the Vite React frontend on port `5173`.
5. Gracefully terminates all background jobs on `Ctrl+C`.

---

## 13. PostgreSQL Initialization

- Database tables (`sessions`, `messages`, `artifacts`, `citations`) are initialized automatically on application startup via SQLAlchemy metadata creation.
- Persistent data is stored in the named Docker volume `lenny_postgres_data` and survives container restarts and upgrades.
- In native development mode, if Docker is temporarily offline, the backend gracefully falls back to a zero-configuration local SQLite database (`lenny_assistant.db`).

---

## 14. Ollama Configuration

Ollama runs natively on the host machine.
- In **Native Windows Mode**: Backend and Agent connect to `http://127.0.0.1:11434`.
- In **Docker Compose Mode**: Containers reach the host daemon via `http://host.docker.internal:11434` enabled by `extra_hosts: ["host.docker.internal:host-gateway"]`.
- To confirm host models:
  ```bash
  ollama list
  ```

---

## 15. Optional Cloud Provider Configuration & Evaluator Guide

The Lenny Growth Assistant features a hybrid Local/Cloud AI inference architecture. By design, **all core functionality operates 100% locally and offline** using local Ollama (`llama3.2` and `qwen2.5:1.5b`), with zero required cloud API keys or billing.

For evaluators who wish to test live cloud inference with their own accounts, OpenAI and Anthropic cloud adapters are fully implemented, tested with mocks, and configuration-ready.

### Evaluator Guide: "How to Enable Cloud LLM Mode Using Your Own API Key"

1. **Open Your Local Environment File:**
   Open the root `.env` file (which is strictly excluded by `.gitignore` and never committed):
   ```bash
   # In root directory
   .env
   ```

2. **Add Your Cloud Key(s):**
   Paste your key into the corresponding environment variable:
   ```env
   # OpenAI (for GPT-4o and GPT-4o Mini)
   OPENAI_API_KEY=your_actual_openai_key_here

   # Anthropic (for Claude Sonnet 4.6 and Claude Haiku 4.5)
   ANTHROPIC_API_KEY=your_actual_anthropic_key_here

   # Groq Cloud (Free Tier - for GPT-OSS 20B and Llama 3.3 70B on Groq LPUs)
   GROQ_API_KEY=your_actual_groq_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   ```

3. **Restart the Stack:**
   - **In Docker Compose:**
     ```bash
     docker compose up -d
     ```
   - **In Native Mode:** Restart `.\run_dev.ps1` to reload environment variables.

4. **Verify in the Web Interface:**
   - Open the web application (`http://localhost:80` for Docker or `http://localhost:5173` for native).
   - Click the **Model Selector** dropdown in the top bar.
   - The selected cloud model badge will dynamically transition from `Cloud • Unconfigured (Fallback Active)` to `Cloud • Ready`.
   - Select your desired model (e.g., `Groq Cloud (GPT-OSS 20B)`, `OpenAI GPT-4o`, or `Anthropic Claude Sonnet 4.6`). Subsequent inquiries will execute directly via the authenticated cloud API.

### Provider Switching & Transparent Fallback Behavior

The application enforces strict truth-in-advertising regarding which inference engine responds:

| Requested Provider | API Key State | Actual Execution Engine | UI Display & Diagnostic Notice |
| :--- | :---: | :--- | :--- |
| **Ollama (Llama 3.2)** | N/A (Local) | Local Ollama daemon (`llama3.2`) | Displays `OLLAMA/llama3.2` badge. |
| **Ollama (Qwen 2.5)** | N/A (Local) | Local Ollama daemon (`qwen2.5:1.5b`) | Displays `OLLAMA/qwen2.5:1.5b` badge. |
| **Groq (GPT-OSS 20B)** | **Configured** | Groq Cloud LPU (`openai/gpt-oss-20b`) | Displays `GROQ/openai/gpt-oss-20b` badge. |
| **Groq (GPT-OSS 20B)** | **Missing / Empty** | **Transparent fallback to local Ollama** | Yellow pill banner: `[Notice: Groq Cloud provider is unconfigured. Automatically routed to local Ollama (llama3.2).]` |
| **OpenAI (GPT-4o)** | **Configured** | Official `AsyncOpenAI` client | Displays `OPENAI/gpt-4o` badge. |
| **OpenAI (GPT-4o)** | **Missing / Empty** | **Transparent fallback to local Ollama** | Yellow pill banner: `[Notice: OpenAI Cloud provider is unconfigured. Automatically routed to local Ollama (llama3.2).]` |
| **Anthropic (Claude)** | **Configured** | Official `AsyncAnthropic` client | Displays `ANTHROPIC/claude-sonnet-4-6` badge. |
| **Anthropic (Claude)** | **Missing / Empty** | **Transparent fallback to local Ollama** | Yellow pill banner: `[Notice: Claude Agent SDK running via Local Ollama Adapter (llama3.2).]` |

### Cloud Security & Key Protection Guarantees
- **Server-Side Only**: Cloud API keys are loaded strictly on the backend (`FastAPI` and Node Pi SDK daemon). They are **never sent to the client browser**, never exposed in network JSON payloads, and never bundled in Vite production assets.
- **Diagnostics Masking**: The `/api/v1/providers/status` endpoint reports boolean flags (`is_configured: true/false`), never leaking raw key values.
- **Git Exclusions**: `.gitignore` strictly excludes `.env`, `.env.*`, `*.pem`, `*.key`, and credential caches.
- **Bounded Timeouts**: All cloud API calls enforce a strict 60-second timeout (`timeout=60.0`) to prevent thread starvation or indefinite hanging on network interruptions.

### Supported Cloud Models & Cost Considerations
- **Groq Cloud (Free Tier Available):**
  - `openai/gpt-oss-20b`: Default open-weight Mixture-of-Experts reasoning model on Groq LPU (131k context, configurable via `GROQ_MODEL`).
  - `llama-3.3-70b-versatile`: Flagship high-intelligence open model on Groq LPU (131k context).
  - `llama-3.1-8b-instant`: Ultra-fast low-latency model on Groq LPU (131k context).
  - Free API keys available without credit card at https://console.groq.com.
- **OpenAI:**
  - `gpt-4o`: Flagship multimodal model (128k context). Configurable via `OPENAI_DEFAULT_MODEL`.
  - `gpt-4o-mini`: Fast, cost-efficient alternative (128k context).
- **Anthropic:**
  - `claude-sonnet-4-6`: Flagship reasoning, coding, and multi-turn agent tool use (200k context). Configurable via `ANTHROPIC_DEFAULT_MODEL`.
  - `claude-haiku-4-5`: High-speed, budget-friendly tier (200k context).
- **Billing Notice & Verification Status**: Cloud API usage incurs direct billing from your respective accounts (except Groq free tier). Real authenticated cloud inference is marked **UNVERIFIED** until a live API key is provided by the evaluator. Local Ollama is 100% verified and free.

---

## 16. Running the Application

| Service | Local URL | Description |
| :--- | :--- | :--- |
| **Frontend UI** | [http://localhost:5173](http://localhost:5173) | Three-panel executive web application |
| **FastAPI Backend** | [http://localhost:8000](http://localhost:8000) | REST API & Hybrid Retrieval engine |
| **Swagger API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI documentation |
| **Pi Agent Daemon** | [http://localhost:8001](http://localhost:8001) | Official Pi Coding Agent SDK service |
| **Health Probe** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Backend & Database connection health |

---

## 17. API Documentation

Key endpoints defined in OpenAPI schema (`/docs`):
- `POST /api/v1/chat`: Conversational chat completion supporting standard and agentic modes.
- `POST /api/v1/chat/agent/pi`: Direct execution via the official Pi Coding Agent SDK.
- `POST /api/v1/skills/ship30`: Dedicated Ship 30 for 30 digital writing engine.
- `GET /api/v1/sessions`: List all persisted user conversation sessions.
- `PATCH /api/v1/sessions/{id}`: Rename conversation title.
- `DELETE /api/v1/sessions/{id}`: Cascade delete session and associated messages/artifacts.
- `POST /api/v1/retrieval/search`: Hybrid semantic + BM25 transcript search.
- `GET /api/v1/knowledge/status`: Retrieval index diagnostics (303 episodes, 32,209 chunks).
- `GET /api/v1/providers/status`: Available LLM providers and configuration state.

---

## 18. Running Automated Tests & Manual Test Plan

### 18.1 Backend Regression Suite (88 Tests)
```bash
# Activate virtual environment and run pytest
cd backend
.venv\Scripts\python.exe -m pytest tests/ -v
```
*Result: 88 passed in 58s (100% pass rate across 10 test modules).*

Key test suites covered:
- `test_chat_api.py`: Session creation, conversational continuity, and chat endpoints.
- `test_pi_agent_responses.py`: Pi Agent SDK routing, empty response prevention, and entity resolution (e.g., "Who is Elena?").
- `test_cloud_providers_audit.py`: Multi-provider routing, live Groq Cloud integration, OpenAI/Anthropic fallback mechanics.
- `test_artifact_security.py`: Sandboxed iframe isolation verification (`sandbox=""` and restrictive CSP).
- `test_incremental.py` & `test_hybrid_retrieval.py`: Hybrid BM25 + dense vector semantic retrieval with RRF ranking.
- `test_ship30_skill.py`: Ship 30 for 30 ~1,250-word atomic essay generation structure.
- `test_session_persistence.py`: PostgreSQL schema and conversation history integrity.

### 18.2 Chrome End-to-End Automation Suite (24 Workflows)
```bash
# Run Chrome Puppeteer evaluation
cd frontend
node test_chrome_e2e.mjs
```
*Result: 24 passed in 58s (100% pass rate across visual and functional flows).*

### 18.3 Manual UI Test Plan for Evaluators (Deliverable 7)

Evaluators can verify the entire frontend experience in under 5 minutes using this step-by-step test plan:

| Step | Flow / Feature | Evaluator Action | Expected Result | Pass / Fail |
| :--- | :--- | :--- | :--- | :---: |
| **1** | **System Readiness & Metrics** | Open `http://localhost:5173`. Inspect header and status bar. | Green pulsing status indicator shows `303 Episodes · 32,209 Chunks`. Header displays **SIGNAL — The Lenny Growth Studio**. | [ ] |
| **2** | **Grounded Query & Source Tapes** | In chat input, enter: *"What does Elena Verna recommend about product-led growth?"* and hit Enter. | Response streams in with substantive tactical advice. An expandable **Source Tapes** tray renders showing Elena Verna episode citations with exact timestamps, guest badges, and direct YouTube links. | [ ] |
| **3** | **Conversational Memory** | Ask a follow-up: *"How does she define pipeline accountability?"* | The assistant answers within context without losing conversational history or repeating entire introductory greetings. | [ ] |
| **4** | **Model & Provider Switching** | Click the Model Selector pill in the top header. Switch from `llama3.2` to `qwen2.5:1.5b` or select `Groq (gpt-oss-20b)`. Send a query: *"What is the PM interview loop?"* | Active model badge updates in header. When using Groq with valid API key, responses stream via Groq LPU. If unconfigured, a polite yellow fallback banner indicates transparent local fallback to Ollama. | [ ] |
| **5** | **Ship 30 for 30 Essay Modal** | Click **"Ship 30 Essay"** in the top header. Select topic *"Finding Product-Market Fit in B2B SaaS"* and click **"Generate & Save Artifact"**. | A loading state with live progress step displays. Within seconds, a ~1,250-word structured atomic essay is generated (1-3-1 hook, bold lead-ins, actionable checklist, grounded podcast takeaways). | [ ] |
| **6** | **Artifact Studio & Sandbox Security** | Observe the right-hand **Artifact Studio** slide-over panel displaying the generated essay. | The artifact renders in the **Warm Paper** reader view. Switching between **Preview** and **Source** reveals clean HTML/Markdown. Click **Copy** (shows emerald checkmark) and **Download** (`.html` or `.md` downloads to disk). Verify that script execution is completely neutralized by checking dev tools iframe `sandbox=""`. | [ ] |
| **7** | **Session Rename & Persistence** | In the left sidebar, hover over the active session and click the pencil icon. Rename to *"Elena PLG Strategy"* and hit Enter. Press `F5` / reload browser. | Session is renamed. Upon page reload, the session remains active with all chat history, citations, and artifacts intact from PostgreSQL. | [ ] |
| **8** | **Layout Flexibility & Responsiveness** | Click and drag the vertical pane splitter between Chat and Artifact Studio. Resize browser window to mobile width (< 768px). | Artifact Studio resizes smoothly without horizontal clipping. On mobile screens, sidebar collapses into a slide-out hamburger drawer, providing an unobstructed reading experience. | [ ] |

---

## 19. Troubleshooting

| Issue | Root Cause | Resolution |
| :--- | :--- | :--- |
| **Ollama connection refused from Docker** | Container cannot resolve `127.0.0.1` | Ensure `OLLAMA_BASE_URL=http://host.docker.internal:11434` and `extra_hosts` is present in `docker-compose.yml`. |
| **PostgreSQL port 5432 conflict** | Another local Postgres instance running | Modify `POSTGRES_PORT=5433` in `.env` or stop the competing service. |
| **Artifact preview blank** | Stale browser cache | Hard refresh with `Ctrl+Shift+R` or clear sessionStorage. |
| **Small model raw JSON in text** | Tokenizer tool emission variance | Handled automatically by backend regex fallback cleaner in `agent_orchestrator.py`. |

---

## 20. Known Limitations

- **Cloud Provider Testing**: Live testing of OpenAI and Anthropic requires personal API keys. In the default configuration, requests gracefully fall back to local Ollama.
- **Initial Embedding Duration**: Embedding the entire 303-episode dataset from scratch takes ~31 minutes on CPU. The pre-built index in `data/indices/` eliminates this for evaluators.

---

## 21. Security Considerations

- **Strict Sandbox Isolation**: All rendered HTML artifacts are sandboxed with `sandbox=""` and a restrictive Content Security Policy (`default-src 'none'`), neutralizing cross-site scripting (XSS), DOM theft, and token exfiltration.
- **No System Tools for Agents**: The Pi Agent is restricted to domain tools (`search_podcast_transcripts`, `generate_sandboxed_artifact`). All shell, process, and host filesystem primitives are strictly excluded.
- **Untrusted Transcript Defense**: Podcast transcripts are treated as passive data. Embedded prompts within transcripts are ignored.
- **Secrets Management**: No API keys or credentials are hardcoded or tracked in Git.

---

## 22. Extending the System

- **Adding a New Domain Tool**: Define tool schema in `backend/app/services/agent_tools.py`, implement executor, and register in `agent_service/pi_agent.mjs`.
- **Adding New Transcripts**: Drop new markdown files into `data/transcripts/episodes/<slug>/transcript.md` and trigger `POST /api/v1/retrieval/ingest`.
- **Custom Writing Skills**: Implement a new prompt engine in `backend/app/services/` following the `ship30_skill.py` modular pattern.

---

## 23. Demonstration Instructions

Refer to the complete 2m 45s walkthrough script in [docs/demo-outline.md](docs/demo-outline.md) for step-by-step presentation guidelines covering the business problem, live grounded query, verifiable citations, session persistence, provider switching, and the Ship 30 atomic essay generation.
