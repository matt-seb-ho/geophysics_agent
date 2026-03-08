"use client";
import { useEffect, useRef, useState } from "react";
import { Message, PendingInput } from "../lib/types";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: Message[];
  isStreaming: boolean;
  pendingInput: PendingInput | null;
  sessionId: string | null;
  onSend: (text: string) => void;
  onToggleFileTree: () => void;
  showFileTree: boolean;
}

const WELCOME = `GEOS Multiphysics Simulation Agent

I can help you:
  ─ create XML input decks for simulations
  ─ search GEOS documentation and examples
  ─ run simulations and analyze results
  ─ visualize output data with Python

Try: "Create a hydraulic fracture simulation"
     "Search for multiphase flow examples"
     "Set up a wellbore model with thermal effects"`;

export default function ChatArea({
  messages,
  isStreaming,
  pendingInput,
  sessionId,
  onSend,
  onToggleFileTree,
  showFileTree,
}: Props) {
  const [inputText, setInputText] = useState("");
  const bottomRef   = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }, [inputText]);

  const handleSubmit = () => {
    const text = inputText.trim();
    if (!text || isStreaming) return;
    setInputText("");
    onSend(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const placeholder = pendingInput
    ? `answer: ${pendingInput.question.slice(0, 60)}${pendingInput.question.length > 60 ? "…" : ""}`
    : isStreaming
    ? "agent is responding…"
    : "describe your simulation… (Enter to send, Shift+Enter for newline)";

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
        height: "100%",
        background: "var(--bg-base)",
      }}
    >
      {/* ── Top bar ── */}
      <div
        style={{
          height: "var(--header-h)",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 14px",
          flexShrink: 0,
          background: "var(--bg-panel)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span
            style={{ color: "var(--text-dim)", fontSize: "10px", letterSpacing: "0.06em" }}
          >
            GEOS AGENT
          </span>
          {isStreaming && (
            <span
              style={{
                background: "var(--accent-bg)",
                border: "1px solid var(--accent-border)",
                color: "var(--accent)",
                fontSize: "9.5px",
                padding: "1px 7px",
                borderRadius: 2,
                letterSpacing: "0.05em",
              }}
            >
              <span className="spinning" style={{ display: "inline-block", marginRight: 4 }}>
                ↻
              </span>
              running
            </span>
          )}
          {pendingInput && !isStreaming && (
            <span
              style={{
                background: "var(--info-bg)",
                border: "1px solid var(--info)",
                color: "var(--info)",
                fontSize: "9.5px",
                padding: "1px 7px",
                borderRadius: 2,
                letterSpacing: "0.05em",
              }}
            >
              awaiting input
            </span>
          )}
        </div>

        {/* File tree toggle */}
        <button
          onClick={onToggleFileTree}
          title="Toggle workspace file tree"
          style={{
            background: showFileTree ? "var(--accent-bg)" : "transparent",
            border: `1px solid ${showFileTree ? "var(--accent-border)" : "var(--border-mid)"}`,
            color: showFileTree ? "var(--accent)" : "var(--text-dim)",
            fontSize: "11px",
            padding: "2px 9px",
            borderRadius: 2,
            cursor: "pointer",
            fontFamily: "var(--font-mono)",
            transition: "all 0.15s",
          }}
          onMouseEnter={(e) => {
            if (!showFileTree)
              (e.currentTarget as HTMLElement).style.color = "var(--accent)";
          }}
          onMouseLeave={(e) => {
            if (!showFileTree)
              (e.currentTarget as HTMLElement).style.color = "var(--text-dim)";
          }}
        >
          {showFileTree ? "✕ files" : "⊞ files"}
        </button>
      </div>

      {/* ── Message list ── */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 20px 12px",
        }}
      >
        {messages.length === 0 ? (
          <pre
            style={{
              color: "var(--text-dim)",
              fontSize: "12px",
              lineHeight: 1.7,
              background: "transparent",
              border: "none",
              padding: 0,
              fontFamily: "var(--font-mono)",
              whiteSpace: "pre-wrap",
            }}
          >
            {WELCOME}
          </pre>
        ) : (
          messages.map((msg, i) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              sessionId={sessionId ?? undefined}
              isLast={i === messages.length - 1}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Pending question reminder ── */}
      {pendingInput && (
        <div
          style={{
            margin: "0 20px",
            marginBottom: 6,
            background: "var(--info-bg)",
            border: "1px solid var(--info)",
            borderRadius: 2,
            padding: "6px 10px",
            fontSize: "11.5px",
          }}
        >
          <span style={{ color: "var(--info)", marginRight: 6 }}>[?]</span>
          <span style={{ color: "var(--text-primary)" }}>{pendingInput.question}</span>
          {pendingInput.choices && pendingInput.choices.length > 0 && (
            <div style={{ marginTop: 4, display: "flex", gap: 5, flexWrap: "wrap" }}>
              {pendingInput.choices.map((c) => (
                <button
                  key={c}
                  onClick={() => { setInputText(c); textareaRef.current?.focus(); }}
                  style={{
                    background: "var(--bg-elevated)",
                    border: "1px solid var(--border-mid)",
                    borderRadius: 2,
                    padding: "1px 8px",
                    color: "var(--text-secondary)",
                    fontSize: "11px",
                    cursor: "pointer",
                    fontFamily: "var(--font-mono)",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--accent)";
                    (e.currentTarget as HTMLElement).style.color = "var(--accent)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--border-mid)";
                    (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                  }}
                >
                  {c}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Input area ── */}
      <div
        style={{
          borderTop: "1px solid var(--border-subtle)",
          padding: "10px 20px 12px",
          flexShrink: 0,
          background: "var(--bg-panel)",
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "flex-end",
          }}
        >
          {/* Prompt glyph */}
          <div
            style={{
              color: pendingInput ? "var(--info)" : "var(--accent)",
              fontSize: "14px",
              paddingBottom: 9,
              flexShrink: 0,
              userSelect: "none",
            }}
          >
            {pendingInput ? "?" : "»"}
          </div>

          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isStreaming}
            rows={1}
            style={{
              flex: 1,
              resize: "none",
              padding: "8px 10px",
              background: "var(--bg-surface)",
              border: `1px solid ${isStreaming ? "var(--border-subtle)" : "var(--border-mid)"}`,
              color: isStreaming ? "var(--text-dim)" : "var(--text-primary)",
              fontSize: "12.5px",
              fontFamily: "var(--font-mono)",
              borderRadius: 2,
              outline: "none",
              lineHeight: 1.5,
              minHeight: 38,
              maxHeight: 160,
              overflowY: "auto",
              transition: "border-color 0.15s",
            }}
            onFocus={(e) => {
              (e.target as HTMLTextAreaElement).style.borderColor = "var(--accent-border)";
            }}
            onBlur={(e) => {
              (e.target as HTMLTextAreaElement).style.borderColor = "var(--border-mid)";
            }}
          />

          <button
            onClick={handleSubmit}
            disabled={isStreaming || !inputText.trim()}
            style={{
              padding: "8px 14px",
              background:
                isStreaming || !inputText.trim()
                  ? "var(--bg-elevated)"
                  : "var(--accent)",
              border: "none",
              color:
                isStreaming || !inputText.trim()
                  ? "var(--text-dim)"
                  : "#000",
              fontSize: "12px",
              fontFamily: "var(--font-mono)",
              fontWeight: 600,
              borderRadius: 2,
              cursor:
                isStreaming || !inputText.trim() ? "not-allowed" : "pointer",
              flexShrink: 0,
              transition: "background 0.15s",
              letterSpacing: "0.04em",
            }}
          >
            {isStreaming ? (
              <span className="spinning" style={{ display: "inline-block" }}>
                ↻
              </span>
            ) : (
              "run"
            )}
          </button>
        </div>

        <div
          style={{
            marginTop: 5,
            color: "var(--text-dim)",
            fontSize: "9.5px",
            letterSpacing: "0.03em",
          }}
        >
          Enter to send · Shift+Enter for newline · Shift+Enter also sends multi-line
        </div>
      </div>
    </div>
  );
}
