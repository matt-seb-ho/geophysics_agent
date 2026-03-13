"use client";
import type { CSSProperties } from "react";
import { useState } from "react";
import * as Select from "@radix-ui/react-select";
import { ChevronDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Message, MessagePart, QuestionField } from "../lib/types";
import ThinkingBlock from "./ThinkingBlock";
import ToolCallBlock from "./ToolCallBlock";

const DCP_TRACE_RE = /<dcp-message-id>[\s\S]*?<\/dcp-message-id>\s*/g;

function sanitizeAssistantContent(content: string): string {
  return content.replace(DCP_TRACE_RE, "").replace(/\n{3,}/g, "\n\n").trimStart();
}

function formatTime(d: Date): string {
  return d.toTimeString().slice(0, 8);
}

function normalizeChoiceLabel(choice: string): string {
  return choice.trim().toLowerCase().replace(/\s+/g, " ");
}

function isCustomChoiceLabel(choice: string): boolean {
  const normalized = normalizeChoiceLabel(choice);
  return (
    normalized === "other" ||
    normalized.startsWith("other ") ||
    normalized.includes("something else") ||
    normalized.includes("something different") ||
    (normalized.includes("describe below") &&
      (normalized.includes("other") || normalized.includes("else") || normalized.includes("custom")))
  );
}

function MarkdownPart({
  content,
  streaming,
  tone = "default",
}: {
  content: string;
  streaming?: boolean;
  tone?: "default" | "bright";
}) {
  return (
    <div
      className={`md ${streaming ? "cursor-blink" : ""}`}
      style={{
        color: tone === "bright" ? "var(--text-bright)" : "var(--text-primary)",
        fontSize: "14px",
        lineHeight: 1.7,
      }}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
        {sanitizeAssistantContent(content)}
      </ReactMarkdown>
    </div>
  );
}

