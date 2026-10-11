import type {
  Session,
  Message,
  Citation,
  Artifact,
  ProvidersStatusResponse,
  ChatRequestPayload,
  Ship30RequestPayload,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export class ApiError extends Error {
  status: number;
  data: any;
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit & { timeoutMs?: number } = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const timeoutMs = options.timeoutMs ?? 120000; // 2 minute default bound
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorDetail = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errJson.message || errorDetail;
      } catch {
        // ignore
      }
      throw new ApiError(errorDetail, response.status);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError" || err.name === "TimeoutError") {
      throw new ApiError(
        `Request to ${endpoint} timed out after ${Math.round(timeoutMs / 1000)}s. Generation is taking longer than expected. Please retry.`,
        408
      );
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      `Network connection failed while connecting to ${endpoint}. Verify the FastAPI backend is running.`,
      503
    );
  }
}

export const api = {
  async listSessions(): Promise<Session[]> {
    const data = await request<any>("/sessions");
    return Array.isArray(data) ? data : (data.sessions || data.items || []);
  },

  async createSession(title?: string, model_provider = "ollama", model_name = "llama3.2"): Promise<Session> {
    return request<Session>("/sessions", {
      method: "POST",
      body: JSON.stringify({ title: title || "New Conversation", model_provider, model_name }),
    });
  },

  async getSession(sessionId: string): Promise<Session> {
    return request<Session>(`/sessions/${sessionId}`);
  },

  async renameSession(sessionId: string, title: string): Promise<Session> {
    return request<Session>(`/sessions/${sessionId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  },

  async deleteSession(sessionId: string): Promise<{ deleted: boolean }> {
    return request<{ deleted: boolean }>(`/sessions/${sessionId}`, {
      method: "DELETE",
    });
  },

  // --- Session Data & History ---
  async getSessionHistory(sessionId: string): Promise<{ session_id: string; title: string; messages: Message[] }> {
    return request<{ session_id: string; title: string; messages: Message[] }>(`/sessions/${sessionId}/history`);
  },

  async getSessionCitations(sessionId: string): Promise<{ session_id: string; total_citations: number; citations: Citation[] }> {
    return request<{ session_id: string; total_citations: number; citations: Citation[] }>(`/sessions/${sessionId}/citations`);
  },

  async getSessionArtifacts(sessionId: string): Promise<{ session_id: string; total_artifacts: number; artifacts: Artifact[] }> {
    return request<{ session_id: string; total_artifacts: number; artifacts: Artifact[] }>(`/sessions/${sessionId}/artifacts`);
  },

  // --- Chat Completion & Official Agent SDK ---
  async sendChatMessage(payload: ChatRequestPayload): Promise<Message> {
    // If Pi agent SDK mode is requested, use dedicated /agent/pi route or send agent_sdk: "pi"
    if (payload.agent_sdk === "pi") {
      return request<Message>("/chat/agent/pi", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }

    return request<Message>("/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // --- Ship 30 for 30 Skill ---
  async generateShip30Essay(payload: Ship30RequestPayload): Promise<{
    session_id: string;
    topic: string;
    essay: string;
    headline: string;
    word_count: number;
    guest_references: string[];
    citations: Citation[];
    artifact_id: string;
  }> {
    const raw: any = await request("/skills/ship30", {
      method: "POST",
      body: JSON.stringify(payload),
      timeoutMs: 180000, // 3 minutes timeout for long-form atomic essay generation
    });

    const essayContent = raw.content || raw.essay || raw.artifacts?.[0]?.content || "";
    const firstArt = (raw.artifacts && raw.artifacts[0]) || {};
    const title = firstArt.title || raw.headline || raw.topic || `Ship 30: ${payload.topic}`;
    const rawCitations: Citation[] = raw.citations || [];
    const guests = Array.from(
      new Set(rawCitations.map((c: any) => c.guest || c.guest_name).filter(Boolean))
    ) as string[];
    const words = essayContent.trim().split(/\s+/).filter(Boolean).length;

    return {
      session_id: raw.session_id || payload.session_id || `session-${Date.now()}`,
      topic: raw.topic || payload.topic,
      essay: essayContent,
      headline: title,
      word_count: words,
      guest_references: guests.length > 0 ? guests : ["Lenny's Podcast Experts"],
      citations: rawCitations,
      artifact_id: raw.artifact_id || `art-${Date.now()}`,
    };
  },

  // --- Providers & Capabilities ---
  async getProvidersStatus(): Promise<ProvidersStatusResponse> {
    return request("/providers/status");
  },

  // --- Hybrid Retrieval Search ---
  async searchTranscripts(query: string, top_k = 5): Promise<{
    query: string;
    evidence_status: string;
    total_candidates: number;
    latency_ms: number;
    passages: Array<{
      guest: string;
      episode_title: string;
      episode_slug: string;
      timestamp_url: string;
      start_timestamp: string;
      text: string;
      score: number;
    }>;
  }> {
    return request("/retrieval/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k }),
    });
  },
};
