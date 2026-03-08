"use client";
import { Settings, Plus, MessageSquare } from "lucide-react";
import { ChatSession, TokenUsage } from "../lib/types";

interface Props {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onOpenSettings: () => void;
  tokenUsage: TokenUsage;
  isStreaming: boolean;
  apiKeyMissing: boolean;
  contextLength: number;
}

function TokenBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div style={{ marginBottom: 5 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: 2,
        }}
      >
        <span style={{ color: "var(--text-secondary)", fontSize: "10.5px" }}>
          {label}
        </span>
        <span style={{ color: "var(--text-primary)", fontSize: "10.5px" }}>
          {value.toLocaleString()}
        </span>
      </div>
      <div
        style={{
          height: 3,
          background: "var(--border-mid)",
          borderRadius: 1,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: color,
            borderRadius: 1,
            transition: "width 0.3s ease",
          }}
        />
      </div>
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
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function ChatHistorySidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onOpenSettings,
  tokenUsage,
  isStreaming,
  apiKeyMissing,
  contextLength,
}: Props) {
  const maxTokens = contextLength > 0 ? contextLength : Math.max(tokenUsage.totalTokens * 1.2, 10000);

  return (
    <div
      style={{
        width: "var(--sidebar-w)",
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        background: "var(--bg-panel)",
        borderRight: "1px solid var(--border-subtle)",
        height: "100%",
      }}
    >
      {/* Header */}
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
          <span style={{ color: "var(--accent)", fontSize: "13px", fontWeight: 600 }}>
            GEOS
          </span>
          <span style={{ color: "var(--text-dim)", fontSize: "11px" }}>
            agent v1.0
          </span>
        </div>
        <button
          onClick={onNewChat}
          disabled={isStreaming}
          title="New chat"
          style={{
            background: "transparent",
            border: "1px solid var(--border-mid)",
            borderRadius: 2,
            cursor: isStreaming ? "not-allowed" : "pointer",
            color: "var(--text-dim)",
            display: "flex",
            alignItems: "center",
            padding: "2px 5px",
          }}
        >
          <Plus size={13} />
        </button>
      </div>

      {/* API key warning */}
      {apiKeyMissing && (
        <div
          style={{
            margin: "8px 12px 0",
            background: "var(--error-bg)",
            border: "1px solid var(--error)",
            borderRadius: 2,
            padding: "6px 8px",
            color: "var(--error)",
            fontSize: "11px",
          }}
        >
          OPENROUTER_API_KEY not set
        </div>
      )}

      {/* Chat history list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "6px 0" }}>
        {sessions.length === 0 ? (
          <div
            style={{
              padding: "20px 12px",
              color: "var(--text-dim)",
              fontSize: "11px",
              textAlign: "center",
            }}
          >
            no conversations yet
          </div>
        ) : (
          sessions.map((s) => {
            const isActive = s.id === activeSessionId;
            return (
              <button
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  width: "100%",
                  padding: "6px 12px",
                  background: isActive ? "var(--accent-bg)" : "transparent",
                  border: "none",
                  borderLeft: isActive ? "2px solid var(--accent)" : "2px solid transparent",
                  cursor: "pointer",
                  fontFamily: "var(--font-mono)",
                  textAlign: "left",
                }}
              >
                <MessageSquare
                  size={12}
                  style={{
                    flexShrink: 0,
                    color: isActive ? "var(--accent)" : "var(--text-dim)",
                  }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      color: isActive ? "var(--accent)" : "var(--text-primary)",
                      fontSize: "11.5px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      fontWeight: isActive ? 500 : 400,
                    }}
                  >
                    {s.name || `Chat ${s.id.slice(0, 6)}`}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      color: "var(--text-dim)",
                      fontSize: "10px",
                      marginTop: 1,
                    }}
                  >
                    <span>{formatRelativeTime(s.lastMessageAt)}</span>
                    <span>{s.messageCount} msgs</span>
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Bottom: token usage + settings */}
      <div
        style={{
          borderTop: "1px solid var(--border-subtle)",
          padding: "10px 12px",
          flexShrink: 0,
        }}
      >
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
        <TokenBar
          label="input"
          value={tokenUsage.promptTokens}
          max={maxTokens}
          color="var(--info)"
        />
        <TokenBar
          label="output"
          value={tokenUsage.completionTokens}
          max={maxTokens}
          color="var(--success)"
        />
        {/* Context window bar */}
        {tokenUsage.contextTokensEst !== undefined && tokenUsage.contextTokensEst > 0 && (
          <TokenBar
            label="context"
            value={tokenUsage.contextTokensEst}
            max={tokenUsage.compactionThreshold ?? 100000}
            color="var(--warning)"
          />
        )}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: 5,
            marginTop: 3,
          }}
        >
          <span style={{ color: "var(--text-dim)", fontSize: "10.5px" }}>
            total
          </span>
          <span
            style={{
              color: tokenUsage.totalTokens > 0 ? "var(--accent)" : "var(--text-dim)",
              fontSize: "11px",
              fontWeight: 500,
            }}
          >
            {tokenUsage.totalTokens.toLocaleString()}
          </span>
        </div>

        {/* Settings gear */}
        <button
          onClick={onOpenSettings}
          style={{
            width: "100%",
            marginTop: 10,
            padding: "6px",
            background: "transparent",
            border: "1px solid var(--border-mid)",
            borderRadius: 2,
            cursor: "pointer",
            fontFamily: "var(--font-mono)",
            fontSize: "11px",
            color: "var(--text-secondary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 6,
          }}
        >
          <Settings size={12} />
          settings
        </button>
      </div>
    </div>
  );
}
