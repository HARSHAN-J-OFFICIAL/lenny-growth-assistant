export interface Citation {
  guest: string;
  speaker?: string;
  episode_title: string;
  episode_slug?: string;
  timestamp_url?: string;
  start_timestamp?: string;
  score?: number;
}

export interface Artifact {
  id: string;
  session_id: string;
  title: string;
  artifact_type: "markdown" | "html" | "svg" | "code";
  content: string;
  created_at?: string;
}

export interface MessageMetadata {
  evidence_status?: string;
  model_provider?: string;
  model_name?: string;
  agentic?: boolean;
  agent_sdk?: string;
  tool_calls_trace?: Array<{ tool: string; params: any }>;
  notice?: string;
  skill?: string;
  retrieval_latency_ms?: number;
  candidates_count?: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  metadata: MessageMetadata;
  artifacts?: Artifact[];
  created_at: string;
}

export interface Session {
  id: string;
  title: string;
  model_provider: string;
  model_name: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  context_length?: number;
  is_default?: boolean;
  is_lightweight?: boolean;
}

export interface ProviderDetail {
  id: string;
  name: string;
  provider_type: "local" | "cloud";
  is_configured: boolean;
  is_available: boolean;
  status_message: string;
  default_model: string;
  models: ModelInfo[];
  requires_api_key: boolean;
}

export interface ProvidersStatusResponse {
  active_provider: string;
  default_model: string;
  providers: ProviderDetail[];
  cloud_testing_status: "pending" | "active";
}

export interface ProviderInfo {
  provider: string;
  model_name: string;
  configured: boolean;
  is_local: boolean;
  label: string;
  description: string;
}

export interface ChatRequestPayload {
  session_id?: string;
  message: string;
  model_provider?: string;
  model_name?: string;
  skill?: string;
  agentic?: boolean;
  agent_sdk?: string;
}

export interface Ship30RequestPayload {
  session_id?: string;
  topic: string;
  target_audience?: string;
  model_provider?: string;
  model_name?: string;
}
