from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


class ConvexStoreError(RuntimeError):
    pass


@dataclass
class ConvexChatStore:
    deployment_url: str
    timeout: float = 15.0

    @classmethod
    def from_env(cls) -> "ConvexChatStore | None":
        url = (os.environ.get("CONVEX_URL") or "").strip().rstrip("/")
        if not url:
            return None
        return cls(deployment_url=url)

    @property
    def enabled(self) -> bool:
        return bool(self.deployment_url)

    def _post(self, endpoint: str, path: str, args: Dict[str, Any]) -> Any:
        if not self.enabled:
            raise ConvexStoreError("CONVEX_URL is not configured")

        url = f"{self.deployment_url}/api/{endpoint}"
        payload = {"path": path, "args": args}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ConvexStoreError(f"Convex {endpoint} failed: {exc}") from exc

        data = response.json()
        status = data.get("status")
        if status != "success":
            raise ConvexStoreError(f"Convex {endpoint} error: {data}")
        return data.get("value")

    def query(self, path: str, args: Optional[Dict[str, Any]] = None) -> Any:
        return self._post("query", path, args or {})

    def mutation(self, path: str, args: Optional[Dict[str, Any]] = None) -> Any:
        return self._post("mutation", path, args or {})

    def list_sessions(self) -> List[Dict[str, Any]]:
        return self.query("chatHistory:listSessions", {})

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.query("chatHistory:getSessionState", {"sessionId": session_id})

    def save_session_state(self, payload: Dict[str, Any]) -> None:
        self.mutation("chatHistory:saveSessionState", payload)

    def rename_session(self, session_id: str, name: str) -> Optional[Dict[str, Any]]:
        return self.mutation(
            "chatHistory:renameSession",
            {"sessionId": session_id, "name": name},
        )

    def delete_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.mutation("chatHistory:deleteSession", {"sessionId": session_id})
