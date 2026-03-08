import { ChatSession, FileNode, ModelInfo, SessionConfig } from "./types";

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
