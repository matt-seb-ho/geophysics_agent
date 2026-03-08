"use client";
import { useCallback, useEffect, useState } from "react";
import {
  Folder,
  FolderOpen,
  File,
  FileText,
  FileCode,
  FileImage,
  Database,
  Terminal,
} from "lucide-react";
import { getFileTree } from "../lib/api";
import { FileNode } from "../lib/types";

function getFileIcon(name: string, isOpen?: boolean) {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (isOpen !== undefined) {
    return isOpen ? (
      <FolderOpen size={13} style={{ flexShrink: 0 }} />
    ) : (
      <Folder size={13} style={{ flexShrink: 0 }} />
    );
  }
  if (["py", "js", "ts", "tsx", "jsx", "c", "cpp", "h", "java", "rs"].includes(ext))
    return <FileCode size={12} style={{ flexShrink: 0 }} />;
  if (["png", "jpg", "jpeg", "gif", "svg", "bmp", "webp"].includes(ext))
    return <FileImage size={12} style={{ flexShrink: 0 }} />;
  if (["hdf5", "h5", "db", "sqlite", "vtk"].includes(ext))
    return <Database size={12} style={{ flexShrink: 0 }} />;
  if (["sh", "bash", "zsh"].includes(ext))
    return <Terminal size={12} style={{ flexShrink: 0 }} />;
  if (["xml", "json", "yaml", "yml", "toml", "csv", "tsv", "txt", "md", "log"].includes(ext))
    return <FileText size={12} style={{ flexShrink: 0 }} />;
  return <File size={12} style={{ flexShrink: 0 }} />;
}

// File extension → color
function fileColor(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (["xml"].includes(ext))        return "#e07810";
  if (["csv", "tsv"].includes(ext)) return "#4d8a5f";
  if (["py"].includes(ext))         return "#4a8fbf";
  if (["json"].includes(ext))       return "#9b7ec4";
  if (["log", "txt"].includes(ext)) return "#666666";
  if (["png", "jpg", "svg"].includes(ext)) return "#c47f0a";
  if (["hdf5", "h5", "vtk"].includes(ext)) return "#bf3b30";
  return "#888888";
}

