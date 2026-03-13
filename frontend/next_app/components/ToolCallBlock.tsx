"use client";
import { useState } from "react";

const TOOL_COLORS: Record<string, string> = {
  search_navigator: "#4a8fbf",
  search_technical: "#4a8fbf",
  search_schema:    "#4a8fbf",
  search_web:       "#4a8fbf",
  read_file:        "#6b9e78",
  write_file:       "#c47f0a",
  edit_file:        "#c47f0a",
  grep_search:      "#6b9e78",
  list_dir:         "#6b9e78",
  run_shell:        "#4a8fbf",
  shell:            "#9b7ec4",
  python_exec:      "#9b7ec4",
  fetch_code:       "#6b9e78",
  run_geos:         "#e07810",
  ask_user:         "#4a8fbf",
  confirm_action:   "#4a8fbf",
};

interface Props {
  name: string;
  summary: string;
  result?: string;
  error?: string;
  streaming?: boolean;
}

export default function ToolCallBlock({ name, summary, result, error, streaming }: Props) {
  const [resultOpen, setResultOpen] = useState(false);
  const color = TOOL_COLORS[name] ?? "var(--tool-text)";
  const hasOutput = result !== undefined || error !== undefined;

  return (
    <div
      className="fade-up"
      style={{
        background: "var(--tool-bg)",
        border: "1px solid var(--tool-border)",
        borderRadius: 2,
        marginBottom: 5,
        overflow: "hidden",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 10px" }}>
        {/* Show/hide toggle on the LEFT (like ThinkingBlock) */}
        {hasOutput && !streaming ? (
          <button
            onClick={() => setResultOpen((v) => !v)}
            aria-label={resultOpen ? "Collapse tool output" : "Expand tool output"}
            style={{
              width: 24,
              height: 24,
              display: "inline-flex",
              justifyContent: "center",
              alignItems: "center",
              background: "transparent",
              border: "none",
              cursor: "pointer",
              color: "var(--text-dim)",
              fontSize: 9,
              flexShrink: 0,
              padding: 0,
              margin: "-5px",
              letterSpacing: 1,
            }}
          >
            {resultOpen ? "▼" : "▶"}
          </button>
        ) : null}

        {/* Tool name badge — theme-aware background */}
        <span
          style={{
            background: `${color}22`,
            color,
            fontSize: "11.5px",
            padding: "2px 7px",
            borderRadius: 2,
            border: `1px solid ${color}55`,
            flexShrink: 0,
            letterSpacing: "0.04em",
            fontWeight: 600,
            whiteSpace: "nowrap",
          }}
        >
          {name}
        </span>

        {/* Summary */}
        <span
          style={{
            color: "var(--text-secondary)",
            fontSize: "12.5px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            flex: 1,
            minWidth: 0,
          }}
        >
          {summary}
        </span>

        {/* Streaming spinner */}
        {streaming && <span className="spinner" />}
      </div>

      {resultOpen && hasOutput && (
        <div
          style={{
            borderTop: "1px solid var(--tool-border)",
            padding: "9px 11px",
            maxHeight: 320,
            overflowY: "auto",
          }}
        >
          {error ? (
            <div style={{ color: "var(--error)", fontSize: "12.5px" }}>
              <span style={{ color: "var(--error)", opacity: 0.6 }}>error: </span>
              {error}
            </div>
          ) : (
            <pre
              style={{
                background: "transparent",
                border: "none",
                padding: 0,
                fontSize: "12px",
                color: "var(--text-secondary)",
                whiteSpace: "pre",
                overflowX: "auto",
                margin: 0,
              }}
            >
              {(result ?? "").slice(0, 4000)}
              {(result ?? "").length > 4000 && (
                <span style={{ color: "var(--text-dim)" }}>{"\n"}... output truncated</span>
              )}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
