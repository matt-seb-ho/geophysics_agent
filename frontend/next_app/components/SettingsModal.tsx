"use client";
import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Select from "@radix-ui/react-select";
import { ChevronDown, ChevronRight, X } from "lucide-react";
import { AVAILABLE_MODELS, SessionConfig } from "../lib/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: SessionConfig;
  setConfig: (c: SessionConfig) => void;
  workspacePath: string;
  onWorkspaceChange: (path: string) => void;
}

function SectionLabel({ label }: { label: string }) {
  return (
    <div
      style={{
        color: "var(--text-dim)",
        fontSize: "9.5px",
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        marginBottom: 6,
        marginTop: 14,
      }}
    >
      {label}
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ color: "var(--text-secondary)", fontSize: "11px", marginBottom: 4 }}>
        {label}
      </div>
      {children}
      {hint && (
        <div style={{ color: "var(--text-dim)", fontSize: "10px", marginTop: 3 }}>
          {hint}
        </div>
      )}
    </div>
  );
}

function inputStyle(): React.CSSProperties {
  return {
    width: "100%",
    padding: "5px 8px",
    background: "var(--bg-elevated)",
    border: "1px solid var(--border-mid)",
    color: "var(--text-primary)",
    fontSize: "11.5px",
    fontFamily: "var(--font-mono)",
    borderRadius: 2,
    outline: "none",
  };
}

function Checkbox({
  checked,
  label,
  hint,
  onChange,
}: {
  checked: boolean;
  label: string;
  hint?: string;
  onChange: () => void;
}) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 7,
          cursor: "pointer",
        }}
        onClick={onChange}
      >
        <input type="checkbox" checked={checked} readOnly style={{ cursor: "pointer" }} />
        <span style={{ color: "var(--text-secondary)", fontSize: "11.5px" }}>{label}</span>
      </div>
      {hint && (
        <div style={{ color: "var(--text-dim)", fontSize: "10px", marginTop: 2, paddingLeft: 19 }}>
          {hint}
        </div>
      )}
    </div>
  );
}