function formatSize(bytes?: number): string {
  if (bytes === undefined) return "";
  if (bytes < 1024)       return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`;
  return `${(bytes / 1024 / 1024).toFixed(1)}M`;
}

interface NodeProps {
  node: FileNode;
  depth: number;
  sessionId: string;
  onOpenFile?: (path: string, name: string) => void;
}

function TreeNode({ node, depth, sessionId, onOpenFile }: NodeProps) {
  const [expanded, setExpanded] = useState(depth === 0 || node.name === "inputs" || node.name === "outputs");

  const indent = depth * 12;

  if (node.type === "directory") {
    const hasChildren = node.children && node.children.length > 0;
    return (
      <div>
        <button
          onClick={() => setExpanded((v) => !v)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            width: "100%",
            padding: `2px 8px 2px ${8 + indent}px`,
            background: "transparent",
            border: "none",
            cursor: hasChildren ? "pointer" : "default",
            color: "var(--text-secondary)",
            fontSize: "11.5px",
            fontFamily: "var(--font-mono)",
            textAlign: "left",
          }}
          onMouseEnter={(e) => {
            if (hasChildren) (e.currentTarget as HTMLElement).style.background = "var(--bg-hover)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = "transparent";
          }}
        >
          <span style={{ fontSize: 9, width: 10, flexShrink: 0, color: "var(--text-dim)" }}>
            {!hasChildren ? "" : expanded ? "▼" : "▶"}
          </span>
          <span style={{ color: "var(--accent)", display: "flex", alignItems: "center" }}>
            {getFileIcon(node.name, expanded)}
          </span>
          <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>
            {node.name}
          </span>
          {node.children && (
            <span style={{ color: "var(--text-dim)", fontSize: 10, marginLeft: "auto", paddingRight: 4 }}>
              {node.children.length}
            </span>
          )}
        </button>

        {expanded && node.children && (
          <div>
            {node.children.map((child) => (
              <TreeNode
                key={child.path}
                node={child}
                depth={depth + 1}
                sessionId={sessionId}
                onOpenFile={onOpenFile}
              />
            ))}
            {node.children.length === 0 && (
              <div
                style={{
                  padding: `1px 8px 1px ${8 + indent + 22}px`,
                  color: "var(--text-dim)",
                  fontSize: "11px",
                  fontStyle: "italic",
                }}
              >
                empty
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // File node
  const color = fileColor(node.name);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpenFile?.(node.path, node.name)}
      onKeyDown={(e) => { if (e.key === "Enter") onOpenFile?.(node.path, node.name); }}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 5,
        padding: `2px 8px 2px ${8 + indent + 15}px`,
        color: "var(--text-secondary)",
        fontSize: "11.5px",
        textDecoration: "none",
        cursor: "pointer",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.background = "var(--bg-hover)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.background = "transparent";
      }}
    >
      <span style={{ color, display: "flex", alignItems: "center" }}>{getFileIcon(node.name)}</span>
      <span style={{ color, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {node.name}
      </span>
      <span style={{ color: "var(--text-dim)", fontSize: "10px", flexShrink: 0 }}>
        {formatSize(node.size)}
      </span>
    </div>
  );
}

interface Props {
  sessionId: string | null;
  refreshKey: number;
  workspacePath: string;
  onOpenFile?: (path: string, name: string) => void;
}

export default function FileTree({ sessionId, refreshKey, workspacePath, onOpenFile }: Props) {
  const [tree, setTree] = useState<FileNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<string>("");

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getFileTree(sessionId);
      setTree(data.tree);
      setWorkspace(data.workspace);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const displayPath = workspace || workspacePath || "—";
  const shortPath =
    displayPath.length > 28
      ? "…" + displayPath.slice(displayPath.length - 27)
      : displayPath;

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
        <span
          style={{
            color: "var(--text-dim)",
            fontSize: "10px",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          workspace
        </span>
        <button
          onClick={load}
          disabled={loading || !sessionId}
          title="Refresh"
          style={{
            background: "transparent",
            border: "none",
            cursor: loading || !sessionId ? "default" : "pointer",
            color: "var(--text-dim)",
            fontSize: "12px",
            padding: "2px 4px",
            borderRadius: 2,
          }}
          onMouseEnter={(e) => {
            if (!loading && sessionId)
              (e.currentTarget as HTMLElement).style.color = "var(--accent)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.color = "var(--text-dim)";
          }}
        >
          {loading ? (
            <span className="spinning" style={{ display: "inline-block" }}>↻</span>
          ) : (
            "↻"
          )}
        </button>
      </div>

      {/* Workspace path */}
      <div
        style={{
          padding: "5px 10px",
          borderBottom: "1px solid var(--border-faint)",
          flexShrink: 0,
        }}
      >
        <div
          title={displayPath}
          style={{
            color: "var(--text-dim)",
            fontSize: "10.5px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {shortPath}
        </div>
      </div>

      {/* Tree content */}
      <div style={{ flex: 1, overflowY: "auto", paddingTop: 4, paddingBottom: 8 }}>
        {!sessionId ? (
          <div
            style={{
              padding: "16px 12px",
              color: "var(--text-dim)",
              fontSize: "11.5px",
              textAlign: "center",
            }}
          >
            no active session
          </div>
        ) : error ? (
          <div
            style={{
              padding: "10px 12px",
              color: "var(--error)",
              fontSize: "11.5px",
            }}
          >
            {error}
          </div>
        ) : loading && !tree ? (
          <div
            style={{
              padding: "16px 12px",
              color: "var(--text-dim)",
              fontSize: "11.5px",
              textAlign: "center",
            }}
          >
            loading...
          </div>
        ) : tree ? (
          <TreeNode node={tree} depth={0} sessionId={sessionId} onOpenFile={onOpenFile} />
        ) : (
          <div
            style={{
              padding: "16px 12px",
              color: "var(--text-dim)",
              fontSize: "11.5px",
              textAlign: "center",
            }}
          >
            send a message to start
          </div>
        )}
      </div>
    </div>
  );
}
