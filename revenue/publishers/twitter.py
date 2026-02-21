"""
Twitter/X Publisher

Posts tweets and threads via the Twitter API v2 (tweepy).

Required env vars:
  TWITTER_API_KEY
  TWITTER_API_SECRET
  TWITTER_ACCESS_TOKEN
  TWITTER_ACCESS_SECRET

Setup:
  1. Create a Twitter Developer app at https://developer.twitter.com
  2. Set OAuth 1.0a User Context with Read+Write permissions
  3. Add credentials to .env

Content handling by stream:
  ghostwriting  → posts each LinkedIn post as a tweet thread
  newsletter    → posts the "Insight of the Week" + link
  seo_content   → posts a teaser thread
  research      → posts top 3 findings as a thread
  podcast       → posts the Twitter thread from social_posts file
  data_analysis → posts key finding + stat
"""

import os
from typing import Any, Dict, List

from .base import BasePublisher


class TwitterPublisher(BasePublisher):
    platform = "twitter"

    def required_env_vars(self) -> List[str]:
        return [
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_SECRET",
        ]

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        settings = settings or {}
        try:
            import tweepy
        except ImportError:
            return {"success": False, "platform": self.platform, "error": "tweepy not installed — run: pip install tweepy"}

        try:
            client = tweepy.Client(
                consumer_key=os.getenv("TWITTER_API_KEY"),
                consumer_secret=os.getenv("TWITTER_API_SECRET"),
                access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
                access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
                wait_on_rate_limit=True,
            )

            content = self.extract_content(session_result, stream_id)
            max_len = settings.get("max_tweet_length", 280)
            thread_if_long = settings.get("thread_if_long", True)

            # Pick what to tweet based on stream
            posts_to_tweet = self._select_posts(content, stream_id, settings)

            posted_urls = []
            posted_ids = []

            for post_text in posts_to_tweet[:3]:  # max 3 posts per run
                # Strip markdown artifacts for Twitter
                post_text = self._clean_for_twitter(post_text)

                if thread_if_long and len(post_text) > max_len:
                    tweets = self._split_to_thread(post_text, max_len=max_len)
                else:
                    tweets = [post_text[:max_len]]

                # Post the thread
                reply_to_id = None
                for tweet_text in tweets:
                    kwargs = {"text": tweet_text}
                    if reply_to_id:
                        kwargs["in_reply_to_tweet_id"] = reply_to_id
                    resp = client.create_tweet(**kwargs)
                    reply_to_id = resp.data["id"]

                if reply_to_id:
                    posted_ids.append(str(reply_to_id))
                    # Can't get exact URL without username, but format the link
                    posted_urls.append(f"https://x.com/i/web/status/{reply_to_id}")

            return {
                "success": True,
                "platform": self.platform,
                "ids": posted_ids,
                "url": posted_urls[0] if posted_urls else "",
                "count": len(posted_ids),
            }

        except Exception as exc:
            return {"success": False, "platform": self.platform, "error": str(exc)}

    def _select_posts(self, content: Dict, stream_id: str, settings: Dict) -> List[str]:
        """Pick the right content to tweet for each stream type."""
        # Social posts file takes priority (newsletter, podcast)
        if stream_id in ("newsletter", "podcast") and content.get("posts"):
            # Look for Twitter-specific section
            for post in content["posts"]:
                if "twitter" in post.lower() or "thread" in post.lower():
                    return [post]
            return content["posts"][:1]

        # Ghostwriting: post each individual post as a thread
        if stream_id == "ghostwriting" and content.get("posts"):
            return content["posts"][:3]

        # Research/data_analysis: post excerpt + key findings
        if stream_id in ("research", "data_analysis"):
            return [content.get("excerpt") or content.get("body", "")[:800]]

        # Default: use excerpt
        return [content.get("excerpt") or content.get("body", "")[:800]]

    def _clean_for_twitter(self, text: str) -> str:
        """Remove markdown formatting for Twitter."""
        import re
        text = re.sub(r"#{1,6}\s+", "", text)        # Remove headings
        text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)  # Remove bold/italic
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)       # Remove links (keep text)
        text = re.sub(r"^[-*]\s+", "• ", text, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