function QuestionPart({
  content,
  choices,
  defaultValue,
  fields,
  allowCustomInput,
  canAnswer,
  onAnswer,
}: {
  content: string;
  choices?: string[];
  defaultValue?: string;
  fields?: QuestionField[];
  allowCustomInput?: boolean;
  canAnswer?: boolean;
  onAnswer?: (value: string) => void;
}) {
  const isInactive = !canAnswer;
  const [draft, setDraft] = useState(defaultValue ?? "");
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [fieldValues, setFieldValues] = useState<Record<string, string | string[]>>(() =>
    Object.fromEntries((fields ?? []).map((field) => [field.id, field.type === "checkbox" ? [] : ""]))
  );

  const hasFields = !!fields && fields.length > 0;
  const baseChoices = choices ?? [];
  const seenChoices = new Set<string>();
  let hasCustomChoice = false;
  const renderedChoices = baseChoices.filter((choice) => {
    const normalized = normalizeChoiceLabel(choice);
    if (seenChoices.has(normalized)) return false;
    seenChoices.add(normalized);

    if (!allowCustomInput) return true;
    if (isCustomChoiceLabel(choice)) {
      if (hasCustomChoice) return false;
      hasCustomChoice = true;
    }
    return true;
  });
  if (allowCustomInput && !hasCustomChoice) {
    renderedChoices.push("Other");
  }

  const setFieldValue = (fieldId: string, value: string | string[]) => {
    setFieldValues((prev) => ({ ...prev, [fieldId]: value }));
  };

  const getFieldDefaultValue = (field: QuestionField): string | string[] => {
    if (field.type === "checkbox") {
      if (Array.isArray(field.default)) return field.default;
      if (typeof field.default === "string" && field.default.trim()) {
        return field.default
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);
      }
      return [];
    }

    if (Array.isArray(field.default)) return "";

    const fieldDefault = String(field.default ?? "").trim();
    if (fieldDefault) return fieldDefault;

    return "";
  };

  const hasAnyFieldDefaults = !!fields?.some((field) => {
    const value = getFieldDefaultValue(field);
    return Array.isArray(value) ? value.length > 0 : !!String(value).trim();
  });

  const useDefaults = () => {
    if (!fields?.length) return;
    setFieldValues(
      Object.fromEntries(fields.map((field) => [field.id, getFieldDefaultValue(field)]))
    );
  };

  const renderField = (field: QuestionField) => {
    const value = fieldValues[field.id];
    const commonLabelStyle: CSSProperties = {
      display: "block",
      color: isInactive ? "var(--text-dim)" : "var(--text-primary)",
      fontSize: "11.5px",
      marginBottom: 5,
    };
    const inputStyle: CSSProperties = {
      width: "100%",
      padding: "8px 10px",
      background: isInactive ? "var(--bg-elevated)" : "var(--bg-base)",
      border: `1px solid ${isInactive ? "var(--border-mid)" : "var(--info)"}`,
      borderRadius: 2,
      color: isInactive ? "var(--text-dim)" : "var(--text-primary)",
      fontFamily: "var(--font-mono)",
      fontSize: "12.5px",
      outline: "none",
    };

    if (field.type === "select") {
      return (
        <label key={field.id} style={commonLabelStyle}>
          {field.label}
          <div style={{ marginTop: 4 }}>
            <Select.Root
              value={typeof value === "string" ? value : ""}
              onValueChange={(nextValue) => setFieldValue(field.id, nextValue)}
              disabled={!canAnswer}
            >
              <Select.Trigger
                style={{
                  ...inputStyle,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  cursor: isInactive ? "default" : "pointer",
                }}
              >
                <Select.Value placeholder={field.placeholder ?? "Select an option"} />
                <Select.Icon>
                  <ChevronDown size={12} style={{ color: "var(--text-dim)" }} />
                </Select.Icon>
              </Select.Trigger>
              <Select.Portal>
                <Select.Content
                  className="radix-select-content"
                  position="popper"
                  sideOffset={4}
                >
                  <Select.Viewport>
                    {(field.options ?? []).map((option) => (
                      <Select.Item key={option} value={option} className="radix-select-item">
                        <Select.ItemText>{option}</Select.ItemText>
                      </Select.Item>
                    ))}
                  </Select.Viewport>
                </Select.Content>
              </Select.Portal>
            </Select.Root>
          </div>
        </label>
      );
    }

    if (field.type === "radio") {
      return (
        <fieldset
          key={field.id}
          style={{ border: "none", padding: 0, margin: "0 0 10px 0" }}
        >
          <legend style={commonLabelStyle}>{field.label}</legend>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {(field.options ?? []).map((option) => (
              <label
                key={option}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  color: isInactive ? "var(--text-dim)" : "var(--text-primary)",
                  fontSize: "12px",
                }}
              >
                <input
                  type="radio"
                  name={field.id}
                  checked={value === option}
                  disabled={!canAnswer}
                  onChange={() => setFieldValue(field.id, option)}
                />
                {option}
              </label>
            ))}
          </div>
        </fieldset>
      );
    }

    if (field.type === "checkbox") {
      const selected = Array.isArray(value) ? value : [];
      return (
        <fieldset
          key={field.id}
          style={{ border: "none", padding: 0, margin: "0 0 10px 0" }}
        >
          <legend style={commonLabelStyle}>{field.label}</legend>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {(field.options ?? []).map((option) => (
              <label
                key={option}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  color: isInactive ? "var(--text-dim)" : "var(--text-primary)",
                  fontSize: "12px",
                }}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(option)}
                  disabled={!canAnswer}
                  onChange={(e) => {
                    setFieldValue(
                      field.id,
                      e.target.checked
                        ? [...selected, option]
                        : selected.filter((item) => item !== option)
                    );
                  }}
                />
                {option}
              </label>
            ))}
          </div>
        </fieldset>
      );
    }

    if (field.type === "textarea") {
      return (
        <label key={field.id} style={commonLabelStyle}>
          {field.label}
          <textarea
            value={typeof value === "string" ? value : ""}
            onChange={(e) => setFieldValue(field.id, e.target.value)}
            placeholder={field.placeholder ?? ""}
            disabled={!canAnswer}
            rows={4}
            style={{ ...inputStyle, marginTop: 4, resize: "vertical", minHeight: 96 }}
          />
        </label>
      );
    }

    return (
      <label key={field.id} style={commonLabelStyle}>
        {field.label}
        <input
          type="text"
          value={typeof value === "string" ? value : ""}
          onChange={(e) => setFieldValue(field.id, e.target.value)}
          placeholder={field.placeholder ?? ""}
          disabled={!canAnswer}
          style={{ ...inputStyle, marginTop: 4 }}
        />
      </label>
    );
  };

  const serializeFields = () => {
    if (!fields || fields.length === 0) return "";
    if (fields.length === 1) {
      const only = fields[0];
      const raw = fieldValues[only.id];
      return Array.isArray(raw) ? raw.join(", ") : String(raw ?? "").trim();
    }
    return fields
      .map((field) => {
        const raw = fieldValues[field.id];
        const value = Array.isArray(raw) ? raw.join(", ") : String(raw ?? "").trim();
        return `${field.label}: ${value}`;
      })
      .filter((line) => !line.endsWith(": "))
      .join("\n");
  };

  const submit = () => {
    const value = hasFields ? serializeFields() : draft.trim();
    if (!onAnswer) return;
    setDraft("");
    setShowCustomInput(false);
    onAnswer(value);
  };

  return (
    <div
      style={{
        background: isInactive ? "var(--bg-panel)" : "var(--info-bg)",
        border: `1px solid ${isInactive ? "var(--border-mid)" : "var(--info)"}`,
        borderRadius: 2,
        padding: "8px 10px",
        marginBottom: 5,
        opacity: isInactive ? 0.72 : 1,
      }}
    >
      <div
        style={{
          color: isInactive ? "var(--text-dim)" : "var(--info)",
          fontSize: "10.5px",
          letterSpacing: "0.05em",
          marginBottom: 4,
        }}
      >
        [agent question]
      </div>
      <div style={{ color: isInactive ? "var(--text-secondary)" : undefined }}>
        <MarkdownPart content={content} />
      </div>
      {renderedChoices.length > 0 && (
        <div style={{ marginTop: 6, display: "flex", gap: 5, flexWrap: "wrap" }}>
          {renderedChoices.map((c) => (
            <button
              key={c}
              onClick={() => {
                if (allowCustomInput && isCustomChoiceLabel(c)) {
                  setShowCustomInput(true);
                  return;
                }
                onAnswer?.(c);
              }}
              disabled={!canAnswer}
              style={{
                background: isInactive ? "var(--bg-elevated)" : "var(--bg-surface)",
                border: `1px solid ${isInactive ? "var(--border-mid)" : "var(--info)"}`,
                borderRadius: 2,
                padding: "3px 9px",
                color: isInactive ? "var(--text-dim)" : "var(--info)",
                fontSize: "11px",
                fontFamily: "var(--font-mono)",
                cursor: canAnswer ? "pointer" : "default",
              }}
            >
              {c}
            </button>
          ))}
        </div>
      )}
      {hasFields && (
        <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
          {fields?.map(renderField)}
        </div>
      )}
      {canAnswer &&
        onAnswer &&
        (hasFields || renderedChoices.length === 0 || showCustomInput) && (
        <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "stretch" }}>
          {hasFields && hasAnyFieldDefaults && (
            <button
              onClick={useDefaults}
              style={{
                padding: "0 12px",
                background: "var(--bg-surface)",
                border: "1px solid var(--info)",
                borderRadius: 2,
                color: "var(--info)",
                fontFamily: "var(--font-mono)",
                fontSize: "11.5px",
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              Use defaults
            </button>
          )}
          {!hasFields && (
            <input
              type="text"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  submit();
                }
              }}
              placeholder="Type your answer..."
              style={{
                flex: 1,
                minWidth: 0,
                padding: "8px 10px",
                background: "var(--bg-base)",
                border: "1px solid var(--info)",
                borderRadius: 2,
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
                fontSize: "12.5px",
                outline: "none",
              }}
            />
          )}
          <button
            onClick={submit}
            style={{
              padding: "0 12px",
              background: "var(--info)",
              border: "1px solid var(--info)",
              borderRadius: 2,
              color: "var(--bg-base)",
              fontFamily: "var(--font-mono)",
              fontSize: "11.5px",
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            Submit
          </button>
        </div>
      )}
    </div>
  );
}

