"use client";
import { useEffect, useState } from "react";
import { X, ArrowLeft } from "lucide-react";
import { getFileContent, fileUrl } from "../lib/api";
import { OpenTab } from "../lib/types";

interface Props {
  tabs: OpenTab[];
  activeTab: string | null;
  sessionId: string | null;
  onSelectTab: (path: string) => void;
  onCloseTab: (path: string) => void;
  onBackToTree: () => void;
}

const IMAGE_EXTS = new Set(["png", "jpg", "jpeg", "gif", "svg", "bmp", "webp"]);
const BINARY_EXTS = new Set(["hdf5", "h5", "vtk", "zip", "gz", "tar", "bin", "exe", "so", "dll"]);

function getExt(name: string): string {
  return name.split(".").pop()?.toLowerCase() ?? "";
}

export default function FileViewer({
  tabs,
  activeTab,
  sessionId,
  onSelectTab,
  onCloseTab,
  onBackToTree,
}: Props) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeFile = tabs.find((t) => t.path === activeTab);
  const ext = activeFile ? getExt(activeFile.name) : "";
  const isImage = IMAGE_EXTS.has(ext);
  const isBinary = BINARY_EXTS.has(ext);

  useEffect(() => {
    if (!sessionId || !activeTab || isImage || isBinary) {
      setContent(null);
      return;
    }
    setLoading(true);
    setError(null);
    getFileContent(sessionId, activeTab)
      .then((text) => {
        setContent(text);
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, [sessionId, activeTab, isImage, isBinary]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "var(--bg-panel)",
        borderLeft: "1px solid var(--border-subtle)",
        width: "var(--filetree-w)",
        flexShrink: 0,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 10px",
          height: "var(--header-h)",
          borderBottom: "1px solid var(--border-subtle)",
          flexShrink: 0,
        }}
      >
        <button
          onClick={onBackToTree}
          style={{
            background: "transparent",
            border: "none",
            cursor: "pointer",
            color: "var(--text-dim)",
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontSize: "10px",
            fontFamily: "var(--font-mono)",
            padding: "2px 4px",
          }}
        >
          <ArrowLeft size={12} />
          tree
        </button>
        <span
          style={{
            color: "var(--text-dim)",
            fontSize: "10px",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          files
        </span>
      </div>

      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          overflowX: "auto",
          borderBottom: "1px solid var(--border-faint)",
          flexShrink: 0,
        }}
      >
        {tabs.map((tab) => {
          const isActive = tab.path === activeTab;
          return (
            <div
              key={tab.path}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 4,
                padding: "4px 8px",
                fontSize: "10.5px",
                cursor: "pointer",
                background: isActive ? "var(--bg-surface)" : "transparent",
                borderBottom: isActive ? "2px solid var(--accent)" : "2px solid transparent",
                color: isActive ? "var(--text-primary)" : "var(--text-dim)",
                whiteSpace: "nowrap",
                flexShrink: 0,
              }}
              onClick={() => onSelectTab(tab.path)}
            >
              <span>{tab.name}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCloseTab(tab.path);
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--text-dim)",
                  display: "flex",
                  alignItems: "center",
                  padding: 0,
                }}
              >
                <X size={10} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Content area */}
      <div style={{ flex: 1, overflowY: "auto", padding: 0 }}>
        {!activeFile ? (
          <div
            style={{
              padding: "20px 12px",
              color: "var(--text-dim)",
              fontSize: "11px",
              textAlign: "center",
            }}
          >
            select a file
          </div>
        ) : isImage && sessionId ? (
          <div style={{ padding: 8 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={fileUrl(sessionId, activeTab!)}
              alt={activeFile.name}
              style={{
                maxWidth: "100%",
                border: "1px solid var(--border-mid)",
                borderRadius: 2,
              }}
            />
          </div>
        ) : isBinary ? (
          <div
            style={{
              padding: "20px 12px",
              color: "var(--text-dim)",
              fontSize: "11px",
              textAlign: "center",
            }}
          >
            binary file — cannot preview
          </div>
        ) : loading ? (
          <div
            style={{
              padding: "20px 12px",
              color: "var(--text-dim)",
              fontSize: "11px",
              textAlign: "center",
            }}
          >
            loading...
          </div>
        ) : error ? (
          <div
            style={{
              padding: "10px 12px",
              color: "var(--error)",
              fontSize: "11px",
            }}
          >
            {error}
          </div>
        ) : (
          <pre
            style={{
              background: "transparent",
              border: "none",
              padding: "8px 10px",
              fontSize: "11px",
              color: "var(--text-primary)",
              whiteSpace: "pre-wrap",
              wordBreak: "break-all",
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            {content}
          </pre>
        )}
      </div>
    </div>
  );
}
