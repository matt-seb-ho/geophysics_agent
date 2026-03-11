import {
  ChatSession,
  FileNode,
  Message,
  ModelInfo,
  PersistedSessionState,
  SessionConfig,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:6305";

export async function checkHealth(): Promise<{ api_key_set: boolean }> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function createSession(
  config: SessionConfig & { workspacePath?: string }
): Promise<{ session_id: string; workspace_path: string }> {
  const res = await fetch(`${API_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: config.model,
      provider: config.provider || null,
      max_steps: config.maxSteps,
      workspace_path: config.workspacePath || null,
      enable_logging: config.enableLogging,
      log_dir: config.logDir || null,
      enable_context_compaction: config.enableContextCompaction,
      enable_reasoning: config.enableReasoning,
      enable_prompt_caching: config.enablePromptCaching,
      prompt_cache_ttl: config.promptCacheTtl === "default" ? null : config.promptCacheTtl,
      auto_compact_after_tokens: config.autoCompactAfterTokens,
      temperature: config.temperature,
      top_p: config.topP,
      frequency_penalty: config.frequencyPenalty,
      presence_penalty: config.presencePenalty,
      seed: config.seed ? parseInt(config.seed) : null,
      max_output_tokens: config.maxOutputTokens,
      openrouter_extra_body: config.openrouterExtraBody || null,
    }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  await fetch(`${API_URL}/api/sessions/${sessionId}`, { method: "DELETE" });
}

export async function updateWorkspace(
  sessionId: string,
  path: string
): Promise<{ workspace_path: string }> {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/workspace`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workspace_path: path }),
  });
  if (!res.ok) throw new Error(`Failed to update workspace: ${res.status}`);
  return res.json();
}

export function messageUrl(sessionId: string): string {
  return `${API_URL}/api/sessions/${sessionId}/message`;
}

export async function getFileTree(
  sessionId: string
): Promise<{ tree: FileNode | null; workspace: string }> {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/tree`);
  if (!res.ok) throw new Error(`Failed to get file tree: ${res.status}`);
  return res.json();
}

export async function getModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_URL}/api/models`);
  if (!res.ok) throw new Error(`Failed to get models: ${res.status}`);
  const data = await res.json();
  return (data.models ?? []).map((m: { id: string; context_length?: number }) => ({
    id: m.id,
    contextLength: m.context_length ?? 128000,
  }));
}

export async function getSessions(): Promise<ChatSession[]> {
  const res = await fetch(`${API_URL}/api/chat-sessions`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.sessions ?? [];
}

function normalizeMessage(message: {
  id: string;
  role: "user" | "assistant";
  parts: unknown[];
  timestamp: string;
  streaming?: boolean;
}): Message {
  return {
    id: message.id,
    role: message.role,
    parts: message.parts as Message["parts"],
    timestamp: new Date(message.timestamp),
    streaming: message.streaming,
  };
}

export async function getSessionState(
  sessionId: string
): Promise<PersistedSessionState> {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to get session: ${res.status}`);
  const data = await res.json();
  return {
    sessionId: data.session_id,
    workspacePath: data.workspace_path,
    name: data.name ?? "",
    createdAt: data.created_at ?? undefined,
    lastMessageAt: data.last_message_at ?? undefined,
    pendingInput: data.pending_input ?? null,
    tokenUsage: {
      promptTokens: data.token_usage?.prompt_tokens ?? 0,
      completionTokens: data.token_usage?.completion_tokens ?? 0,
      totalTokens: data.token_usage?.total_tokens ?? 0,
      turnPromptTokens: data.token_usage?.turn_prompt_tokens ?? undefined,
      cachedTokens: data.token_usage?.cached_tokens ?? undefined,
      cacheWriteTokens: data.token_usage?.cache_write_tokens ?? undefined,
      contextTokensEst: data.token_usage?.context_tokens_est ?? undefined,
      compactionThreshold: data.token_usage?.compaction_threshold ?? undefined,
    },
    config: data.config as SessionConfig,
    messageCount: data.message_count ?? 0,
    messages: Array.isArray(data.messages)
      ? data.messages.map(normalizeMessage)
      : [],
  };
}

export async function generateTitle(
  sessionId: string,
  firstMessage: string
): Promise<string> {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/generate-title`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: firstMessage }),
  });
  if (!res.ok) throw new Error(`Failed to generate title: ${res.status}`);
  const data = await res.json();
  return data.title;
}

export async function renameSession(
  sessionId: string,
  name: string
): Promise<string> {
  const res = await fetch(`${API_URL}/api/sessions/${sessionId}/rename`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error(`Failed to rename session: ${res.status}`);
  const data = await res.json();
  return data.title;
}

export async function getFileContent(
  sessionId: string,
  path: string
): Promise<string> {
  const res = await fetch(
    `${API_URL}/api/sessions/${sessionId}/file?path=${encodeURIComponent(path)}`
  );
  if (!res.ok) throw new Error(`Failed to get file: ${res.status}`);
  return res.text();
}

export function fileUrl(sessionId: string, path: string): string {
  return `${API_URL}/api/sessions/${sessionId}/file?path=${encodeURIComponent(path)}`;
}
