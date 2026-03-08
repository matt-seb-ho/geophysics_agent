"use client";
import * as Dialog from "@radix-ui/react-dialog";
import * as Select from "@radix-ui/react-select";
import { ChevronDown, X } from "lucide-react";
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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ color: "var(--text-secondary)", fontSize: "11px", marginBottom: 4 }}>
        {label}
      </div>
      {children}
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

export default function SettingsModal({
  open,
  onOpenChange,
  config,
  setConfig,
  workspacePath,
  onWorkspaceChange,
}: Props) {
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
            width: 380,
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

          <Field label="provider override">
            <input
              type="text"
              value={config.provider}
              onChange={(e) => setConfig({ ...config, provider: e.target.value })}
              placeholder="e.g. baseten, novita"
              style={inputStyle()}
            />
          </Field>

          {/* AGENT */}
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
              marginBottom: 10,
              cursor: "pointer",
            }}
            onClick={() =>
              setConfig({
                ...config,
                enableContextCompaction: !config.enableContextCompaction,
              })
            }
          >
            <input
              type="checkbox"
              checked={config.enableContextCompaction}
              readOnly
              style={{ cursor: "pointer" }}
            />
            <span style={{ color: "var(--text-secondary)", fontSize: "11.5px" }}>
              context compaction
            </span>
          </div>

          {/* WORKSPACE */}
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
              marginBottom: 10,
              marginTop: -6,
            }}
          >
            agent reads/writes here
          </div>

          {/* LOGGING */}
          <SectionLabel label="logging" />
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              marginBottom: 8,
              cursor: "pointer",
            }}
            onClick={() =>
              setConfig({ ...config, enableLogging: !config.enableLogging })
            }
          >
            <input
              type="checkbox"
              checked={config.enableLogging}
              readOnly
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
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
