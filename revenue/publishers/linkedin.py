"""
LinkedIn Publisher

Posts text updates and articles via LinkedIn API v2 (UGC Posts).

Required env vars:
  LINKEDIN_ACCESS_TOKEN   OAuth 2.0 access token with w_member_social scope

Setup:
  1. Create a LinkedIn app at https://developer.linkedin.com
  2. Request r_liteprofile + w_member_social permissions
  3. Generate an access token (valid 60 days — automate refresh with LINKEDIN_REFRESH_TOKEN)
  4. Add LINKEDIN_ACCESS_TOKEN to .env

Content handling by stream:
  ghostwriting  → posts each individual post (up to 5 per run)
  newsletter    → posts the LinkedIn promo post from social_promo file
  seo_content   → posts a teaser excerpt with link
  research      → posts the executive summary
  podcast       → posts the LinkedIn section from social_posts
  data_analysis → posts top 3 findings as a professional update
"""

import os
from typing import Any, Dict, List, Optional

import requests

from .base import BasePublisher


LINKEDIN_API = "https://api.linkedin.com/v2"


class LinkedInPublisher(BasePublisher):
    platform = "linkedin"

    def required_env_vars(self) -> List[str]:
        return ["LINKEDIN_ACCESS_TOKEN"]

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        settings = settings or {}
        token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        try:
            # Get the authenticated user's URN
            author_urn = self._get_author_urn(headers)
            if not author_urn:
                return {"success": False, "platform": self.platform, "error": "Could not fetch LinkedIn profile"}

            content = self.extract_content(session_result, stream_id)
            posts_to_publish = self._select_posts(content, stream_id, settings)

            posted_ids = []
            for post_text in posts_to_publish[:5]:  # LinkedIn allows up to 5 posts/day
                post_text = self._clean_for_linkedin(post_text)
                if not post_text:
                    continue

                payload = {
                    "author": author_urn,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": post_text[:3000],  # LinkedIn 3k char limit
                            },
                            "shareMediaCategory": "NONE",
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": settings.get(
                            "visibility", "PUBLIC"
                        )
                    },
                }

                resp = requests.post(
                    f"{LINKEDIN_API}/ugcPosts",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )

                if resp.status_code == 201:
                    post_id = resp.headers.get("X-RestLi-Id", "")
                    posted_ids.append(post_id)
                else:
                    return {
                        "success": False,
                        "platform": self.platform,
                        "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
                    }

            return {
                "success": True,
                "platform": self.platform,
                "ids": posted_ids,
                "count": len(posted_ids),
                "url": f"https://www.linkedin.com/feed/update/{posted_ids[0]}/" if posted_ids else "",
            }

        except Exception as exc:
            return {"success": False, "platform": self.platform, "error": str(exc)}

    def _get_author_urn(self, headers: Dict) -> Optional[str]:
        """Fetch the authenticated user's LinkedIn URN."""
        try:
            resp = requests.get(f"{LINKEDIN_API}/me", headers=headers, timeout=10)
            if resp.status_code == 200:
                person_id = resp.json().get("id", "")
                return f"urn:li:person:{person_id}"
        except Exception:
            pass
        # Allow manual override
        manual = os.getenv("LINKEDIN_PERSON_URN")
        return manual

    def _select_posts(self, content: Dict, stream_id: str, settings: Dict) -> List[str]:
        """Choose what to post on LinkedIn."""
        # LinkedIn promo from social files takes priority
        lnk_section = self._find_linkedin_section(content.get("posts", []))
        if lnk_section:
            return [lnk_section]

        if stream_id == "ghostwriting" and content.get("posts"):
            return content["posts"]

        if stream_id in ("newsletter", "podcast") and content.get("posts"):
            return content["posts"][:1]

        if stream_id in ("research", "data_analysis", "seo_content"):
            return [content.get("excerpt") or content.get("body", "")[:2500]]

        return [content.get("excerpt") or content.get("body", "")[:2500]]

    def _find_linkedin_section(self, posts: List[str]) -> Optional[str]:
        """Find a LinkedIn-specific section in the posts list."""
        for post in posts:
            if "linkedin" in post.lower()[:100]:
                return post
        return None

    def _clean_for_linkedin(self, text: str) -> str:
        """Minimal cleanup — LinkedIn supports line breaks and emoji."""
        import re
        # Remove H1/H2 markdown headers (keep content)
        text = re.sub(r"^#{1,3}\s+", "", text, flags=re.MULTILINE)
        # LinkedIn doesn't render markdown bold/italic — remove markers
        text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1 ", text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()
