"use client";
import { useEffect, useRef, useState } from "react";
import { FolderOpen, PanelLeft } from "lucide-react";
import ChatArea from "../components/ChatArea";
import ChatHistorySidebar from "../components/ChatHistorySidebar";
import FileTree from "../components/FileTree";
import FileViewer from "../components/FileViewer";
import SettingsPanel from "../components/SettingsPanel";
import {
  checkHealth,
  createSession,
  deleteSession,
  generateTitle,
  getModels,
  getSessionState,
  renameSession,
  getSessions,
  messageUrl,
  updateWorkspace,
} from "../lib/api";
import { loadConfig, loadWorkspace, saveConfig, saveWorkspace } from "../lib/config";
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

// ── Per-chat tab state ────────────────────────────────────────────────────────
interface ChatTab {
  tabId: string;
  sessionId: string | null;
  label: string;
  fileCount: number;
}

interface PerChatState {
  sessionId: string | null;
  workspacePath: string;
  messages: Message[];
  tokenUsage: TokenUsage;
  pendingInput: PendingInput | null;
  openTabs: OpenTab[];
  activeFileTab: string | null;
  firstMessageSent: boolean;
  fileCount: number;
}

interface TabContextMenu {
  kind: "chat" | "file";
  targetId: string;
  x: number;
  y: number;
}

