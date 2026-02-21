"""
Base Publisher — shared logic for all platform publishers.
"""

import os
import re
from typing import Any, Dict, List, Optional


class BasePublisher:
    """
    Abstract base for all platform publishers.

    Subclasses must implement:
      - platform: str
      - can_publish() -> bool
      - required_env_vars() -> List[str]
      - publish(session_result, stream_id, settings) -> dict
    """

    platform: str = "base"

    def can_publish(self) -> bool:
        """Return True if all required credentials are set."""
        return all(os.getenv(v) for v in self.required_env_vars())

    def required_env_vars(self) -> List[str]:
        """List of env var names needed by this publisher."""
        return []

    def publish(
        self,
        session_result: Dict[str, Any],
        stream_id: str,
        settings: Dict = None,
    ) -> Dict:
        """
        Publish content from a completed stream session.

        Args:
            session_result: The dict returned by RevenueEngine.run()
            stream_id:      Which stream produced this content
            settings:       Platform-specific settings from scheduler_config.json

        Returns:
            {
              "success": bool,
              "platform": str,
              "url": str,            # Public URL if available
              "ids": list,           # Platform-specific IDs
              "error": str,          # Error message if failed
            }
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Shared content extraction helpers
    # ------------------------------------------------------------------

    def _read_file(self, path: str) -> str:
        """Read a text/markdown file."""
        with open(path, encoding="utf-8") as f:
            return f.read()

    def _find_files(self, files: List[str], *patterns: str) -> List[str]:
        """Find files whose basename contains any of the given patterns."""
        matched = []
        for fpath in files:
            name = os.path.basename(fpath).lower()
            if any(p.lower() in name for p in patterns):
                matched.append(fpath)
        return matched

    def _find_file(self, files: List[str], *patterns: str) -> Optional[str]:
        """Find the first file matching any pattern."""
        results = self._find_files(files, *patterns)
        return results[0] if results else None

    def extract_content(self, session_result: Dict, stream_id: str) -> Dict:
        """
        Extract publishable content from a session result.

        Returns a normalized dict:
          title      str   — headline / post title
          body       str   — full content
          excerpt    str   — short summary (first 500 chars of body)
          posts      list  — individual posts (ghostwriting, newsletter sections)
          tags       list  — hashtags / tags
          files      list  — original file paths
        """
        files = session_result.get("created_files", [])
        content = {
            "title": "",
            "body": "",
            "excerpt": "",
            "posts": [],
            "tags": [],
            "files": files,
        }

        for fpath in files:
            if not fpath.endswith((".md", ".txt", ".csv")):
                continue
            try:
                text = self._read_file(fpath)
            except OSError:
                continue

            name = os.path.basename(fpath).lower()

            if "posts_" in name:
                # Ghostwriting: individual posts separated by "---" or "Post #"
                content["posts"] = self._parse_posts(text)
                if not content["body"]:
                    content["body"] = text

            elif "newsletter_issue" in name:
                content["body"] = text
                content["title"] = self._extract_title(text)

            elif "article_" in name:
                content["body"] = text
                content["title"] = self._extract_title(text)

            elif "executive_summary" in name:
                content["excerpt"] = text[:800]

            elif "social_posts" in name or "social_promo" in name:
                content["posts"] = self._parse_posts(text)

            elif "subject_lines" in name:
                # Take first subject line as title
                for line in text.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        content["title"] = line
                        break

            elif "report" in name and not content["body"]:
                content["body"] = text
                content["title"] = self._extract_title(text)

        # Fallbacks
        if not content["title"] and content["body"]:
            content["title"] = self._extract_title(content["body"])
        if not content["excerpt"] and content["body"]:
            content["excerpt"] = content["body"][:600]
        if not content["posts"] and content["body"]:
            content["posts"] = [content["excerpt"]]

        # Extract hashtags from body
        content["tags"] = re.findall(r"#(\w+)", content["body"])[:10]

        return content

    def _extract_title(self, text: str) -> str:
        """Extract the first H1 or H2 heading from markdown text."""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line.startswith("## "):
                return line[3:].strip()
            if line and not line.startswith("#") and len(line) < 120:
                return line
        return "Untitled"

    def _parse_posts(self, text: str) -> List[str]:
        """Split a multi-post document into individual posts."""
        posts = []

        # Try "Post #N" separator
        if re.search(r"Post #\d+", text, re.IGNORECASE):
            parts = re.split(r"(?=Post #\d+)", text, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                if len(part) > 50:
                    posts.append(part)
            return posts

        # Try "---" separator
        if "\n---\n" in text:
            for part in text.split("\n---\n"):
                part = part.strip()
                if len(part) > 50:
                    posts.append(part)
            return posts

        # Try double newlines (paragraphs)
        for part in re.split(r"\n\n{2,}", text):
            part = part.strip()
            if len(part) > 80:
                posts.append(part)

        return posts or [text[:2000]]

    def _split_to_thread(self, text: str, max_len: int = 280) -> List[str]:
        """Split long text into tweet-sized chunks."""
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text) <= max_len:
            return [text]

        tweets = []
        # Split on double newlines first
        paragraphs = text.split("\n\n")
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) + 2 <= max_len:
                current = (current + "\n\n" + para).strip()
            else:
                if current:
                    tweets.append(current)
                # Para itself may be too long — split by sentence
                if len(para) > max_len:
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    current = ""
                    for s in sentences:
                        if len(current) + len(s) + 1 <= max_len:
                            current = (current + " " + s).strip()
                        else:
                            if current:
                                tweets.append(current)
                            current = s[:max_len]
                else:
                    current = para

        if current:
            tweets.append(current)

        return tweets[:25]  # cap at 25 tweets per thread

    def _markdown_to_html(self, md: str) -> str:
        """Basic markdown → HTML conversion."""
        try:
            import markdown
            return markdown.markdown(md, extensions=["extra", "nl2br"])
        except ImportError:
            # Manual fallback
            html = md
            html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
            html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
            html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
            html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
            html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
            html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
            html = html.replace("\n\n", "</p><p>")
            return f"<p>{html}</p>"
