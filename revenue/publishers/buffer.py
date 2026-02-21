"""
Buffer Publisher

Schedules posts across multiple platforms via Buffer's API.
Buffer handles: Twitter, LinkedIn, Facebook, Instagram, Pinterest, TikTok.

Using Buffer as a single integration eliminates the need to manage
platform-specific OAuth for every social network.

Required env vars:
  BUFFER_ACCESS_TOKEN     Access token from buffer.com/developers

Setup:
  1. Go to https://buffer.com/developers/apps → Create an App
  2. Get an access token → add to .env as BUFFER_ACCESS_TOKEN
  3. Configure BUFFER_PROFILE_IDS (comma-separated) for which accounts to post to
     OR leave empty to post to all connected accounts

Optional:
  BUFFER_PROFILE_IDS      Comma-separated profile IDs (e.g. "abc123,def456")
                          Find these in Buffer's API: GET /profiles.json

Best for: ghostwriting (schedule posts across the week), newsletter promos
"""

import os
from typing import Any, Dict, List, Optional

import requests

from .base import BasePublisher

BUFFER_API = "https://api.bufferapp.com/1"


class BufferPublisher(BasePublisher):
    platform = "buffer"

    def required_env_vars(self) -> List[str]:
        return ["BUFFER_ACCESS_TOKEN"]

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        settings = settings or {}
        token = os.getenv("BUFFER_ACCESS_TOKEN")

        try:
            # Get profile IDs
            profile_ids = self._get_profile_ids(token, settings)
            if not profile_ids:
                return {
                    "success": False,
                    "platform": self.platform,
                    "error": "No Buffer profiles found. Set BUFFER_PROFILE_IDS or connect accounts.",
                }

            content = self.extract_content(session_result, stream_id)
            posts_to_schedule = self._select_posts(content, stream_id, settings)

            scheduled_ids = []
            for post_text in posts_to_schedule:
                post_text = post_text[:500]  # Buffer limit
                if not post_text.strip():
                    continue

                payload = {
                    "text": post_text,
                    "profile_ids[]": profile_ids,
                    "shorten": True,
                }

                # Add to Buffer queue (scheduled automatically)
                resp = requests.post(
                    f"{BUFFER_API}/updates/create.json",
                    data={**payload, "access_token": token},
                    timeout=20,
                )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    updates = data.get("updates", [])
                    for u in updates:
                        scheduled_ids.append(u.get("id", ""))
                else:
                    return {
                        "success": False,
                        "platform": self.platform,
                        "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                    }

            return {
                "success": True,
                "platform": self.platform,
                "ids": scheduled_ids,
                "count": len(scheduled_ids),
                "url": "https://buffer.com/app/queue",
            }

        except Exception as exc:
            return {"success": False, "platform": self.platform, "error": str(exc)}

    def _get_profile_ids(self, token: str, settings: Dict) -> List[str]:
        """Get the list of Buffer profile IDs to post to."""
        # Manual override from env or settings
        env_ids = os.getenv("BUFFER_PROFILE_IDS", "")
        if env_ids:
            return [pid.strip() for pid in env_ids.split(",") if pid.strip()]

        setting_ids = settings.get("profile_ids", [])
        if setting_ids:
            return setting_ids

        # Fetch from API
        try:
            resp = requests.get(
                f"{BUFFER_API}/profiles.json",
                params={"access_token": token},
                timeout=10,
            )
            profiles = resp.json()
            return [p["id"] for p in profiles if p.get("default", False)][:3]
        except Exception:
            return []

    def _select_posts(self, content: Dict, stream_id: str, settings: Dict) -> List[str]:
        """Choose content to push to Buffer queue."""
        max_posts = settings.get("max_posts", 5)

        if stream_id == "ghostwriting":
            return content.get("posts", [])[:max_posts]

        if stream_id in ("newsletter", "podcast"):
            # Use social promo posts
            posts = content.get("posts", [])
            if posts:
                return posts[:max_posts]

        return [content.get("excerpt") or content.get("body", "")[:400]]
