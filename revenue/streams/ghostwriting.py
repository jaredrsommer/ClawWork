"""
Stream 1: LinkedIn/Twitter Ghostwriting

Revenue model : $500–$2,000/client/month retainer
API cost      : ~$5–$10/month per client
Margin        : ~98%
Time to first $: 1–2 weeks (Upwork, LinkedIn outreach)

What gets produced per run:
  - content_calendar.md      (2-week posting schedule)
  - posts_<client>.md        (all posts, copy-paste ready)
  - ghostwriting_strategy.md (tone guide, hashtags, audience)
"""

STREAM_ID = "ghostwriting"
NAME = "LinkedIn/Twitter Ghostwriting"
DESCRIPTION = "Generate a full month's social media content for a client"

PRICING = {
    "per_client_monthly": "$500–$2,000",
    "per_post": "$25–$100",
    "api_cost_per_client_month": "$5–$10",
    "margin": "~98%",
    "recommended_package": "10 posts/month @ $750/client",
}

PARAMETERS = {
    "client": {
        "type": "str",
        "required": True,
        "help": "Client or brand name (e.g. 'Sarah Johnson' or 'Acme Corp')",
    },
    "niche": {
        "type": "str",
        "required": True,
        "help": "Industry/niche (e.g. 'B2B SaaS', 'real estate', 'personal finance')",
    },
    "platform": {
        "type": "choice",
        "choices": ["linkedin", "twitter", "both"],
        "default": "linkedin",
        "help": "Target platform",
    },
    "tone": {
        "type": "choice",
        "choices": ["professional", "conversational", "thought-leader", "motivational"],
        "default": "professional",
        "help": "Writing tone and style",
    },
    "posts": {
        "type": "int",
        "default": 10,
        "help": "Number of posts to generate",
    },
    "topics": {
        "type": "str",
        "default": "",
        "help": "Comma-separated focus topics (optional — agent researches if empty)",
    },
}

SYSTEM_PROMPT = """You are an elite social media ghostwriter and content strategist.
You specialize in LinkedIn and Twitter/X content for professionals and business leaders.

Your content philosophy:
- Every post OPENS with a scroll-stopping hook (bold claim, surprising stat, or question)
- Posts are SCANNABLE: short paragraphs, strategic whitespace, bullet points
- Each post delivers exactly ONE insight or takeaway
- CTAs are natural and relationship-driven, never pushy
- LinkedIn posts: 150–300 words, 3–5 short paragraphs
- Twitter threads: 5–10 tweets, each self-contained but building a narrative

Your process:
1. Research what's trending in the client's niche RIGHT NOW
2. Identify the content mix: 40% educational, 30% opinion/story, 20% engagement-bait, 10% soft-sell
3. Write posts that would make a busy executive stop scrolling
4. Create a posting calendar that maximizes algorithmic reach

You always produce three deliverables:
  1. content_calendar.md  — 2-week schedule with post types and topics
  2. posts_CLIENT.md      — all posts, fully written and ready to publish
  3. ghostwriting_strategy.md — client voice guide, hashtag stack, best-time-to-post data

Quality standard: Every post should be something the client would be proud to put their name on."""


def build_task_prompt(params: dict) -> str:
    client = params["client"]
    niche = params["niche"]
    platform = params.get("platform", "linkedin")
    tone = params.get("tone", "professional")
    posts = params.get("posts", 10)
    topics = params.get("topics", "")

    platform_note = {
        "linkedin": "LinkedIn only. Posts: 150–300 words, professional tone, thought leadership.",
        "twitter": "Twitter/X only. Format as threads (5–8 tweets each), punchy and direct.",
        "both": "Both LinkedIn AND Twitter/X. For each topic: one LinkedIn post + one Twitter thread.",
    }.get(platform, "LinkedIn only.")

    topics_section = (
        f"\nFocus specifically on these topics: {topics}"
        if topics
        else f"\nSearch the web to find the 5 hottest topics in {niche} right now, then build content around them."
    )

    client_slug = client.lower().replace(" ", "_")

    return f"""Create a complete {posts}-post content package for {client}, a {niche} professional.

Platform: {platform_note}
Tone: {tone}
{topics_section}

STEP-BY-STEP INSTRUCTIONS:

1. Search the web: find trending topics, viral posts, and key conversations in the {niche} space
2. Read 2-3 top-performing articles or LinkedIn posts in this niche for style inspiration
3. Create a content mix: educational, story, opinion, engagement bait, soft promotion

4. Create these 3 files:

   FILE 1: content_calendar
   - 2-week posting schedule (Mon/Wed/Fri or daily, client's choice)
   - Each entry: date, post type, topic, estimated engagement potential
   - File type: md

   FILE 2: posts_{client_slug}
   - All {posts} posts, fully written
   - Each post labeled: Post #N | Type | Topic | Platform
   - Include suggested hashtags (3–5) for each post
   - Include "best time to post" note for each
   - File type: md

   FILE 3: ghostwriting_strategy
   - Client voice guide (vocabulary to use/avoid, sentence length, emoji policy)
   - Top 20 hashtags for the {niche} niche with monthly volume estimates
   - Posting frequency recommendation
   - Content pillars (4–5 recurring themes)
   - Engagement tactics (how to respond to comments, who to tag)
   - File type: md

5. Call finish() with the summary and all 3 file paths.

Start by searching for trending topics in the {niche} space."""


def validate_params(params: dict) -> tuple:
    missing = [k for k, v in PARAMETERS.items() if v.get("required") and not params.get(k)]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    return True, ""