function genId() {
  return `t-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
}

const emptyTokenUsage: TokenUsage = { promptTokens: 0, completionTokens: 0, totalTokens: 0 };

export default function HomePage() {
  // ── Chat tabs ──────────────────────────────────────────────────────────────
  const initTabId = genId();
  const [chatTabs, setChatTabs] = useState<ChatTab[]>([{ tabId: initTabId, sessionId: null, label: "new chat", fileCount: 0 }]);
  const [activeChatTabId, setActiveChatTabId] = useState<string>(initTabId);

  // ── Settings tab ───────────────────────────────────────────────────────────
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settingsActive, setSettingsActive] = useState(false);
  const [tabContextMenu, setTabContextMenu] = useState<TabContextMenu | null>(null);
  const [selectedChatTabIds, setSelectedChatTabIds] = useState<string[]>([]);
  const [selectedFileTabIds, setSelectedFileTabIds] = useState<string[]>([]);
  const [chatSelectionAnchorId, setChatSelectionAnchorId] = useState<string | null>(initTabId);
  const [fileSelectionAnchorId, setFileSelectionAnchorId] = useState<string | null>(null);
  const [hoveredTabKey, setHoveredTabKey] = useState<string | null>(null);

  // ── Active chat state ──────────────────────────────────────────────────────
  const [sessionId, setSessionId]       = useState<string | null>(null);
  const [workspacePath, setWorkspacePath] = useState("");
  const [messages, setMessages]         = useState<Message[]>([]);
  const [config, setConfig]             = useState<SessionConfig>(defaultConfig);
  const [tokenUsage, setTokenUsage]     = useState<TokenUsage>(emptyTokenUsage);
  const [pendingInput, setPendingInput] = useState<PendingInput | null>(null);
  const [isStreaming, setIsStreaming]   = useState(false);
  const [openTabs, setOpenTabs]         = useState<OpenTab[]>([]);
  const [activeFileTab, setActiveFileTab] = useState<string | null>(null);
  const [firstMessageSent, setFirstMessageSent] = useState(false);
  const [fileCount, setFileCount]       = useState(0);

  // ── Other state ────────────────────────────────────────────────────────────
  const [showFileTree, setShowFileTree]   = useState(true);
  const [showSidebar, setShowSidebar]     = useState(true);
  const [fileTreeRefreshKey, setFileTreeRefreshKey] = useState(0);
  const [apiKeyMissing, setApiKeyMissing] = useState(false);
  const [sessions, setSessions]           = useState<ChatSession[]>([]);
  const [models, setModels]               = useState<ModelInfo[]>([]);

  // ── Refs ───────────────────────────────────────────────────────────────────
  const perChatRef = useRef<Map<string, PerChatState>>(new Map());
  const sessionIdRef = useRef<string | null>(null);
  sessionIdRef.current = sessionId;
  const activeChatTabIdRef = useRef<string>(initTabId);
  activeChatTabIdRef.current = activeChatTabId;

  // ── Load config + workspace from localStorage ─────────────────────────────
  useEffect(() => {
    setConfig(loadConfig());
    setWorkspacePath(loadWorkspace());
  }, []);

  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === "geos_config" && e.newValue) {
        try { setConfig({ ...defaultConfig, ...JSON.parse(e.newValue) }); } catch {}
      }
      if (e.key === "geos_workspace") setWorkspacePath(e.newValue ?? "");
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  // ── Health + models + sessions ─────────────────────────────────────────────
  useEffect(() => {
    checkHealth().then(({ api_key_set }) => setApiKeyMissing(!api_key_set)).catch(() => {});
    getModels().then(setModels).catch(() => {});
    getSessions().then(setSessions).catch(() => {});
  }, []);

  const currentModel = models.find((m) => m.id === config.model);
  const contextLength = currentModel?.contextLength ?? 0;
  const buildEmptyTabState = (): PerChatState => ({
    sessionId: null,
    workspacePath: loadWorkspace(),
    messages: [],
    tokenUsage: emptyTokenUsage,
    pendingInput: null,
    openTabs: [],
    activeFileTab: null,
    firstMessageSent: false,
    fileCount: 0,
  });

  const getStoredTabState = (tabId: string): PerChatState =>
    perChatRef.current.get(tabId) ?? buildEmptyTabState();

  // ── Save current chat tab state ────────────────────────────────────────────
  const saveCurrentTabState = () => {
    const tid = activeChatTabIdRef.current;
    perChatRef.current.set(tid, {
      sessionId,
      workspacePath,
      messages,
      tokenUsage,
      pendingInput,
      openTabs,
      activeFileTab,
      firstMessageSent,
      fileCount,
    });
  };

  const updateMessagesForTab = (
    tabId: string,
    updater: (prev: Message[]) => Message[]
  ) => {
    if (activeChatTabIdRef.current === tabId) {
      setMessages(updater);
      return;
    }
    const stored = getStoredTabState(tabId);
    perChatRef.current.set(tabId, { ...stored, messages: updater(stored.messages) });
  };

  const updatePendingInputForTab = (tabId: string, next: PendingInput | null) => {
    if (activeChatTabIdRef.current === tabId) {
      setPendingInput(next);
      return;
    }
    const stored = getStoredTabState(tabId);
    perChatRef.current.set(tabId, { ...stored, pendingInput: next });
  };

  const updateTokenUsageForTab = (tabId: string, next: TokenUsage) => {
    if (activeChatTabIdRef.current === tabId) {
      setTokenUsage(next);
      return;
    }
    const stored = getStoredTabState(tabId);
    perChatRef.current.set(tabId, { ...stored, tokenUsage: next });
  };

  const incrementFileCountForTab = (tabId: string, delta: number) => {
    if (delta <= 0) return;
    if (activeChatTabIdRef.current === tabId) {
      setFileCount((prev) => prev + delta);
    } else {
      const stored = getStoredTabState(tabId);
      perChatRef.current.set(tabId, { ...stored, fileCount: stored.fileCount + delta });
    }
    setChatTabs((prev) =>
      prev.map((tab) =>
        tab.tabId === tabId ? { ...tab, fileCount: tab.fileCount + delta } : tab
      )
    );
  };

  const assignSessionToTab = (tabId: string, nextSessionId: string, nextWorkspacePath: string) => {
    if (activeChatTabIdRef.current === tabId) {
      setSessionId(nextSessionId);
      setWorkspacePath(nextWorkspacePath);
    } else {
      const stored = getStoredTabState(tabId);
      perChatRef.current.set(tabId, {
        ...stored,
        sessionId: nextSessionId,
        workspacePath: nextWorkspacePath,
      });
    }
    setChatTabs((prev) =>
      prev.map((tab) =>
        tab.tabId === tabId ? { ...tab, sessionId: nextSessionId } : tab
      )
    );
  };

  // ── Switch to a chat tab ───────────────────────────────────────────────────
  const switchToChatTab = (tabId: string) => {
    if (tabId === activeChatTabId && !settingsActive) return;
    saveCurrentTabState();

    const stored = perChatRef.current.get(tabId);
    if (stored) {
      setSessionId(stored.sessionId);
      setWorkspacePath(stored.workspacePath);
      setMessages(stored.messages);
      setTokenUsage(stored.tokenUsage);
      setPendingInput(stored.pendingInput);
      setOpenTabs(stored.openTabs);
      setActiveFileTab(stored.activeFileTab);
      setFirstMessageSent(stored.firstMessageSent);
      setFileCount(stored.fileCount);
      setFileTreeRefreshKey((k) => k + 1);
    } else {
      // Fresh tab
      setSessionId(null);
      setWorkspacePath(loadWorkspace());
      setMessages([]);
      setTokenUsage(emptyTokenUsage);
      setPendingInput(null);
      setOpenTabs([]);
      setActiveFileTab(null);
      setFirstMessageSent(false);
      setFileCount(0);
    }
    setActiveChatTabId(tabId);
    setChatSelectionAnchorId(tabId);
    setSettingsActive(false);
  };

  // ── Create new chat tab ────────────────────────────────────────────────────
  const handleNewChat = () => {
    saveCurrentTabState();
    const tabId = genId();
    setChatTabs((prev) => [...prev, { tabId, sessionId: null, label: "new chat", fileCount: 0 }]);
    setSessionId(null);
    setWorkspacePath(loadWorkspace());
    setMessages([]);
    setTokenUsage(emptyTokenUsage);
    setPendingInput(null);
    setOpenTabs([]);
    setActiveFileTab(null);
    setFirstMessageSent(false);
    setFileCount(0);
    setActiveChatTabId(tabId);
    setChatSelectionAnchorId(tabId);
    setFileSelectionAnchorId(null);
    setSettingsActive(false);
  };

  // ── Close a chat tab ───────────────────────────────────────────────────────
  const closeChatTab = (tabId: string) => {
    setChatTabs((prev) => {
      const next = prev.filter((t) => t.tabId !== tabId);
      if (next.length === 0) {
        // Always keep at least one tab
        const fresh = { tabId: genId(), sessionId: null, label: "new chat", fileCount: 0 };
        perChatRef.current.delete(tabId);
        // Switch to fresh tab
        setSessionId(null); setWorkspacePath(loadWorkspace()); setMessages([]); setTokenUsage(emptyTokenUsage); setPendingInput(null); setOpenTabs([]); setActiveFileTab(null); setFirstMessageSent(false); setFileCount(0);
        setActiveChatTabId(fresh.tabId);
        setChatSelectionAnchorId(fresh.tabId);
        setFileSelectionAnchorId(null);
        setSettingsActive(false);
        return [fresh];
      }
      if (tabId === activeChatTabId) {
        const idx = prev.findIndex((t) => t.tabId === tabId);
        const nextTab = next[Math.min(idx, next.length - 1)];
        switchToChatTab(nextTab.tabId);
      }
      perChatRef.current.delete(tabId);
      return next;
    });
  };

  // ── Select session from sidebar ────────────────────────────────────────────
  const handleSelectSession = async (id: string) => {
    // Check if session already has an open tab
    const existing = chatTabs.find((t) => t.sessionId === id);
    if (existing) {
      switchToChatTab(existing.tabId);
      return;
    }
    // Open a new tab for this session
    saveCurrentTabState();
    const tabId = genId();
    const session = sessions.find((s) => s.id === id);
    setChatTabs((prev) => [
      ...prev,
      { tabId, sessionId: id, label: session?.name || `Chat ${id.slice(0, 6)}`, fileCount: 0 },
    ]);

    try {
      const persisted = await getSessionState(id);
      const restoredState: PerChatState = {
        sessionId: persisted.sessionId,
        workspacePath: persisted.workspacePath,
        messages: persisted.messages,
        tokenUsage: persisted.tokenUsage,
        pendingInput: persisted.pendingInput,
        openTabs: [],
        activeFileTab: null,
        firstMessageSent: persisted.messages.length > 0,
        fileCount: 0,
      };
      perChatRef.current.set(tabId, restoredState);
      setSessionId(persisted.sessionId);
      setWorkspacePath(persisted.workspacePath);
      setMessages(persisted.messages);
      setTokenUsage(persisted.tokenUsage);
      setPendingInput(persisted.pendingInput);
      setOpenTabs([]);
      setActiveFileTab(null);
      setFirstMessageSent(persisted.messages.length > 0);
      setFileCount(0);
      setChatTabs((prev) =>
        prev.map((tab) =>
          tab.tabId === tabId
            ? { ...tab, label: persisted.name || tab.label }
            : tab
        )
      );
    } catch {
      setSessionId(id);
      setWorkspacePath(session?.workspacePath || loadWorkspace());
      setMessages([]);
      setTokenUsage(emptyTokenUsage);
      setPendingInput(null);
      setOpenTabs([]);
      setActiveFileTab(null);
      setFirstMessageSent(false);
      setFileCount(0);
    }

    setActiveChatTabId(tabId);
    setChatSelectionAnchorId(tabId);
    setFileSelectionAnchorId(null);
    setSettingsActive(false);
    setFileTreeRefreshKey((k) => k + 1);
  };

  // ── Delete session ─────────────────────────────────────────────────────────
  const handleDeleteSession = async (id: string) => {
    deleteSession(id).catch(() => {});
    // Close tab if open
    const tab = chatTabs.find((t) => t.sessionId === id);
    if (tab) closeChatTab(tab.tabId);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  const handleRenameSession = async (id: string, name: string) => {
    try {
      const title = await renameSession(id, name);
      setSessions((prev) =>
        prev.map((session) => (session.id === id ? { ...session, name: title } : session))
      );
      setChatTabs((prev) =>
        prev.map((tab) => (tab.sessionId === id ? { ...tab, label: title } : tab))
      );
    } catch {
      // Ignore failed rename for now; sidebar keeps the prior title.
    }
  };

  // ── Workspace ─────────────────────────────────────────────────────────────
  const handleWorkspaceChange = async (path: string) => {
    setWorkspacePath(path);
    saveWorkspace(path);
    const sid = sessionIdRef.current;
    if (!sid) return;
    try { await updateWorkspace(sid, path); setFileTreeRefreshKey((k) => k + 1); } catch {}
  };

  // ── Settings tab ──────────────────────────────────────────────────────────
  const openSettings = () => {
    if (!settingsOpen) setSettingsOpen(true);
    saveCurrentTabState();
    setSettingsActive(true);
  };
  const closeSettings = () => {
    setSettingsOpen(false);
    setSettingsActive(false);
  };

  // ── File tabs ─────────────────────────────────────────────────────────────
  const handleOpenFile = (path: string, name: string) => {
    setSettingsActive(false);
    if (!openTabs.find((t) => t.path === path)) {
      setOpenTabs((prev) => [...prev, { path, name }]);
    }
    setSelectedFileTabIds([]);
    setActiveFileTab(path);
    setFileSelectionAnchorId(path);
  };

  const handleCloseFileTab = (path: string) => {
    setOpenTabs((prev) => {
      const next = prev.filter((t) => t.path !== path);
      setSelectedFileTabIds((ids) => ids.filter((id) => id !== path));
      setActiveFileTab((cur) => {
        const nextActive = cur === path ? (next[next.length - 1]?.path ?? null) : cur;
        setFileSelectionAnchorId((anchor) => (anchor === path ? nextActive : anchor));
        return nextActive;
      });
      return next;
    });
  };

  // ── Session helpers ───────────────────────────────────────────────────────
  const ensureSession = async (tabId: string, cfg: SessionConfig, wp: string): Promise<string> => {
    const existing =
      activeChatTabIdRef.current === tabId
        ? sessionIdRef.current
        : perChatRef.current.get(tabId)?.sessionId ?? null;
    if (existing) return existing;
    const data = await createSession({ ...cfg, workspacePath: wp });
    const sid = data.session_id;
    assignSessionToTab(tabId, sid, data.workspace_path);
    setSessions((prev) => {
      const now = new Date().toISOString();
      return [
        {
          id: sid,
          name: "",
          createdAt: now,
          lastMessageAt: now,
          messageCount: 0,
          workspacePath: data.workspace_path,
        },
        ...prev.filter((s) => s.id !== sid),
      ];
    });
    return sid;
  };

  // ── Main send / stream ────────────────────────────────────────────────────
  const sendMessage = async (text: string) => {
    if (isStreaming) return;
    const sourceTabId = activeChatTabIdRef.current;
    const promptTokensBeforeSend = tokenUsage.promptTokens;
    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      parts: [{ type: "text", content: text }],
      timestamp: new Date(),
    } satisfies Message;
    const assistantId = crypto.randomUUID();
    const assistantMessage = {
      id: assistantId,
      role: "assistant",
      parts: [],
      timestamp: new Date(),
      streaming: true,
    } satisfies Message;

    setIsStreaming(true);
    const isFirst = !firstMessageSent;
    setFirstMessageSent(true);
    if (pendingInput) setPendingInput(null);
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    perChatRef.current.set(sourceTabId, {
      ...getStoredTabState(sourceTabId),
      sessionId,
      workspacePath,
      messages: [...messages, userMessage, assistantMessage],
      tokenUsage,
      pendingInput: null,
      openTabs,
      activeFileTab,
      firstMessageSent: true,
      fileCount,
    });

    try {
      const sid = await ensureSession(sourceTabId, config, workspacePath);

      if (isFirst) {
        generateTitle(sid, text)
          .then((title) => {
            setSessions((prev) => prev.map((s) => s.id === sid ? { ...s, name: title, lastMessageAt: new Date().toISOString() } : s));
            setChatTabs((prev) => prev.map((t) => t.tabId === sourceTabId ? { ...t, label: title } : t));
            return getSessions();
          })
          .then((fresh) => { if (fresh) setSessions(fresh); })
          .catch(() => {});
      }

      const parts: MessagePart[] = [];
      let currentText = "";
      let currentThinking = "";

      const flushText = () => { if (currentText) { parts.push({ type: "text", content: currentText }); currentText = ""; } };
      const refreshUI = () => {
        const snap: MessagePart[] = [...parts];
        if (currentText) snap.push({ type: "text", content: currentText });
        updateMessagesForTab(sourceTabId, (prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, parts: snap } : m))
        );
      };

      const res = await fetch(messageUrl(sid), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: text }) });
      if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

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
          try { event = JSON.parse(raw); } catch { continue; }
          const type = event.type as string;

          if (type === "text") { currentText += event.data as string; refreshUI(); }
          else if (type === "thinking_start") { flushText(); currentThinking = ""; }
          else if (type === "thinking") { currentThinking += event.data as string; }
          else if (type === "thinking_end") {
            if (currentThinking) { parts.push({ type: "thinking", content: currentThinking }); currentThinking = ""; }
            refreshUI();
          }
          else if (type === "tool_start") { flushText(); const d = event.data as { name: string; summary: string }; parts.push({ type: "tool_call", name: d.name, summary: d.summary, streaming: true }); refreshUI(); }
          else if (type === "tool_result") {
            const d = event.data as { name: string; result: string };
            for (let i = parts.length - 1; i >= 0; i--) { const p = parts[i]; if (p.type === "tool_call" && p.name === d.name) { parts[i] = { ...p, result: d.result, streaming: false }; break; } }
            refreshUI();
          }
          else if (type === "tool_error") {
            const d = event.data as { name: string; error: string };
            for (let i = parts.length - 1; i >= 0; i--) { const p = parts[i]; if (p.type === "tool_call" && p.name === d.name) { parts[i] = { ...p, error: d.error, streaming: false }; break; } }
            refreshUI();
          }
          else if (type === "user_input_required") {
            flushText();
            const q = event.question as string; const c = (event.choices ?? []) as string[];
            const defaultValue = (event.default as string | undefined) ?? undefined;
            const fields = Array.isArray(event.fields) ? (event.fields as PendingInput["fields"]) : undefined;
            const allowCustomInput =
              typeof event.allow_custom_input === "boolean"
                ? (event.allow_custom_input as boolean)
                : undefined;
            updatePendingInputForTab(sourceTabId, {
              question: q,
              choices: c,
              default: defaultValue,
              fields,
              allowCustomInput,
            });
            parts.push({
              type: "question",
              content: q,
              choices: c,
              default: defaultValue,
              fields,
              allowCustomInput,
            });
            refreshUI();
          }
          else if (type === "step_limit") { flushText(); parts.push({ type: "warning", content: `Step limit reached (${event.max_steps} steps). You can continue the conversation.` }); refreshUI(); }
          else if (type === "error") { flushText(); parts.push({ type: "error", content: event.message as string }); refreshUI(); }
          else if (type === "token_usage") {
            updateTokenUsageForTab(sourceTabId, {
              promptTokens:     (event.prompt_tokens     as number) ?? 0,
              completionTokens: (event.completion_tokens as number) ?? 0,
              totalTokens:      (event.total_tokens      as number) ?? 0,
              turnPromptTokens: Math.max(0, ((event.prompt_tokens as number) ?? 0) - promptTokensBeforeSend),
              cachedTokens:     (event.cached_tokens     as number) ?? 0,
              cacheWriteTokens: (event.cache_write_tokens as number) ?? 0,
              contextTokensEst: (event.context_tokens_est as number) ?? undefined,
              compactionThreshold: (event.compaction_threshold as number) ?? undefined,
            });
          }
          else if (type === "new_files") {
            setFileTreeRefreshKey((k) => k + 1);
            incrementFileCountForTab(sourceTabId, ((event.files as string[] | undefined)?.length ?? 0));
          }
        }
      }

      flushText();
      updateMessagesForTab(sourceTabId, (prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, parts, streaming: false, timestamp: new Date() } : m
        )
      );
      getSessions().then(setSessions).catch(() => {});
    } catch (err) {
      updateMessagesForTab(sourceTabId, (prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                parts: [{ type: "error", content: String(err) }],
                streaming: false,
                timestamp: new Date(),
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  // ── fileCounts map for sidebar ────────────────────────────────────────────
  const fileCounts: Record<string, number> = {};
  for (const t of chatTabs) {
    if (t.sessionId) fileCounts[t.sessionId] = t.fileCount;
  }

  // ── Derived ───────────────────────────────────────────────────────────────
  const activeFile = openTabs.find((t) => t.path === activeFileTab) ?? null;

  // Tab style helper
  const tabStyle = (isActive: boolean): React.CSSProperties => ({
    alignSelf: "stretch",
    display: "flex",
    alignItems: "center",
    padding: "0 4px 0 10px",
    border: "none",
    borderBottom: isActive ? "2px solid var(--accent)" : "2px solid transparent",
    background: isActive ? "var(--bg-surface)" : "transparent",
    cursor: "pointer",
    fontFamily: "var(--font-mono)",
    fontSize: "11px",
    gap: 4,
    whiteSpace: "nowrap",
    color: isActive ? "var(--text-bright)" : "var(--text-secondary)",
    flexShrink: 0,
  });

  const getTabShellStyle = (
    isActive: boolean,
    isSelected: boolean
  ): React.CSSProperties => ({
    ...tabStyle(isActive),
    background: isSelected
      ? "var(--accent-bg)"
      : isActive
      ? "var(--bg-surface)"
      : "transparent",
    boxShadow: isSelected ? "inset 0 0 0 1px var(--accent-border)" : "none",
    borderRight: "2px solid var(--border-mid)",
    borderLeft: "2px solid var(--border-faint)",
    marginLeft: -1,
  });

  const closeTabBtnStyle = (visible: boolean): React.CSSProperties => ({
    background: "transparent",
    border: "none",
    cursor: "pointer",
    color: "var(--text-dim)",
    fontFamily: "var(--font-mono)",
    fontSize: "13px",
    padding: "0 4px",
    lineHeight: 1,
    display: "flex",
    alignItems: "center",
    opacity: visible ? 1 : 0,
    pointerEvents: visible ? "auto" : "none",
    transition: "opacity 0.12s ease",
  });

  const openTabContextMenu = (
    e: React.MouseEvent,
    kind: "chat" | "file",
    targetId: string
  ) => {
    e.preventDefault();
    setTabContextMenu({ kind, targetId, x: e.clientX, y: e.clientY });
  };

  const toggleChatTabSelection = (tabId: string) => {
    setSelectedFileTabIds([]);
    setFileSelectionAnchorId(null);
    setChatSelectionAnchorId(tabId);
    setSelectedChatTabIds((prev) =>
      prev.includes(tabId) ? prev.filter((id) => id !== tabId) : [...prev, tabId]
    );
  };

  const toggleFileTabSelection = (tabId: string) => {
    setSelectedChatTabIds([]);
    setChatSelectionAnchorId(null);
    setFileSelectionAnchorId(tabId);
    setSelectedFileTabIds((prev) =>
      prev.includes(tabId) ? prev.filter((id) => id !== tabId) : [...prev, tabId]
    );
  };

  const clearTabSelection = () => {
    setSelectedChatTabIds([]);
    setSelectedFileTabIds([]);
  };

  const selectContiguousChatTabs = (tabId: string) => {
    setSelectedFileTabIds([]);
    setFileSelectionAnchorId(null);
    const anchorId = chatSelectionAnchorId ?? activeChatTabId ?? tabId;
    const anchorIndex = chatTabs.findIndex((tab) => tab.tabId === anchorId);
    const targetIndex = chatTabs.findIndex((tab) => tab.tabId === tabId);
    if (anchorIndex === -1 || targetIndex === -1) {
      setSelectedChatTabIds([tabId]);
      return;
    }
    const start = Math.min(anchorIndex, targetIndex);
    const end = Math.max(anchorIndex, targetIndex);
    setSelectedChatTabIds(chatTabs.slice(start, end + 1).map((tab) => tab.tabId));
  };

  const selectContiguousFileTabs = (tabId: string) => {
    setSelectedChatTabIds([]);
    setChatSelectionAnchorId(null);
    const anchorId = fileSelectionAnchorId ?? activeFileTab ?? tabId;
    const anchorIndex = openTabs.findIndex((tab) => tab.path === anchorId);
    const targetIndex = openTabs.findIndex((tab) => tab.path === tabId);
    if (anchorIndex === -1 || targetIndex === -1) {
      setSelectedFileTabIds([tabId]);
      return;
    }
    const start = Math.min(anchorIndex, targetIndex);
    const end = Math.max(anchorIndex, targetIndex);
    setSelectedFileTabIds(openTabs.slice(start, end + 1).map((tab) => tab.path));
  };

  const getContextTargetIds = (): string[] => {
    if (!tabContextMenu) return [];
    if (tabContextMenu.kind === "chat") {
      return selectedChatTabIds.length > 0 && selectedChatTabIds.includes(tabContextMenu.targetId)
        ? selectedChatTabIds
        : [tabContextMenu.targetId];
    }
    return selectedFileTabIds.length > 0 && selectedFileTabIds.includes(tabContextMenu.targetId)
      ? selectedFileTabIds
      : [tabContextMenu.targetId];
  };

  const closeFileTabsByIds = (ids: string[]) => {
    if (ids.length === 0) return;
    const next = openTabs.filter((tab) => !ids.includes(tab.path));
    setOpenTabs(next);
    setSelectedFileTabIds((prev) => prev.filter((id) => !ids.includes(id)));
    if (ids.includes(activeFileTab ?? "")) {
      const nextActive = next[next.length - 1]?.path ?? null;
      setActiveFileTab(nextActive);
      setFileSelectionAnchorId(nextActive);
      return;
    }
    setFileSelectionAnchorId((anchor) => (anchor && ids.includes(anchor) ? activeFileTab ?? next[next.length - 1]?.path ?? null : anchor));
  };

  const closeChatTabsByIds = (ids: string[]) => {
    if (ids.length === 0) return;
    const remaining = chatTabs.filter((tab) => !ids.includes(tab.tabId));
    ids.forEach((id) => perChatRef.current.delete(id));
    setSelectedChatTabIds((prev) => prev.filter((id) => !ids.includes(id)));

    if (remaining.length === 0) {
      const fresh = { tabId: genId(), sessionId: null, label: "new chat", fileCount: 0 };
      setChatTabs([fresh]);
      setSelectedChatTabIds([]);
      setSessionId(null);
      setWorkspacePath(loadWorkspace());
      setMessages([]);
      setTokenUsage(emptyTokenUsage);
      setPendingInput(null);
      setOpenTabs([]);
      setActiveFileTab(null);
      setFirstMessageSent(false);
      setFileCount(0);
      setActiveChatTabId(fresh.tabId);
      setChatSelectionAnchorId(fresh.tabId);
      setFileSelectionAnchorId(null);
      setSettingsActive(false);
      return;
    }

    const activeWasClosed = ids.includes(activeChatTabId);
    setChatTabs(remaining);
    if (activeWasClosed) {
      const closedIndex = chatTabs.findIndex((tab) => tab.tabId === activeChatTabId);
      const nextTab = remaining[Math.min(closedIndex, remaining.length - 1)];
      const stored = getStoredTabState(nextTab.tabId);
      setSessionId(stored.sessionId);
      setWorkspacePath(stored.workspacePath);
      setMessages(stored.messages);
      setTokenUsage(stored.tokenUsage);
      setPendingInput(stored.pendingInput);
      setOpenTabs(stored.openTabs);
      setActiveFileTab(stored.activeFileTab);
      setFirstMessageSent(stored.firstMessageSent);
      setFileCount(stored.fileCount);
      setActiveChatTabId(nextTab.tabId);
      setChatSelectionAnchorId(nextTab.tabId);
      setFileSelectionAnchorId(stored.activeFileTab);
      setSettingsActive(false);
      setFileTreeRefreshKey((k) => k + 1);
      return;
    }
    setChatSelectionAnchorId((anchor) => (anchor && ids.includes(anchor) ? activeChatTabId : anchor));
  };

  useEffect(() => {
    if (!tabContextMenu) return;
    const close = () => setTabContextMenu(null);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, [tabContextMenu]);

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: "var(--bg-base)" }}>
      {showSidebar && (
        <ChatHistorySidebar
          sessions={sessions}
          activeSessionId={sessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onOpenSettings={openSettings}
          onDeleteSession={handleDeleteSession}
          onRenameSession={handleRenameSession}
          tokenUsage={tokenUsage}
          isStreaming={isStreaming}
          apiKeyMissing={apiKeyMissing}
          contextLength={contextLength}
          fileCounts={fileCounts}
        />
      )}

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, height: "100%" }}>
        {/* Tab bar */}
        <div
          style={{
            display: "flex",
            alignItems: "stretch",
            minHeight: "var(--header-h)",
            background: "var(--bg-panel)",
            borderBottom: "1px solid var(--border-subtle)",
            overflowX: "auto",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "0 18px 0 10px", flexShrink: 0 }}>
            <button
              onClick={() => setShowSidebar((prev) => !prev)}
              onMouseDown={() => clearTabSelection()}
              title={showSidebar ? "Hide chat history" : "Show chat history"}
              style={{
                background: showSidebar ? "var(--accent-bg)" : "transparent",
                border: `1px solid ${showSidebar ? "var(--accent-border)" : "var(--border-mid)"}`,
                borderRadius: 2,
                cursor: "pointer",
                color: showSidebar ? "var(--accent)" : "var(--text-secondary)",
                width: 28,
                height: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <PanelLeft size={17} />
            </button>
            <button
              onClick={() => setShowFileTree((v) => !v)}
              onMouseDown={() => clearTabSelection()}
              title="Toggle file tree"
              style={{
                background: showFileTree ? "var(--accent-bg)" : "transparent",
                border: `1px solid ${showFileTree ? "var(--accent-border)" : "var(--border-mid)"}`,
                borderRadius: 2,
                cursor: "pointer",
                color: showFileTree ? "var(--accent)" : "var(--text-secondary)",
                width: 28,
                height: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <FolderOpen size={17} />
            </button>
          </div>

          {/* Chat tabs */}
          {chatTabs.map((tab) => {
            const isActive = tab.tabId === activeChatTabId && !settingsActive && !activeFileTab;
            const isSelected = selectedChatTabIds.includes(tab.tabId);
            const tabKey = `chat:${tab.tabId}`;
            return (
              <div
                key={tab.tabId}
                style={getTabShellStyle(isActive, isSelected)}
                onContextMenu={(e) => openTabContextMenu(e, "chat", tab.tabId)}
                onMouseEnter={() => setHoveredTabKey(tabKey)}
                onMouseLeave={() => setHoveredTabKey((current) => (current === tabKey ? null : current))}
              >
                <button
                  onClick={(e) => {
                    if (e.shiftKey) {
                      selectContiguousChatTabs(tab.tabId);
                      return;
                    }
                    if (e.metaKey || e.ctrlKey) {
                      toggleChatTabSelection(tab.tabId);
                      return;
                    }
                    clearTabSelection();
                    setChatSelectionAnchorId(tab.tabId);
                    setFileSelectionAnchorId(null);
                    if (tab.tabId === activeChatTabId) {
                      setSettingsActive(false);
                      setActiveFileTab(null);
                      return;
                    }
                    switchToChatTab(tab.tabId);
                  }}
                  title={tab.label}
                  style={{ background: "transparent", border: "none", cursor: "pointer", color: "inherit", fontFamily: "var(--font-mono)", fontSize: "11px", padding: 0, maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                >
                  {tab.label}
                </button>
                {chatTabs.length > 1 && (
                  <button onClick={() => closeChatTab(tab.tabId)} style={closeTabBtnStyle(hoveredTabKey === tabKey)} title="Close tab">×</button>
                )}
              </div>
            );
          })}

          {/* File tabs (for active chat) */}
          {openTabs.map((tab) => {
            const isActive = !settingsActive && tab.path === activeFileTab;
            const isSelected = selectedFileTabIds.includes(tab.path);
            const tabKey = `file:${tab.path}`;
            return (
              <div
                key={tab.path}
                style={getTabShellStyle(isActive, isSelected)}
                onContextMenu={(e) => openTabContextMenu(e, "file", tab.path)}
                onMouseEnter={() => setHoveredTabKey(tabKey)}
                onMouseLeave={() => setHoveredTabKey((current) => (current === tabKey ? null : current))}
              >
                <button onClick={(e) => {
                  if (e.shiftKey) {
                    selectContiguousFileTabs(tab.path);
                    return;
                  }
                  if (e.metaKey || e.ctrlKey) {
                    toggleFileTabSelection(tab.path);
                    return;
                  }
                  clearTabSelection();
                  setChatSelectionAnchorId(null);
                  setFileSelectionAnchorId(tab.path);
                  setSettingsActive(false);
                  setActiveFileTab(tab.path);
                }} style={{ background: "transparent", border: "none", cursor: "pointer", color: "inherit", fontFamily: "var(--font-mono)", fontSize: "11px", padding: 0, maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={tab.path}>
                  {tab.name}
                </button>
                <button onClick={() => handleCloseFileTab(tab.path)} style={closeTabBtnStyle(hoveredTabKey === tabKey)}>×</button>
              </div>
            );
          })}

          {/* Settings tab */}
          {settingsOpen && (
            <div
              style={getTabShellStyle(settingsActive, false)}
              onMouseEnter={() => setHoveredTabKey("settings")}
              onMouseLeave={() => setHoveredTabKey((current) => (current === "settings" ? null : current))}
            >
              <button onClick={openSettings} style={{ background: "transparent", border: "none", cursor: "pointer", color: "inherit", fontFamily: "var(--font-mono)", fontSize: "11px", padding: 0 }}>
                settings
              </button>
              <button onClick={closeSettings} style={closeTabBtnStyle(hoveredTabKey === "settings")}>×</button>
            </div>
          )}
        </div>

        {/* Content area */}
        <div style={{ flex: 1, minHeight: 0 }}>
          {settingsActive ? (
            <SettingsPanel
              config={config}
              setConfig={(c) => { setConfig(c); saveConfig(c); }}
              workspacePath={workspacePath}
              onWorkspaceChange={handleWorkspaceChange}
            />
          ) : activeFile ? (
            <FileViewer
              file={activeFile}
              sessionId={sessionId}
            />
          ) : (
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
          )}
        </div>
      </div>

      {showFileTree && (
        <FileTree
          sessionId={sessionId}
          refreshKey={fileTreeRefreshKey}
          workspacePath={workspacePath}
          onOpenFile={handleOpenFile}
        />
      )}
      {tabContextMenu && (
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            position: "fixed",
            top: tabContextMenu.y,
            left: tabContextMenu.x,
            background: "var(--bg-surface)",
            border: "1px solid var(--border-mid)",
            borderRadius: 4,
            boxShadow: "0 10px 28px rgba(0,0,0,0.18)",
            padding: 4,
            zIndex: 300,
            width: "max-content",
            minWidth: 0,
          }}
        >
          {[
            {
              label: "Close",
              onClick: () => {
                const ids = getContextTargetIds();
                if (tabContextMenu.kind === "chat") closeChatTabsByIds(ids);
                else closeFileTabsByIds(ids);
              },
            },
            {
              label: "Close Tabs To The Right",
              onClick: () => {
                if (tabContextMenu.kind === "chat") {
                  const idx = chatTabs.findIndex((tab) => tab.tabId === tabContextMenu.targetId);
                  const base = getContextTargetIds();
                  const right = chatTabs.slice(idx + 1).map((tab) => tab.tabId);
                  closeChatTabsByIds(Array.from(new Set([...base, ...right])));
                } else {
                  const idx = openTabs.findIndex((tab) => tab.path === tabContextMenu.targetId);
                  const base = getContextTargetIds();
                  const right = openTabs.slice(idx + 1).map((tab) => tab.path);
                  closeFileTabsByIds(Array.from(new Set([...base, ...right])));
                }
              },
            },
            {
              label: "Close Other Tabs",
              onClick: () => {
                if (tabContextMenu.kind === "chat") {
                  const keep = new Set(getContextTargetIds());
                  closeChatTabsByIds(chatTabs.filter((tab) => !keep.has(tab.tabId)).map((tab) => tab.tabId));
                } else {
                  const keep = new Set(getContextTargetIds());
                  closeFileTabsByIds(openTabs.filter((tab) => !keep.has(tab.path)).map((tab) => tab.path));
                }
              },
            },
            {
              label: "Close All Tabs",
              onClick: () => {
                if (tabContextMenu.kind === "chat") {
                  closeChatTabsByIds(chatTabs.map((tab) => tab.tabId));
                } else {
                  closeFileTabsByIds(openTabs.map((tab) => tab.path));
                }
              },
            },
          ].map((item) => (
            <button
              key={item.label}
              onClick={() => {
                item.onClick();
                setTabContextMenu(null);
              }}
              style={{
                display: "block",
                background: "transparent",
                border: "none",
                color: "var(--text-primary)",
                textAlign: "left",
                padding: "7px 10px",
                fontFamily: "var(--font-mono)",
                fontSize: "11.5px",
                cursor: "pointer",
                borderRadius: 2,
                whiteSpace: "nowrap",
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
