import { SessionConfig, defaultConfig } from "./types";

const CONFIG_KEY = "geos_config";
const WORKSPACE_KEY = "geos_workspace";

export function loadConfig(): SessionConfig {
  if (typeof window === "undefined") return defaultConfig;
  try {
    const raw = localStorage.getItem(CONFIG_KEY);
    if (!raw) return defaultConfig;
    return { ...defaultConfig, ...JSON.parse(raw) };
  } catch {
    return defaultConfig;
  }
}

export function saveConfig(config: SessionConfig): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
  } catch {}
}

export function loadWorkspace(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(WORKSPACE_KEY) ?? "";
}

export function saveWorkspace(path: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(WORKSPACE_KEY, path);
  } catch {}
}
