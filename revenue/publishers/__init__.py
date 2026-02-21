"""
Revenue Publishers — Cross-Platform Content Distribution

Supported platforms:
  twitter    Twitter/X threads and tweets           (tweepy)
  linkedin   LinkedIn posts and articles            (requests + LinkedIn API v2)
  medium     Medium stories and drafts             (requests + Medium API)
  wordpress  WordPress posts via REST API           (requests)
  beehiiv    Beehiiv newsletter posts              (requests + Beehiiv API)
  buffer     Buffer post scheduling (multi-platform)(requests + Buffer API)
  reddit     Reddit posts to subreddits            (praw)

Credentials (add to .env):
  TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
  LINKEDIN_ACCESS_TOKEN
  MEDIUM_ACCESS_TOKEN
  WORDPRESS_URL, WORDPRESS_USER, WORDPRESS_APP_PASSWORD
  BEEHIIV_API_KEY, BEEHIIV_PUBLICATION_ID
  BUFFER_ACCESS_TOKEN
  REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
"""

from .twitter import TwitterPublisher
from .linkedin import LinkedInPublisher
from .medium import MediumPublisher
from .wordpress import WordPressPublisher
from .beehiiv import BeehiivPublisher
from .buffer import BufferPublisher
from .reddit import RedditPublisher

_REGISTRY = {
    "twitter": TwitterPublisher,
    "linkedin": LinkedInPublisher,
    "medium": MediumPublisher,
    "wordpress": WordPressPublisher,
    "beehiiv": BeehiivPublisher,
    "buffer": BufferPublisher,
    "reddit": RedditPublisher,
}


def get_publisher(platform: str):
    """Return an instantiated publisher for the given platform, or None."""
    cls = _REGISTRY.get(platform)
    return cls() if cls else None


def list_publishers() -> dict:
    """Return all publishers with their credential status."""
    result = {}
    for name, cls in _REGISTRY.items():
        pub = cls()
        result[name] = {
            "platform": name,
            "configured": pub.can_publish(),
            "required_env": pub.required_env_vars(),
        }
    return result
