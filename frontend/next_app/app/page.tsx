"use client";
import { useEffect, useRef, useState } from "react";
import ChatArea from "../components/ChatArea";
import ChatHistorySidebar from "../components/ChatHistorySidebar";
import FileTree from "../components/FileTree";
import FileViewer from "../components/FileViewer";
import SettingsModal from "../components/SettingsModal";
import {
  checkHealth,
  createSession,
  deleteSession,
  generateTitle,
  getModels,
  getSessions,
  messageUrl,
  updateWorkspace,
} from "../lib/api";
import {
  ChatSession,
  defaultConfig,
  Message,
  MessagePart,
  ModelInfo,
  OpenTab,
  PendingInput,
  SessionConfig,
  TokenUsage,
} from "../lib/types";

export default function HomePage() {
  const [sessionId, setSessionId]     = useState<string | null>(null);
  const [workspacePath, setWorkspacePath] = useState("");
  const [messages, setMessages]       = useState<Message[]>([]);
  const [config, setConfig]           = useState<SessionConfig>(defaultConfig);
  const [tokenUsage, setTokenUsage]   = useState<TokenUsage>({
    promptTokens: 0, completionTokens: 0, totalTokens: 0,
  });
  const [pendingInput, setPendingInput] = useState<PendingInput | null>(null);
  const [isStreaming, setIsStreaming]  = useState(false);
  const [showFileTree, setShowFileTree] = useState(false);
  const [fileTreeRefreshKey, setFileTreeRefreshKey] = useState(0);
  const [apiKeyMissing, setApiKeyMissing] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [openTabs, setOpenTabs] = useState<OpenTab[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [showFileViewer, setShowFileViewer] = useState(false);
  const [firstMessageSent, setFirstMessageSent] = useState(false);

  // Stable ref so async streaming closures see the latest sessionId
  const sessionIdRef = useRef<string | null>(null);
  sessionIdRef.current = sessionId;

  // ── Health check + load models + sessions ──────────────────────────────
  useEffect(() => {
    checkHealth()
      .then(({ api_key_set }) => setApiKeyMissing(!api_key_set))
      .catch(() => {});

    getModels()
      .then((m) => setModels(m))
      .catch(() => {});

    getSessions()
      .then((s) => setSessions(s))
      .catch(() => {});
  }, []);

  // ── Derive context length from current model ─────────────────────────
  const currentModel = models.find((m) => m.id === config.model);
  const contextLength = currentModel?.contextLength ?? 0;

  // ── Session helpers ───────────────────────────────────────────────────
  const ensureSession = async (cfg: SessionConfig, wp: string): Promise<string> => {
    const existing = sessionIdRef.current;
    if (existing) return existing;

    const data = await createSession({ ...cfg, workspacePath: wp });
    setSessionId(data.session_id);
    setWorkspacePath(data.workspace_path);
    return data.session_id;
  };

  const handleNewChat = async () => {
    const old = sessionIdRef.current;
    setMessages([]);
    setTokenUsage({ promptTokens: 0, completionTokens: 0, totalTokens: 0 });
    setPendingInput(null);
    setSessionId(null);
    setWorkspacePath("");
    setOpenTabs([]);
    setActiveTab(null);
    setShowFileViewer(false);
    setFirstMessageSent(false);
    if (old) deleteSession(old).catch(() => {});
    // Refresh sessions list
    getSessions().then((s) => setSessions(s)).catch(() => {});
  };

  const handleWorkspaceChange = async (path: string) => {
    setWorkspacePath(path);
    const sid = sessionIdRef.current;
    if (!sid) return;
    try {
      await updateWorkspace(sid, path);
      setFileTreeRefreshKey((k) => k + 1);
    } catch {
      /* invalid path */
    }
  };

  const handleSelectSession = (id: string) => {
    // For now just highlight — full reload would need backend message storage
    if (id === sessionId) return;
  };

  // ── File tab management ─────────────────────────────────────────────
  const handleOpenFile = (path: string, name: string) => {
    if (!openTabs.find((t) => t.path === path)) {
      setOpenTabs((prev) => [...prev, { path, name }]);
    }
    setActiveTab(path);
    setShowFileViewer(true);
  };

  const handleCloseTab = (path: string) => {
    setOpenTabs((prev) => {
      const next = prev.filter((t) => t.path !== path);
      if (activeTab === path) {
        setActiveTab(next.length > 0 ? next[next.length - 1].path : null);
        if (next.length === 0) setShowFileViewer(false);
      }
      return next;
    });
  };

  // ── Main send / stream ────────────────────────────────────────────────
  const sendMessage = async (text: string) => {
    if (isStreaming) return;
    setIsStreaming(true);

    const isFirst = !firstMessageSent;
    setFirstMessageSent(true);

    // Clear pending input immediately
    if (pendingInput) setPendingInput(null);

    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        parts: [{ type: "text", content: text }],
        timestamp: new Date(),
      } satisfies Message,
    ]);

    // Add streaming assistant placeholder
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        parts: [],
        timestamp: new Date(),
        streaming: true,
      } satisfies Message,
    ]);

    try {
      const sid = await ensureSession(config, workspacePath);

      // Auto-generate title after first message
      if (isFirst) {
        generateTitle(sid, text)
          .then((title) => {
            setSessions((prev) =>
              prev.map((s) => (s.id === sid ? { ...s, name: title } : s))
            );
          })
          .catch(() => {});
      }

      // ── Local streaming state (mutable, not React state) ──────────────
      const parts: MessagePart[] = [];
      let currentText     = "";
      let currentThinking = "";

      const flushText = () => {
        if (currentText) {
          parts.push({ type: "text", content: currentText });
          currentText = "";
        }
      };

      const refreshUI = () => {
        const snapshot: MessagePart[] = [...parts];
        if (currentText) snapshot.push({ type: "text", content: currentText });
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, parts: snapshot } : m
          )
        );
      };

      // ── Fetch SSE stream ───────────────────────────────────────────────
      const res = await fetch(messageUrl(sid), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`${res.status} ${res.statusText}`);
      }

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer    = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let event: Record<string, unknown>;
          try {
            event = JSON.parse(raw);
          } catch {
            continue;
          }

          const type = event.type as string;

          if (type === "text") {
            currentText += event.data as string;
            refreshUI();
          } else if (type === "thinking_start") {
            flushText();
            currentThinking = "";
          } else if (type === "thinking") {
            currentThinking += event.data as string;
          } else if (type === "thinking_end") {
            if (currentThinking) {
              parts.push({ type: "thinking", content: currentThinking });
              currentThinking = "";
            }
            refreshUI();
          } else if (type === "tool_start") {
            flushText();
            const d = event.data as { name: string; summary: string };
            parts.push({ type: "tool_call", name: d.name, summary: d.summary, streaming: true });
            refreshUI();
          } else if (type === "tool_result") {
            const d = event.data as { name: string; result: string };
            for (let i = parts.length - 1; i >= 0; i--) {
              const p = parts[i];
              if (p.type === "tool_call" && p.name === d.name) {
                parts[i] = { ...p, result: d.result, streaming: false };
                break;
              }
            }
            refreshUI();
          } else if (type === "tool_error") {
            const d = event.data as { name: string; error: string };
            for (let i = parts.length - 1; i >= 0; i--) {
              const p = parts[i];
              if (p.type === "tool_call" && p.name === d.name) {
                parts[i] = { ...p, error: d.error, streaming: false };
                break;
              }
            }
            refreshUI();
          } else if (type === "user_input_required") {
            flushText();
            const q = event.question as string;
            const c = (event.choices ?? []) as string[];
            setPendingInput({ question: q, choices: c });
            parts.push({ type: "question", content: q, choices: c });
            refreshUI();
          } else if (type === "step_limit") {
            flushText();
            parts.push({
              type: "warning",
              content: `Step limit reached (${event.max_steps} steps). You can continue the conversation.`,
            });
            refreshUI();
          } else if (type === "error") {
            flushText();
            parts.push({ type: "error", content: event.message as string });
            refreshUI();
          } else if (type === "token_usage") {
            setTokenUsage({
              promptTokens:     (event.prompt_tokens     as number) ?? 0,
              completionTokens: (event.completion_tokens as number) ?? 0,
              totalTokens:      (event.total_tokens      as number) ?? 0,
              contextTokensEst: (event.context_tokens_est as number) ?? undefined,
              compactionThreshold: (event.compaction_threshold as number) ?? undefined,
            });
          } else if (type === "new_files") {
            setFileTreeRefreshKey((k) => k + 1);
          }
          // keepalive, done, stream_end — no action needed
        }
      }

      // ── Finalize ───────────────────────────────────────────────────────
      flushText();
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, parts, streaming: false } : m
        )
      );

      // Refresh sessions after message
      getSessions().then((s) => setSessions(s)).catch(() => {});
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                parts: [{ type: "error", content: String(err) }],
                streaming: false,
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  // ── Layout ────────────────────────────────────────────────────────────
  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        overflow: "hidden",
        background: "var(--bg-base)",
      }}
    >
      {showSidebar && (
        <ChatHistorySidebar
          sessions={sessions}
          activeSessionId={sessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onOpenSettings={() => setShowSettings(true)}
          tokenUsage={tokenUsage}
          isStreaming={isStreaming}
          apiKeyMissing={apiKeyMissing}
          contextLength={contextLength}
        />
      )}

      <ChatArea
        messages={messages}
        isStreaming={isStreaming}
        pendingInput={pendingInput}
        sessionId={sessionId}
        onSend={sendMessage}
        onToggleFileTree={() => setShowFileTree((v) => !v)}
        showFileTree={showFileTree}
        onToggleSidebar={() => setShowSidebar((v) => !v)}
        showSidebar={showSidebar}
      />

      {showFileTree && (
        showFileViewer && openTabs.length > 0 ? (
          <FileViewer
            tabs={openTabs}
            activeTab={activeTab}
            sessionId={sessionId}
            onSelectTab={setActiveTab}
            onCloseTab={handleCloseTab}
            onBackToTree={() => setShowFileViewer(false)}
          />
        ) : (
          <FileTree
            sessionId={sessionId}
            refreshKey={fileTreeRefreshKey}
            workspacePath={workspacePath}
            onOpenFile={handleOpenFile}
          />
        )
      )}

      <SettingsModal
        open={showSettings}
        onOpenChange={setShowSettings}
        config={config}
        setConfig={setConfig}
        workspacePath={workspacePath}
        onWorkspaceChange={handleWorkspaceChange}
      />
    </div>
  );
}
