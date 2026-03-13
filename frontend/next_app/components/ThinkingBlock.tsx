"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

interface Props {
  content: string;
}

const DCP_TRACE_RE = /<dcp-message-id>[\s\S]*?<\/dcp-message-id>\s*/g;

function sanitizeThinkingContent(content: string): string {
  return content.replace(DCP_TRACE_RE, "").replace(/\n{3,}/g, "\n\n").trimStart();
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
          padding: "5px 10px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          color: "var(--text-dim)",
          fontSize: "12px",
          fontFamily: "var(--font-mono)",
          textAlign: "left",
        }}
      >
        <span
          style={{
            width: 14,
            display: "inline-flex",
            justifyContent: "center",
            fontSize: 9,
            letterSpacing: 1,
            flexShrink: 0,
          }}
        >
          {open ? "▼" : "▶"}
        </span>
        <span style={{ color: "var(--text-dim)", letterSpacing: "0.03em" }}>
          [reasoning]
        </span>
      </button>

      {open && (
        <div
          style={{
            padding: "6px 12px 8px",
            borderTop: "1px solid var(--thinking-border)",
            color: "var(--text-dim)",
            fontSize: "12.5px",
            lineHeight: 1.6,
            fontStyle: "italic",
          }}
        >
          <div className="md">
            <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
              {sanitizeThinkingContent(content)}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
