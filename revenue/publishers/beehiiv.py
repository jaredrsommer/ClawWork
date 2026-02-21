"""
Beehiiv Publisher

Creates newsletter posts via the Beehiiv API v2.

Required env vars:
  BEEHIIV_API_KEY          API key from app.beehiiv.com/settings/integrations
  BEEHIIV_PUBLICATION_ID   Publication ID (found in Beehiiv URL or settings)

Setup:
  1. Go to app.beehiiv.com → Settings → Integrations → API
  2. Generate an API key → add to .env
  3. Get your Publication ID from app.beehiiv.com/publications/<ID>/settings

Best for: newsletter stream (primary), research reports as bonus content
"""

import os
from typing import Any, Dict, List

import requests

from .base import BasePublisher

BEEHIIV_API = "https://api.beehiiv.com/v2"


class BeehiivPublisher(BasePublisher):
    platform = "beehiiv"

    def required_env_vars(self) -> List[str]:
        return ["BEEHIIV_API_KEY", "BEEHIIV_PUBLICATION_ID"]

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        settings = settings or {}
        api_key = os.getenv("BEEHIIV_API_KEY")
        pub_id = os.getenv("BEEHIIV_PUBLICATION_ID")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            content = self.extract_content(session_result, stream_id)
            title = content["title"] or "Newsletter Issue"
            body_html = self._markdown_to_html(content["body"] or content["excerpt"])

            if not body_html.strip():
                return {"success": False, "platform": self.platform, "error": "No content to publish"}

            # Beehiiv post payload
            payload = {
                "subject": title[:150],
                "preview_text": self._make_preview(content),
                "content_json": None,  # Use HTML path
                "content_html": body_html,
                "content_text": content.get("body") or content.get("excerpt", ""),
                "status": settings.get("status", "draft"),
                "send_at": None,  # Null = don't schedule immediately
                "displayed_date": None,
                "meta_default_description": content.get("excerpt", "")[:160],
                "audience": settings.get("audience", "free"),
            }

            resp = requests.post(
                f"{BEEHIIV_API}/publications/{pub_id}/posts",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                data = resp.json().get("data", {})
                post_id = data.get("id", "")
                web_url = data.get("web_url", "")
                return {
                    "success": True,
                    "platform": self.platform,
                    "id": post_id,
                    "url": web_url or f"https://app.beehiiv.com/publications/{pub_id}/posts/{post_id}",
                    "status": data.get("status", ""),
                }
            else:
                return {
                    "success": False,
                    "platform": self.platform,
                    "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
                }

        except Exception as exc:
            return {"success": False, "platform": self.platform, "error": str(exc)}

    def _make_preview(self, content: Dict) -> str:
        """Generate a 100-char preview text for the email preview snippet."""
        preview = content.get("excerpt") or content.get("body", "")
        # Strip markdown
        import re
        preview = re.sub(r"[#*`\[\]()]", "", preview)
        preview = re.sub(r"\s+", " ", preview)
        return preview.strip()[:100]
