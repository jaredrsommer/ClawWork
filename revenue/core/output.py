"""
Output management for the Revenue Pipeline Engine.

Handles session directories, logs, and result display.
"""

import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class OutputManager:
    """Manages the output directory tree for all revenue sessions."""

    def __init__(self, base_dir: str = "./revenue/output"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def create_session_dir(self, stream_id: str, session_id: str) -> str:
        """Create and return the absolute path for this session's output."""
        session_dir = os.path.join(self.base_dir, stream_id, session_id)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir

    def save_session_log(self, session_result: Dict[str, Any], output_dir: str) -> str:
        """Persist the session result as _session_log.json."""
        log_path = os.path.join(output_dir, "_session_log.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(session_result, f, indent=2, default=str)
        return log_path

    def list_sessions(self, stream_id: Optional[str] = None) -> List[Dict]:
        """Return all session logs, newest first. Filter by stream_id if given."""
        search_root = (
            os.path.join(self.base_dir, stream_id) if stream_id else self.base_dir
        )
        sessions = []
        if not os.path.exists(search_root):
            return sessions

        for root, _dirs, files in os.walk(search_root):
            if "_session_log.json" in files:
                log_path = os.path.join(root, "_session_log.json")
                try:
                    with open(log_path, encoding="utf-8") as f:
                        sessions.append(json.load(f))
                except (json.JSONDecodeError, OSError):
                    pass

        return sorted(sessions, key=lambda x: x.get("session_id", ""), reverse=True)

    def print_sessions_table(self, sessions: List[Dict]) -> None:
        """Pretty-print a table of sessions."""
        if not sessions:
            print("  No sessions found.")
            return

        print(f"\n  {'SESSION ID':<42} {'STREAM':<18} {'STATUS':<10} {'FILES'}")
        print(f"  {'-'*42} {'-'*18} {'-'*10} {'-'*5}")
        for s in sessions:
            sid = s.get("session_id", "")[:42]
            stream = s.get("stream_id", "")[:18]
            status = s.get("status", "")[:10]
            files = len(s.get("created_files", []))
            print(f"  {sid:<42} {stream:<18} {status:<10} {files}")
        print()
