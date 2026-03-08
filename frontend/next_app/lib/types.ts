export type MessagePart =
  | { type: "text"; content: string; streaming?: boolean }
  | { type: "thinking"; content: string }
  | { type: "tool_call"; name: string; summary: string; streaming?: boolean; result?: string; error?: string }
  | { type: "question"; content: string; choices?: string[] }
  | { type: "error"; content: string }
  | { type: "warning"; content: string }
  | { type: "image"; path: string; caption?: string }
  | { type: "dataframe"; path: string; caption?: string };

export interface Message {
  id: string;
  role: "user" | "assistant";
  parts: MessagePart[];
  timestamp: Date;
  streaming?: boolean;
}

export interface PendingInput {
  question: string;
  choices?: string[];
}

export interface SessionConfig {
  model: string;
  provider: string;
  maxSteps: number;
  enableContextCompaction: boolean;
  enableLogging: boolean;
  logDir: string;
  workspacePath?: string;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  contextTokensEst?: number;
  compactionThreshold?: number;
}

export interface FileNode {
  name: string;
  path: string;
  type: "directory" | "file";
  size?: number;
  modified?: number;
  children?: FileNode[];
}

export const AVAILABLE_MODELS: string[] = [
  "moonshotai/kimi-k2.5",
  "z-ai/glm-5",
  "anthropic/claude-sonnet-4.6",
  "openai/gpt-5.2",
  "google/gemini-3.1-pro-preview",
  "openai/gpt-5.3-codex",
  "deepseek/deepseek-v3.2",
  "openai/gpt-5-mini",
  "anthropic/claude-haiku-4.5",
  "qwen/qwen3-coder-next",
  "google/gemini-3-flash-preview",
  "google/gemini-3.1-flash-lite-preview",
];

export interface ChatSession {
  id: string;
  name: string;
  createdAt: string;
  lastMessageAt: string;
  messageCount: number;
}

export interface ModelInfo {
  id: string;
  contextLength: number;
}

export interface OpenTab {
  path: string;
  name: string;
}

export const defaultConfig: SessionConfig = {
  model: "moonshotai/kimi-k2.5",
  provider: "",
  maxSteps: 100,
  enableContextCompaction: true,
  enableLogging: true,
  logDir: "data/eval/jsonl_logs",
};
