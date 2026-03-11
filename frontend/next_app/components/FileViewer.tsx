"use client";
import { useEffect, useState } from "react";
import { getFileContent, fileUrl } from "../lib/api";
import { OpenTab } from "../lib/types";

interface Props {
  file: OpenTab | null;
  sessionId: string | null;
}

const IMAGE_EXTS = new Set(["png", "jpg", "jpeg", "gif", "svg", "bmp", "webp"]);
const BINARY_EXTS = new Set(["hdf5", "h5", "vtk", "zip", "gz", "tar", "bin", "exe", "so", "dll"]);

function getExt(name: string): string {
  return name.split(".").pop()?.toLowerCase() ?? "";
}

export default function FileViewer({
  file,
  sessionId,
}: Props) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ext = file ? getExt(file.name) : "";
  const isImage = IMAGE_EXTS.has(ext);
  const isBinary = BINARY_EXTS.has(ext);
  useEffect(() => {
    if (!sessionId || !file || isImage || isBinary) {
      setContent(null);
      return;
    }
    setLoading(true);
    setError(null);
    getFileContent(sessionId, file.path)
      .then((text) => {
        setContent(text);
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, [sessionId, file, isImage, isBinary]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "var(--bg-base)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "0 14px",
          height: "var(--header-h)",
          borderBottom: "1px solid var(--border-subtle)",
          flexShrink: 0,
          background: "var(--bg-panel)",
        }}
      >
        <div
          style={{
            color: "var(--text-bright)",
            fontSize: "12px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            minWidth: 0,
          }}
          title={file?.path ?? ""}
        >
          {file?.path ?? "No file selected"}
        </div>
        <span
          style={{
            color: "var(--text-secondary)",
            fontSize: "10px",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          preview
        </span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 0 }}>
        {!file ? (
          <div
            style={{
              padding: "20px 12px",
              color: "var(--text-dim)",
              fontSize: "12px",
              textAlign: "center",
            }}
          >
            select a file
          </div>
        ) : isImage && sessionId ? (
          <div style={{ padding: 12 }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={fileUrl(sessionId, file.path)}
              alt={file.name}
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
              fontSize: "12px",
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
              fontSize: "12px",
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
              fontSize: "12px",
            }}
          >
            {error}
          </div>
        ) : (
          <pre
            style={{
              background: "transparent",
              border: "none",
              padding: "12px 14px",
              fontSize: "12.5px",
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
