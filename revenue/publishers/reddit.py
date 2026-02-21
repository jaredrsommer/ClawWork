"""
Reddit Publisher

Posts to relevant subreddits via PRAW (Python Reddit API Wrapper).

Required env vars:
  REDDIT_CLIENT_ID       App client ID from reddit.com/prefs/apps
  REDDIT_CLIENT_SECRET   App secret
  REDDIT_USERNAME        Your Reddit username
  REDDIT_PASSWORD        Your Reddit password

Setup:
  1. Go to https://www.reddit.com/prefs/apps → Create App
  2. Select "script" type → fill in redirect URI (http://localhost)
  3. Copy client_id (under app name) and client_secret
  4. Add all 4 vars to .env

Configuration:
  Set target subreddits in scheduler_config.json → publisher_settings → reddit → subreddits
  e.g. ["r/artificial", "r/MachineLearning", "r/learnprogramming"]

Content rules:
  - Self-post (text) for research reports and long-form articles
  - Link post for articles on WordPress/Medium
  - Flair and post rules vary by subreddit — always check rules before posting
  - Be a community contributor — do not spam or over-promote

Best for: research, seo_content (when also published to WordPress/Medium), data_analysis
"""

import os
from typing import Any, Dict, List, Optional

from .base import BasePublisher


class RedditPublisher(BasePublisher):
    platform = "reddit"

    def required_env_vars(self) -> List[str]:
        return [
            "REDDIT_CLIENT_ID",
            "REDDIT_CLIENT_SECRET",
            "REDDIT_USERNAME",
            "REDDIT_PASSWORD",
        ]

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        settings = settings or {}
        try:
            import praw
        except ImportError:
            return {
                "success": False,
                "platform": self.platform,
                "error": "praw not installed — run: pip install praw",
            }

        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                username=os.getenv("REDDIT_USERNAME"),
                password=os.getenv("REDDIT_PASSWORD"),
                user_agent=f"RevenueBot/1.0 (by u/{os.getenv('REDDIT_USERNAME')})",
            )

            content = self.extract_content(session_result, stream_id)
            subreddits = settings.get("subreddits", [])
            if not subreddits:
                return {
                    "success": False,
                    "platform": self.platform,
                    "error": "No subreddits configured. Add 'subreddits' to publisher_settings.reddit in scheduler_config.json",
                }

            title = content["title"] or "Untitled"
            body = content["body"] or content["excerpt"] or ""

            # External URL takes priority (from WordPress/Medium publish)
            external_url = session_result.get("_published_url")

            posted_urls = []
            for subreddit_name in subreddits[:2]:  # max 2 subreddits per run
                sub_name = subreddit_name.lstrip("r/")
                try:
                    subreddit = reddit.subreddit(sub_name)

                    if external_url:
                        # Link post
                        submission = subreddit.submit(
                            title=title[:300],
                            url=external_url,
                        )
                    else:
                        # Self/text post — truncate to Reddit's 40k char limit
                        submission = subreddit.submit(
                            title=title[:300],
                            selftext=self._clean_for_reddit(body)[:39000],
                        )

                    posted_urls.append(submission.url)

                except Exception as sub_exc:
                    # Don't fail entire run if one subreddit rejects (e.g., flair required)
                    posted_urls.append(f"Error on r/{sub_name}: {str(sub_exc)[:100]}")

            success = any("http" in u for u in posted_urls)
            return {
                "success": success,
                "platform": self.platform,
                "urls": posted_urls,
                "url": next((u for u in posted_urls if "http" in u), ""),
            }

        except Exception as exc:
            return {"success": False, "platform": self.platform, "error": str(exc)}

    def _clean_for_reddit(self, text: str) -> str:
        """Reddit supports markdown natively — minimal cleanup needed."""
        import re
        # Remove HTML tags if any
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()
