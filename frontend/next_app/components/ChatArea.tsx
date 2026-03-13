"use client";
import { useEffect, useRef, useState } from "react";
import { Play, Square } from "lucide-react";
import { Message, PendingInput } from "../lib/types";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: Message[];
  isStreaming: boolean;
  pendingInput: PendingInput | null;
  sessionId: string | null;
  onSend: (text: string) => void;
  onCancel: () => void;
  onToggleFileTree: () => void;
  showFileTree: boolean;
  onToggleSidebar?: () => void;
  showSidebar?: boolean;
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
  onCancel,
  onToggleFileTree,
  showFileTree,
  onToggleSidebar,
  showSidebar,
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

  // Suppress unused variable warnings for props kept for parent compatibility
  void onToggleFileTree;
  void showFileTree;
  void onToggleSidebar;
  void showSidebar;

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
              fontSize: "13.5px",
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
              canAnswerQuestion={!!pendingInput && i === messages.length - 1 && msg.role === "assistant"}
              onAnswerQuestion={onSend}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

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
              fontSize: "14px",
              fontFamily: "var(--font-mono)",
              borderRadius: 2,
              outline: "none",
              lineHeight: 1.5,
              minHeight: 44,
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
            onClick={isStreaming ? onCancel : handleSubmit}
            disabled={!isStreaming && !inputText.trim()}
            title={isStreaming ? "Cancel response" : "Run prompt"}
            aria-label={isStreaming ? "Cancel response" : "Run prompt"}
            style={{
              width: 44,
              height: 44,
              background:
                !isStreaming && !inputText.trim()
                  ? "var(--bg-elevated)"
                  : isStreaming
                  ? "var(--bg-surface)"
                  : "var(--accent)",
              border: `1px solid ${isStreaming ? "var(--danger, #d46a6a)" : "transparent"}`,
              color:
                !isStreaming && !inputText.trim()
                  ? "var(--text-dim)"
                  : isStreaming
                  ? "var(--danger, #d46a6a)"
                  : "var(--accent-contrast)",
              borderRadius: 2,
              cursor:
                !isStreaming && !inputText.trim() ? "not-allowed" : "pointer",
              flexShrink: 0,
              transition: "background 0.15s, border-color 0.15s, color 0.15s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {isStreaming ? (
              <Square size={16} strokeWidth={2.25} />
            ) : (
              <Play size={16} strokeWidth={2.25} />
            )}
          </button>
        </div>

      </div>
    </div>
  );
}
