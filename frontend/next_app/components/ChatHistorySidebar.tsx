"use client";
import { useEffect, useState } from "react";
import { File, Plus, Settings } from "lucide-react";
import { ChatSession, TokenUsage } from "../lib/types";

interface Props {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onOpenSettings: () => void;
  onDeleteSession: (id: string) => void;
  onRenameSession: (id: string, name: string) => void;
  onToggleSidebar?: () => void;
  tokenUsage: TokenUsage;
  isStreaming: boolean;
  apiKeyMissing: boolean;
  contextLength: number;
  fileCounts: Record<string, number>;
}

function ContextBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "10.5px" }}>context</span>
        <span style={{ color: "var(--text-primary)", fontSize: "10.5px" }}>
          {value.toLocaleString()} / {max.toLocaleString()}
        </span>
      </div>
      <div style={{ height: 3, background: "var(--border-mid)", borderRadius: 1, overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: pct > 85 ? "var(--error)" : pct > 65 ? "var(--warning)" : "var(--accent)",
            borderRadius: 1,
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}

function TokenRow({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", marginBottom: 2 }}>
      <span style={{ color: "var(--text-secondary)" }}>{label}</span>
      <span
        style={{
          color: value > 0 ? (color ?? "var(--text-primary)") : "var(--text-dim)",
          fontWeight: value > 0 ? 500 : 400,
        }}
      >
        {value.toLocaleString()}
      </span>
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const d = new Date(dateStr).getTime();
  const diffMs = now - d;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function ChatHistorySidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onOpenSettings,
  onDeleteSession,
  onRenameSession,
  tokenUsage,
  apiKeyMissing,
  contextLength,
  fileCounts,
}: Props) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftName, setDraftName] = useState("");
  const [contextMenu, setContextMenu] = useState<{ id: string; x: number; y: number } | null>(null);
  const contextMax = contextLength > 0 ? contextLength : 128000;
  const contextValue = tokenUsage.turnPromptTokens ?? 0;

  useEffect(() => {
    if (!contextMenu) return;
    const close = () => setContextMenu(null);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, [contextMenu]);

  const startRename = (session: ChatSession) => {
    setEditingId(session.id);
    setDraftName(session.name || `Chat ${session.id.slice(0, 6)}`);
  };

  const commitRename = () => {
    if (!editingId) return;
    const next = draftName.trim();
    if (next) {
      onRenameSession(editingId, next);
    }
    setEditingId(null);
    setDraftName("");
  };

  return (
    <div
      style={{
        width: "var(--sidebar-w)",
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        background: "var(--bg-panel)",
        borderRight: "1px solid var(--border-strong)",
        boxShadow: "1px 0 0 var(--border-faint)",
        height: "100%",
      }}
    >
      <div
        style={{
          padding: "0 12px",
          height: "var(--header-h)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--border-subtle)",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "var(--accent)", fontSize: "14px", fontWeight: 600 }}>GEOS</span>
          <span style={{ color: "var(--text-dim)", fontSize: "12px" }}>agent v1.0</span>
        </div>
        <button
          onClick={onNewChat}
          title="New chat"
          style={{
            background: "transparent",
            border: "1px solid var(--border-mid)",
            borderRadius: 2,
            cursor: "pointer",
            color: "var(--text-secondary)",
            display: "flex",
            alignItems: "center",
            padding: "2px 5px",
          }}
        >
          <Plus size={13} />
        </button>
      </div>

      {apiKeyMissing && (
        <div
          style={{
            margin: "8px 12px 0",
            background: "var(--error-bg)",
            border: "1px solid var(--error)",
            borderRadius: 2,
            padding: "6px 8px",
            color: "var(--error)",
            fontSize: "12px",
          }}
        >
          OPENROUTER_API_KEY not set
        </div>
      )}

      <div style={{ flex: 1, overflowY: "auto", padding: "6px 0" }}>
        {sessions.length === 0 ? (
          <div style={{ padding: "20px 12px", color: "var(--text-dim)", fontSize: "12px", textAlign: "center" }}>
            no conversations yet
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            const fileCount = fileCounts[session.id] ?? 0;
            return (
              <div
                key={session.id}
                onContextMenu={(e) => {
                  e.preventDefault();
                  setContextMenu({ id: session.id, x: e.clientX, y: e.clientY });
                }}
                style={{
                  display: "flex",
                  width: "100%",
                  background: isActive ? "var(--accent-bg)" : "transparent",
                  borderLeft: isActive ? "2px solid var(--accent)" : "2px solid transparent",
                }}
              >
                <button
                  onClick={() => onSelectSession(session.id)}
                  onDoubleClick={() => startRename(session)}
                  style={{
                    flex: 1,
                    minWidth: 0,
                    padding: "6px 8px 6px 12px",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    fontFamily: "var(--font-mono)",
                    textAlign: "left",
                  }}
                >
                  {editingId === session.id ? (
                    <input
                      autoFocus
                      value={draftName}
                      onChange={(e) => setDraftName(e.target.value)}
                      onBlur={commitRename}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") commitRename();
                        if (e.key === "Escape") {
                          setEditingId(null);
                          setDraftName("");
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        width: "100%",
                        background: "var(--bg-surface)",
                        border: "1px solid var(--accent-border)",
                        color: "var(--text-primary)",
                        padding: "3px 6px",
                        borderRadius: 2,
                        fontFamily: "var(--font-mono)",
                        fontSize: "12px",
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        color: isActive ? "var(--accent)" : "var(--text-primary)",
                        fontSize: "12.5px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        fontWeight: isActive ? 500 : 400,
                      }}
                    >
                      {session.name || `Chat ${session.id.slice(0, 6)}`}
                    </div>
                  )}
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      color: "var(--text-dim)",
                      fontSize: "11px",
                      marginTop: 1,
                      alignItems: "center",
                    }}
                  >
                    <span>{formatRelativeTime(session.lastMessageAt)}</span>
                    {fileCount > 0 && (
                      <span style={{ display: "flex", alignItems: "center", gap: 2 }}>
                        <File size={9} />
                        {fileCount}
                      </span>
                    )}
                  </div>
                </button>
              </div>
            );
          })
        )}
      </div>

      <div style={{ borderTop: "1px solid var(--border-subtle)", padding: "10px 12px", flexShrink: 0 }}>
        <div
          style={{
            color: "var(--text-dim)",
            fontSize: "9.5px",
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom: 6,
          }}
        >
          token usage
        </div>
        <ContextBar value={contextValue} max={contextMax} />
        <TokenRow label="input" value={tokenUsage.promptTokens} color="var(--accent)" />
        <TokenRow label="output" value={tokenUsage.completionTokens} color="var(--info)" />
        <TokenRow label="total" value={tokenUsage.totalTokens} />
        {(tokenUsage.cachedTokens !== undefined && tokenUsage.cachedTokens > 0) && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: "10px",
              color: "var(--text-dim)",
              marginTop: 1,
            }}
          >
            <span>cache r/w</span>
            <span>
              {(tokenUsage.cachedTokens ?? 0).toLocaleString()} / {(tokenUsage.cacheWriteTokens ?? 0).toLocaleString()}
            </span>
          </div>
        )}
        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 10 }}>
          <button
            onClick={onOpenSettings}
            title="Settings"
            style={{
              background: "transparent",
              border: "1px solid var(--border-mid)",
              borderRadius: 2,
              cursor: "pointer",
              color: "var(--text-secondary)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 28,
              height: 28,
            }}
          >
            <Settings size={13} />
          </button>
        </div>
      </div>
      {contextMenu && (
        <div
          style={{
            position: "fixed",
            top: contextMenu.y,
            left: contextMenu.x,
            background: "var(--bg-surface)",
            border: "1px solid var(--border-mid)",
            borderRadius: 4,
            boxShadow: "0 10px 28px rgba(0,0,0,0.18)",
            padding: 4,
            zIndex: 310,
            minWidth: 112,
          }}
        >
          {[
            {
              label: "Rename",
              onClick: () => {
                const target = sessions.find((session) => session.id === contextMenu.id);
                if (target) startRename(target);
              },
            },
            {
              label: "Delete",
              onClick: () => onDeleteSession(contextMenu.id),
            },
          ].map((item) => (
            <button
              key={item.label}
              onClick={() => {
                item.onClick();
                setContextMenu(null);
              }}
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                color: "var(--text-primary)",
                textAlign: "left",
                padding: "7px 10px",
                fontFamily: "var(--font-mono)",
                fontSize: "11.5px",
                cursor: "pointer",
                borderRadius: 2,
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
