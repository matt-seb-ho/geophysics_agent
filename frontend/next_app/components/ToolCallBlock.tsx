"use client";
import { useState } from "react";

// Short tag labels matching the Python TOOL_ICONS
const TOOL_TAGS: Record<string, string> = {
  search_navigator: "nav",
  search_technical: "tec",
  search_schema:    "xsd",
  search_web:       "web",
  read_file:        " r ",
  write_file:       " w ",
  edit_file:        " e ",
  grep_search:      "grep",
  list_dir:         " ls",
  shell:            " sh",
  python_exec:      " py",
  fetch_code:       " fc",
  run_geos:         "geos",
  ask_user:         " ? ",
  confirm_action:   " ! ",
};

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

export default function ToolCallBlock({
  name,
  summary,
  result,
  error,
  streaming,
}: Props) {
  const [resultOpen, setResultOpen] = useState(false);

  const tag   = TOOL_TAGS[name]  ?? name;
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
      {/* Call line */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "5px 9px",
        }}
      >
        {/* Tool tag badge */}
        <span
          style={{
            background: "rgba(0,0,0,0.4)",
            color,
            fontSize: "10px",
            padding: "1px 5px",
            borderRadius: 2,
            border: `1px solid ${color}44`,
            flexShrink: 0,
            letterSpacing: "0.04em",
            fontWeight: 600,
          }}
        >
          {tag}
        </span>

        {/* Function name — only show separately if name has a known tag */}
        {TOOL_TAGS[name] !== undefined && (
          <span style={{ color, fontSize: "12px", fontWeight: 500, flexShrink: 0 }}>
            {name}
          </span>
        )}

        {/* Summary */}
        <span
          style={{
            color: "var(--text-secondary)",
            fontSize: "11.5px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            flex: 1,
          }}
        >
          {summary}
        </span>

        {/* Status indicator */}
        {streaming ? (
          <span
            className="spinning"
            style={{ fontSize: 10, color: "var(--accent)", flexShrink: 0 }}
          >
            ↻
          </span>
        ) : hasOutput ? (
          <button
            onClick={() => setResultOpen((v) => !v)}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              color: "var(--text-dim)",
              fontSize: 10,
              flexShrink: 0,
              padding: "0 2px",
            }}
          >
            {resultOpen ? "▼ hide" : "▶ show"}
          </button>
        ) : null}
      </div>

      {/* Result / Error */}
      {resultOpen && hasOutput && (
        <div
          style={{
            borderTop: "1px solid var(--tool-border)",
            padding: "7px 10px",
            maxHeight: 320,
            overflowY: "auto",
          }}
        >
          {error ? (
            <div style={{ color: "var(--error)", fontSize: "11.5px" }}>
              <span style={{ color: "var(--error)", opacity: 0.6 }}>error: </span>
              {error}
            </div>
          ) : (
            <pre
              style={{
                background: "transparent",
                border: "none",
                padding: 0,
                fontSize: "11px",
                color: "var(--text-secondary)",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                margin: 0,
              }}
            >
              {(result ?? "").slice(0, 4000)}
              {(result ?? "").length > 4000 && (
                <span style={{ color: "var(--text-dim)" }}>
                  {"\n"}... [{((result ?? "").length - 4000).toLocaleString()} chars truncated]
                </span>
              )}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
