"""
Medium Publisher

Publishes articles (draft or public) via the Medium API.

Required env vars:
  MEDIUM_ACCESS_TOKEN     Integration token from medium.com/me/settings

Setup:
  1. Go to https://medium.com/me/settings → Integration tokens
  2. Generate a token and add to .env as MEDIUM_ACCESS_TOKEN

Optional:
  MEDIUM_PUBLICATION_ID   Publish to a publication instead of personal profile

Best for streams: seo_content, research, publishing (book excerpts)
"""

import os
from typing import Any, Dict, List

import requests

from .base import BasePublisher

MEDIUM_API = "https://api.medium.com/v1"


class MediumPublisher(BasePublisher):
    platform = "medium"

    def required_env_vars(self) -> List[str]:
        return ["MEDIUM_ACCESS_TOKEN"]

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        settings = settings or {}
        token = os.getenv("MEDIUM_ACCESS_TOKEN")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            # Get author ID
            me_resp = requests.get(f"{MEDIUM_API}/me", headers=headers, timeout=10)
            if me_resp.status_code != 200:
                return {"success": False, "platform": self.platform, "error": f"Auth failed: {me_resp.status_code}"}
            user_id = me_resp.json()["data"]["id"]

            content = self.extract_content(session_result, stream_id)
            title = content["title"] or "Untitled"
            body_html = self._markdown_to_html(content["body"] or content["excerpt"])

            if not body_html.strip():
                return {"success": False, "platform": self.platform, "error": "No content to publish"}

            pub_id = os.getenv("MEDIUM_PUBLICATION_ID") or settings.get("publication_id")
            publish_status = settings.get("status", "draft")

            payload = {
                "title": title[:100],
                "contentFormat": "html",
                "content": f"<h1>{title}</h1>{body_html}",
                "publishStatus": publish_status,
                "tags": content.get("tags", [])[:5],
            }

            if pub_id:
                url = f"{MEDIUM_API}/publications/{pub_id}/posts"
            else:
                url = f"{MEDIUM_API}/users/{user_id}/posts"

            resp = requests.post(url, json=payload, headers=headers, timeout=30)

            if resp.status_code in (200, 201):
                data = resp.json().get("data", {})
                return {
                    "success": True,
                    "platform": self.platform,
                    "url": data.get("url", ""),
                    "id": data.get("id", ""),
                    "status": data.get("publishStatus", ""),
                }
            else:
                return {
                    "success": False,
                    "platform": self.platform,
                    "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
                }

        except Exception as exc:
            return {"success": False, "platform": self.platform, "error": str(exc)}
