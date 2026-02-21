"""
WordPress Publisher

Publishes posts via the WordPress REST API (v2).
Works with any self-hosted WordPress or WordPress.com site.

Required env vars:
  WORDPRESS_URL           Full site URL (e.g. https://yourblog.com)
  WORDPRESS_USER          WP username
  WORDPRESS_APP_PASSWORD  Application password (WP Admin → Users → Application Passwords)

Setup:
  1. WP Admin → Users → Your Profile → Application Passwords → Add New
  2. Copy the generated password (spaces included) and add to .env

Optional:
  WORDPRESS_CATEGORY_ID   Default category ID for posts
  WORDPRESS_AUTHOR_ID     Author user ID (defaults to authenticated user)

Best for: seo_content, research, publishing (serialized book chapters)
"""

import os
import base64
from typing import Any, Dict, List

import requests

from .base import BasePublisher


class WordPressPublisher(BasePublisher):
    platform = "wordpress"

    def required_env_vars(self) -> List[str]:
        return ["WORDPRESS_URL", "WORDPRESS_USER", "WORDPRESS_APP_PASSWORD"]

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        settings = settings or {}

        wp_url = os.getenv("WORDPRESS_URL", "").rstrip("/")
        user = os.getenv("WORDPRESS_USER", "")
        app_pass = os.getenv("WORDPRESS_APP_PASSWORD", "")

        # WordPress Application Password auth (Basic)
        token = base64.b64encode(f"{user}:{app_pass}".encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

        try:
            content = self.extract_content(session_result, stream_id)
            title = content["title"] or "Untitled Post"
            body_html = self._markdown_to_html(content["body"] or content["excerpt"])

            if not body_html.strip():
                return {"success": False, "platform": self.platform, "error": "No content to publish"}

            # Build excerpt
            excerpt_text = content.get("excerpt", "")[:300]

            payload = {
                "title": title,
                "content": body_html,
                "excerpt": excerpt_text,
                "status": settings.get("status", "draft"),
                "format": "standard",
            }

            # Optional category
            cat_id = os.getenv("WORDPRESS_CATEGORY_ID") or settings.get("category_id")
            if cat_id:
                payload["categories"] = [int(cat_id)]

            # Tags
            if content.get("tags"):
                payload["tags"] = self._get_or_create_tags(
                    content["tags"][:5], wp_url, headers
                )

            resp = requests.post(
                f"{wp_url}/wp-json/wp/v2/posts",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "success": True,
                    "platform": self.platform,
                    "url": data.get("link", ""),
                    "id": str(data.get("id", "")),
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

    def _get_or_create_tags(
        self, tag_names: List[str], wp_url: str, headers: Dict
    ) -> List[int]:
        """Fetch existing tags or create new ones. Returns list of tag IDs."""
        tag_ids = []
        for name in tag_names:
            try:
                # Try to find existing
                resp = requests.get(
                    f"{wp_url}/wp-json/wp/v2/tags",
                    params={"search": name},
                    headers=headers,
                    timeout=10,
                )
                existing = resp.json()
                if existing:
                    tag_ids.append(existing[0]["id"])
                    continue
                # Create new
                create = requests.post(
                    f"{wp_url}/wp-json/wp/v2/tags",
                    json={"name": name},
                    headers=headers,
                    timeout=10,
                )
                if create.status_code == 201:
                    tag_ids.append(create.json()["id"])
            except Exception:
                continue
        return tag_ids
