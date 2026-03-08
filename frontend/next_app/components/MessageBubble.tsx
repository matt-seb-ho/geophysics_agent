"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Message, MessagePart } from "../lib/types";
import ThinkingBlock from "./ThinkingBlock";
import ToolCallBlock from "./ToolCallBlock";

function formatTime(d: Date): string {
  return d.toTimeString().slice(0, 8);
}

function TextPart({ content, streaming }: { content: string; streaming?: boolean }) {
  return (
    <div className={`md ${streaming ? "cursor-blink" : ""}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>{content}</ReactMarkdown>
    </div>
  );
}

function QuestionPart({ content, choices }: { content: string; choices?: string[] }) {
  return (
    <div
      style={{
        background: "var(--info-bg)",
        border: "1px solid var(--info)",
        borderRadius: 2,
        padding: "8px 10px",
        marginBottom: 5,
      }}
    >
      <div
        style={{
          color: "var(--info)",
          fontSize: "10.5px",
          letterSpacing: "0.05em",
          marginBottom: 4,
        }}
      >
        [agent question]
      </div>
      <div style={{ color: "var(--text-primary)", fontSize: "12.5px" }}>{content}</div>
      {choices && choices.length > 0 && (
        <div style={{ marginTop: 6, display: "flex", gap: 5, flexWrap: "wrap" }}>
          {choices.map((c) => (
            <span
              key={c}
              style={{
                background: "var(--bg-elevated)",
                border: "1px solid var(--border-mid)",
                borderRadius: 2,
                padding: "2px 7px",
                color: "var(--text-secondary)",
                fontSize: "11px",
              }}
            >
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ErrorPart({ content, variant = "error" }: { content: string; variant?: "error" | "warning" }) {
  const color   = variant === "error" ? "var(--error)"   : "var(--warning)";
  const bg      = variant === "error" ? "var(--error-bg)" : "var(--warning-bg)";
  const label   = variant === "error" ? "[error]"        : "[warning]";
  return (
    <div
      style={{
        background: bg,
        border: `1px solid ${color}`,
        borderRadius: 2,
        padding: "7px 10px",
        marginBottom: 5,
      }}
    >
      <span style={{ color, fontSize: "10.5px", marginRight: 6 }}>{label}</span>
      <span style={{ color: "var(--text-primary)", fontSize: "12px" }}>{content}</span>
    </div>
  );
}

function ImagePart({
  path,
  caption,
  sessionId,
}: {
  path: string;
  caption?: string;
  sessionId?: string;
}) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:6305";
  const src = sessionId
    ? `${API_URL}/api/sessions/${sessionId}/file?path=${encodeURIComponent(path)}`
    : path;

  return (
    <div style={{ marginBottom: 6 }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={caption ?? path}
        style={{
          maxWidth: "100%",
          border: "1px solid var(--border-mid)",
          borderRadius: 2,
        }}
      />
      {caption && (
        <div style={{ color: "var(--text-dim)", fontSize: "10.5px", marginTop: 3 }}>
          {caption}
        </div>
      )}
    </div>
  );
}

function renderPart(
  part: MessagePart,
  idx: number,
  sessionId?: string,
  isStreamingLast?: boolean
) {
  switch (part.type) {
    case "text":
      return <TextPart key={idx} content={part.content} streaming={isStreamingLast} />;
    case "thinking":
      return <ThinkingBlock key={idx} content={part.content} />;
    case "tool_call":
      return (
        <ToolCallBlock
          key={idx}
          name={part.name}
          summary={part.summary}
          result={part.result}
          error={part.error}
          streaming={part.streaming}
        />
      );
    case "question":
      return <QuestionPart key={idx} content={part.content} choices={part.choices} />;
    case "error":
      return <ErrorPart key={idx} content={part.content} variant="error" />;
    case "warning":
      return <ErrorPart key={idx} content={part.content} variant="warning" />;
    case "image":
      return (
        <ImagePart key={idx} path={part.path} caption={part.caption} sessionId={sessionId} />
      );
    case "dataframe":
      return (
        <div
          key={idx}
          style={{
            background: "var(--bg-elevated)",
            border: "1px solid var(--border-mid)",
            borderRadius: 2,
            padding: "6px 10px",
            marginBottom: 5,
          }}
        >
          <span style={{ color: "var(--text-dim)", fontSize: "10.5px" }}>
            [table] {part.caption ?? part.path}
          </span>
        </div>
      );
    default:
      return null;
  }
}

interface Props {
  message: Message;
  sessionId?: string;
  isLast?: boolean;
}

export default function MessageBubble({ message, sessionId, isLast }: Props) {
  const isUser = message.role === "user";
  const time   = formatTime(message.timestamp);

  return (
    <div
      className={isLast ? "fade-up" : ""}
      style={{
        display: "flex",
        gap: 0,
        marginBottom: 14,
        alignItems: "flex-start",
      }}
    >
      {/* Gutter: role + timestamp */}
      <div
        style={{
          width: 82,
          flexShrink: 0,
          paddingTop: 1,
          paddingRight: 10,
          textAlign: "right",
        }}
      >
        <div
          style={{
            color: isUser ? "var(--accent)" : "var(--text-dim)",
            fontSize: "10.5px",
            fontWeight: isUser ? 600 : 400,
            letterSpacing: "0.03em",
          }}
        >
          {isUser ? "in" : "out"}
        </div>
        {(isUser || !message.streaming) && (
          <div style={{ color: "var(--text-dim)", fontSize: "9.5px", marginTop: 2 }}>
            {time}
          </div>
        )}
      </div>

      {/* Separator line */}
      <div
        style={{
          width: 1,
          alignSelf: "stretch",
          background: isUser ? "var(--accent-border)" : "var(--border-subtle)",
          flexShrink: 0,
          marginRight: 12,
          minHeight: 20,
        }}
      />

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {isUser ? (
          <div
            style={{
              color: "var(--text-bright)",
              fontSize: "12.5px",
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {message.parts[0]?.type === "text" ? message.parts[0].content : ""}
          </div>
        ) : (
          <>
            {/* Streaming indicator */}
            {message.streaming && message.parts.length === 0 && (
              <div style={{ color: "var(--text-dim)", fontSize: "11.5px" }}>
                <span className="spinning" style={{ display: "inline-block", marginRight: 6 }}>
                  ↻
                </span>
                thinking...
              </div>
            )}
            {message.parts.map((part, i) => {
              const isLast = i === message.parts.length - 1;
              const showCursor = isLast && !!message.streaming && part.type === "text";
              return renderPart(part, i, sessionId, showCursor);
            })}
          </>
        )}
      </div>
    </div>
  );
}