export default function SettingsModal({
  open,
  onOpenChange,
  config,
  setConfig,
  workspacePath,
  onWorkspaceChange,
}: Props) {
  const [advancedOpen, setAdvancedOpen] = useState(false);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="radix-dialog-overlay" />
        <Dialog.Content
          className="radix-dialog-content"
          style={{
            background: "var(--bg-panel)",
            border: "1px solid var(--border-mid)",
            borderRadius: 4,
            width: 420,
            padding: "16px 20px 20px",
            fontFamily: "var(--font-mono)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 4,
            }}
          >
            <Dialog.Title
              style={{
                color: "var(--text-bright)",
                fontSize: "12px",
                fontWeight: 600,
                letterSpacing: "0.06em",
              }}
            >
              Settings
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-dim)",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <X size={14} />
              </button>
            </Dialog.Close>
          </div>

          {/* MODEL */}
          <SectionLabel label="model" />
          <Field label="provider/model">
            <Select.Root
              value={config.model}
              onValueChange={(v) => setConfig({ ...config, model: v })}
            >
              <Select.Trigger
                style={{
                  ...inputStyle(),
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  cursor: "pointer",
                }}
              >
                <Select.Value />
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
                    {AVAILABLE_MODELS.map((m) => (
                      <Select.Item key={m} value={m} className="radix-select-item">
                        <Select.ItemText>{m}</Select.ItemText>
                      </Select.Item>
                    ))}
                  </Select.Viewport>
                </Select.Content>
              </Select.Portal>
            </Select.Root>
          </Field>

          <Field label="provider override" hint="Route to a specific OpenRouter provider">
            <input
              type="text"
              value={config.provider}
              onChange={(e) => setConfig({ ...config, provider: e.target.value })}
              placeholder="e.g. baseten, novita, together"
              style={inputStyle()}
            />
          </Field>

          {/* Advanced model options (collapsible) */}
          <button
            onClick={() => setAdvancedOpen((v) => !v)}
            style={{
              background: "transparent",
              border: "none",
              cursor: "pointer",
              color: "var(--text-secondary)",
              fontSize: "11px",
              fontFamily: "var(--font-mono)",
              display: "flex",
              alignItems: "center",
              gap: 4,
              padding: "4px 0",
              marginBottom: 4,
            }}
          >
            {advancedOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            advanced model options
          </button>

          {advancedOpen && (
            <div
              style={{
                padding: "8px 0 4px 8px",
                borderLeft: "2px solid var(--border-mid)",
                marginBottom: 8,
              }}
            >
              <Checkbox
                checked={config.enableReasoning}
                label="Enable reasoning"
                hint="Request reasoning tokens for models that support them"
                onChange={() => setConfig({ ...config, enableReasoning: !config.enableReasoning })}
              />

              <Checkbox
                checked={config.enablePromptCaching}
                label="Enable prompt caching"
                hint="Use provider prompt caching where available"
                onChange={() => setConfig({ ...config, enablePromptCaching: !config.enablePromptCaching })}
              />

              <Field label="prompt cache TTL" hint="Anthropic cache TTL override">
                <Select.Root
                  value={config.promptCacheTtl}
                  onValueChange={(v) => setConfig({ ...config, promptCacheTtl: v })}
                >
                  <Select.Trigger
                    style={{
                      ...inputStyle(),
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      cursor: "pointer",
                    }}
                  >
                    <Select.Value />
                    <Select.Icon>
                      <ChevronDown size={12} style={{ color: "var(--text-dim)" }} />
                    </Select.Icon>
                  </Select.Trigger>
                  <Select.Portal>
                    <Select.Content className="radix-select-content" position="popper" sideOffset={4}>
                      <Select.Viewport>
                        <Select.Item value="default" className="radix-select-item">
                          <Select.ItemText>default</Select.ItemText>
                        </Select.Item>
                        <Select.Item value="1h" className="radix-select-item">
                          <Select.ItemText>1h</Select.ItemText>
                        </Select.Item>
                      </Select.Viewport>
                    </Select.Content>
                  </Select.Portal>
                </Select.Root>
              </Field>

              <Field label={`auto-compact after tokens: ${config.autoCompactAfterTokens.toLocaleString()}`} hint="0 to disable">
                <input
                  type="number"
                  min={0}
                  max={2000000}
                  step={10000}
                  value={config.autoCompactAfterTokens}
                  onChange={(e) => setConfig({ ...config, autoCompactAfterTokens: parseInt(e.target.value) || 0 })}
                  style={inputStyle()}
                />
              </Field>

              <Field label={`temperature: ${config.temperature.toFixed(2)}`}>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.05}
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  style={{ width: "100%" }}
                />
              </Field>

              <Field label={`top p: ${config.topP.toFixed(2)}`}>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={config.topP}
                  onChange={(e) => setConfig({ ...config, topP: parseFloat(e.target.value) })}
                  style={{ width: "100%" }}
                />
              </Field>

              <Field label={`frequency penalty: ${config.frequencyPenalty.toFixed(1)}`}>
                <input
                  type="range"
                  min={-2}
                  max={2}
                  step={0.1}
                  value={config.frequencyPenalty}
                  onChange={(e) => setConfig({ ...config, frequencyPenalty: parseFloat(e.target.value) })}
                  style={{ width: "100%" }}
                />
              </Field>

              <Field label={`presence penalty: ${config.presencePenalty.toFixed(1)}`}>
                <input
                  type="range"
                  min={-2}
                  max={2}
                  step={0.1}
                  value={config.presencePenalty}
                  onChange={(e) => setConfig({ ...config, presencePenalty: parseFloat(e.target.value) })}
                  style={{ width: "100%" }}
                />
              </Field>

              <Field label="seed" hint="Optional deterministic seed">
                <input
                  type="text"
                  value={config.seed}
                  onChange={(e) => setConfig({ ...config, seed: e.target.value })}
                  placeholder="optional integer"
                  style={inputStyle()}
                />
              </Field>

              <Field label={`max output tokens: ${config.maxOutputTokens.toLocaleString()}`}>
                <input
                  type="number"
                  min={1}
                  max={200000}
                  step={1000}
                  value={config.maxOutputTokens}
                  onChange={(e) => setConfig({ ...config, maxOutputTokens: parseInt(e.target.value) || 50000 })}
                  style={inputStyle()}
                />
              </Field>

              <Field label="extra OpenRouter JSON" hint="Merged into OpenRouter request body">
                <textarea
                  value={config.openrouterExtraBody}
                  onChange={(e) => setConfig({ ...config, openrouterExtraBody: e.target.value })}
                  placeholder='{"provider":{"allow_fallbacks":false}}'
                  rows={3}
                  style={{
                    ...inputStyle(),
                    resize: "vertical",
                    minHeight: 50,
                    lineHeight: 1.4,
                  }}
                />
              </Field>
            </div>
          )}

          {/* AGENT */}
          <SectionLabel label="agent" />
          <Field label={`max steps per turn: ${config.maxSteps}`}>
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

          <Checkbox
            checked={config.enableContextCompaction}
            label="Context compaction"
            onChange={() =>
              setConfig({
                ...config,
                enableContextCompaction: !config.enableContextCompaction,
              })
            }
          />

          {/* WORKSPACE */}
          <SectionLabel label="workspace" />
          <Field label="directory" hint="Agent reads/writes here">
            <input
              type="text"
              value={workspacePath}
              onChange={(e) => onWorkspaceChange(e.target.value)}
              placeholder="auto (temp dir)"
              style={inputStyle()}
            />
          </Field>

          {/* LOGGING */}
          <SectionLabel label="logging" />
          <Checkbox
            checked={config.enableLogging}
            label="Persist chat history to Convex"
            hint="Stores workspace path, messages, pending prompts, and token counts in Convex when the backend has CONVEX_URL set"
            onChange={() =>
              setConfig({ ...config, enableLogging: !config.enableLogging })
            }
          />

          {config.enableLogging && (
            <Field label="backend requirement" hint="Configure CONVEX_URL in the FastAPI environment for persistence to be active">
              <input
                type="text"
                value="CONVEX_URL"
                readOnly
                style={{ ...inputStyle(), color: "var(--text-dim)" }}
              />
            </Field>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