function ErrorPart({
  content,
  variant = "error",
  hideLabel = false,
}: {
  content: string;
  variant?: "error" | "warning";
  hideLabel?: boolean;
}) {
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
      {!hideLabel && (
        <span style={{ color, fontSize: "10.5px", marginRight: 6 }}>{label}</span>
      )}
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
  isStreamingLast?: boolean,
  canAnswer?: boolean,
  onAnswer?: (value: string) => void
) {
  switch (part.type) {
    case "text":
      return <MarkdownPart key={idx} content={part.content} streaming={isStreamingLast} />;
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
      return (
        <QuestionPart
          key={idx}
          content={part.content}
          choices={part.choices}
          defaultValue={part.default}
          fields={part.fields}
          allowCustomInput={part.allowCustomInput}
          canAnswer={canAnswer}
          onAnswer={onAnswer}
        />
      );
    case "error":
      return <ErrorPart key={idx} content={part.content} variant="error" />;
    case "warning":
      return (
        <ErrorPart
          key={idx}
          content={part.content}
          variant="warning"
          hideLabel={part.hideLabel}
        />
      );
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
            padding: "7px 10px",
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
  canAnswerQuestion?: boolean;
  onAnswerQuestion?: (value: string) => void;
}

export default function MessageBubble({
  message,
  sessionId,
  isLast,
  canAnswerQuestion,
  onAnswerQuestion,
}: Props) {
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
            fontSize: "11.5px",
            fontWeight: isUser ? 600 : 400,
            letterSpacing: "0.03em",
          }}
        >
          {isUser ? "in" : "out"}
        </div>
        {(isUser || !message.streaming) && (
          <div style={{ color: "var(--text-dim)", fontSize: "10.5px", marginTop: 2 }}>
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
          <MarkdownPart
            content={message.parts[0]?.type === "text" ? message.parts[0].content : ""}
            tone="bright"
          />
        ) : (
          <>
            {/* Streaming indicator */}
            {message.streaming && message.parts.length === 0 && (
              <div style={{ color: "var(--text-dim)", fontSize: "12.5px", display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner" />
                thinking...
              </div>
            )}
            {message.parts.map((part, i) => {
              const isLast = i === message.parts.length - 1;
              const showCursor = isLast && !!message.streaming && part.type === "text";
              return renderPart(
                part,
                i,
                sessionId,
                showCursor,
                canAnswerQuestion && part.type === "question",
                onAnswerQuestion
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
