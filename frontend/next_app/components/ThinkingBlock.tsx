"use client";
import { useState } from "react";

interface Props {
  content: string;
}

export default function ThinkingBlock({ content }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        border: "1px solid var(--thinking-border)",
        background: "var(--thinking-bg)",
        borderRadius: 2,
        marginBottom: 6,
      }}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          width: "100%",
          padding: "5px 9px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: "var(--text-dim)",
          fontSize: "11px",
          fontFamily: "var(--font-mono)",
          textAlign: "left",
        }}
      >
        <span style={{ fontSize: 9, letterSpacing: 1 }}>
          {open ? "▼" : "▶"}
        </span>
        <span style={{ color: "var(--text-dim)", letterSpacing: "0.03em" }}>
          [reasoning]
        </span>
        <span style={{ marginLeft: "auto", color: "var(--text-dim)", fontSize: 10 }}>
          {content.length.toLocaleString()} chars
        </span>
      </button>

      {open && (
        <div
          style={{
            padding: "6px 12px 8px",
            borderTop: "1px solid var(--thinking-border)",
            color: "var(--text-dim)",
            fontSize: "11.5px",
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            fontStyle: "italic",
          }}
        >
          {content}
        </div>
      )}
    </div>
  );
}
