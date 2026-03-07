"use client";
import { AVAILABLE_MODELS, SessionConfig, TokenUsage } from "../lib/types";

interface Props {
  config: SessionConfig;
  setConfig: (c: SessionConfig) => void;
  tokenUsage: TokenUsage;
  isStreaming: boolean;
  sessionId: string | null;
  workspacePath: string;
  onWorkspaceChange: (path: string) => void;
  onNewChat: () => void;
  apiKeyMissing: boolean;
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div
      style={{
        color: "var(--text-dim)",
        fontSize: "9.5px",
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        marginBottom: 5,
        marginTop: 2,
      }}
    >
      {label}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ color: "var(--text-secondary)", fontSize: "11px", marginBottom: 3 }}>
        {label}
      </div>
      {children}
    </div>
  );
}

function inputStyle(): React.CSSProperties {
  return {
    width: "100%",
    padding: "4px 7px",
    background: "var(--bg-elevated)",
    border: "1px solid var(--border-mid)",
    color: "var(--text-primary)",
    fontSize: "11.5px",
    fontFamily: "var(--font-mono)",
    borderRadius: 2,
    outline: "none",
  };
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

export default function Sidebar({
  config,
  setConfig,
  tokenUsage,
  isStreaming,
  sessionId,
  workspacePath,
  onWorkspaceChange,
  onNewChat,
  apiKeyMissing,
}: Props) {
  const maxTokens = Math.max(tokenUsage.totalTokens * 1.2, 10000);

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
        overflowY: "auto",
      }}
    >
      {/* Logo / title */}
      <div
        style={{
          padding: "0 12px",
          height: "var(--header-h)",
          display: "flex",
          alignItems: "center",
          borderBottom: "1px solid var(--border-subtle)",
          flexShrink: 0,
          gap: 8,
        }}
      >
        <span style={{ color: "var(--accent)", fontSize: "13px", fontWeight: 600 }}>
          GEOS
        </span>
        <span style={{ color: "var(--text-dim)", fontSize: "11px" }}>
          agent v1.0
        </span>
      </div>

      <div style={{ padding: "12px 12px", flex: 1 }}>
        {/* API key warning */}
        {apiKeyMissing && (
          <div
            style={{
              background: "var(--error-bg)",
              border: "1px solid var(--error)",
              borderRadius: 2,
              padding: "6px 8px",
              marginBottom: 10,
              color: "var(--error)",
              fontSize: "11px",
            }}
          >
            OPENROUTER_API_KEY not set
          </div>
        )}

        {/* ── Model ── */}
        <SectionLabel label="model" />
        <Field label="provider/model">
          <select
            value={config.model}
            onChange={(e) => setConfig({ ...config, model: e.target.value })}
            style={{ ...inputStyle(), cursor: "pointer" }}
          >
            {AVAILABLE_MODELS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </Field>

        <Field label="provider override">
          <input
            type="text"
            value={config.provider}
            onChange={(e) => setConfig({ ...config, provider: e.target.value })}
            placeholder="e.g. baseten, novita"
            style={inputStyle()}
          />
        </Field>

        <hr className="divider" />

        {/* ── Agent settings ── */}
        <SectionLabel label="agent" />
        <Field label={`max steps: ${config.maxSteps}`}>
          <input
            type="range"
            min={10}
            max={200}
            step={5}
            value={config.maxSteps}
            onChange={(e) =>
              setConfig({ ...config, maxSteps: parseInt(e.target.value) })
            }
            style={{ width: "100%", marginTop: 4 }}
          />
        </Field>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            marginBottom: 8,
            cursor: "pointer",
          }}
          onClick={() =>
            setConfig({
              ...config,
              enableContextProjection: !config.enableContextProjection,
            })
          }
        >
          <input
            type="checkbox"
            checked={config.enableContextProjection}
            onChange={(e) =>
              setConfig({ ...config, enableContextProjection: e.target.checked })
            }
            style={{ cursor: "pointer" }}
          />
          <span style={{ color: "var(--text-secondary)", fontSize: "11.5px" }}>
            context projection
          </span>
        </div>

        <hr className="divider" />

        {/* ── Workspace ── */}
        <SectionLabel label="workspace" />
        <Field label="directory">
          <input
            type="text"
            value={workspacePath}
            onChange={(e) => onWorkspaceChange(e.target.value)}
            placeholder="auto (temp dir)"
            style={inputStyle()}
          />
        </Field>
        <div
          style={{
            color: "var(--text-dim)",
            fontSize: "10.5px",
            marginBottom: 8,
            marginTop: -4,
          }}
        >
          agent reads/writes here
        </div>

        <hr className="divider" />

        {/* ── Logging ── */}
        <SectionLabel label="logging" />
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 7,
            marginBottom: 6,
            cursor: "pointer",
          }}
          onClick={() =>
            setConfig({ ...config, enableLogging: !config.enableLogging })
          }
        >
          <input
            type="checkbox"
            checked={config.enableLogging}
            onChange={(e) =>
              setConfig({ ...config, enableLogging: e.target.checked })
            }
            style={{ cursor: "pointer" }}
          />
          <span style={{ color: "var(--text-secondary)", fontSize: "11.5px" }}>
            save conversation log (.jsonl)
          </span>
        </div>

        {config.enableLogging && (
          <Field label="log directory">
            <input
              type="text"
              value={config.logDir}
              onChange={(e) => setConfig({ ...config, logDir: e.target.value })}
              placeholder="data/eval/jsonl_logs"
              style={inputStyle()}
            />
          </Field>
        )}

        <hr className="divider" />

        {/* ── Actions ── */}
        <button
          onClick={onNewChat}
          disabled={isStreaming}
          style={{
            width: "100%",
            padding: "7px",
            background: "transparent",
            border: "1px solid var(--border-strong)",
            color: isStreaming ? "var(--text-dim)" : "var(--text-secondary)",
            fontSize: "11.5px",
            fontFamily: "var(--font-mono)",
            borderRadius: 2,
            cursor: isStreaming ? "not-allowed" : "pointer",
            transition: "border-color 0.15s, color 0.15s",
            marginBottom: 16,
          }}
          onMouseEnter={(e) => {
            if (!isStreaming) {
              (e.currentTarget as HTMLElement).style.borderColor = "var(--accent)";
              (e.currentTarget as HTMLElement).style.color = "var(--accent)";
            }
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.borderColor = "var(--border-strong)";
            (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
          }}
        >
          new session
        </button>

        {/* ── Token usage ── */}
        <SectionLabel label="token usage" />
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

        {/* ── Session info ── */}
        {sessionId && (
          <>
            <hr className="divider" />
            <div style={{ color: "var(--text-dim)", fontSize: "10.5px" }}>
              <div>
                session:{" "}
                <span style={{ color: "var(--text-secondary)" }}>
                  {sessionId.slice(0, 8)}…
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
