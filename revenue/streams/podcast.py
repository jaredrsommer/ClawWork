"""
Stream 6: Podcast Production Service

Revenue model : $25–$75/episode, $400–$1,200/month per client (4 eps/week)
API cost      : ~$0.20–$0.50/episode
Margin        : ~99%
Time to first $: 2–4 weeks (podcast Facebook groups, Upwork, direct outreach)

What gets produced per run (from a transcript or topic):
  - show_notes.md          (formatted episode show notes)
  - episode_description.md (SEO podcast description)
  - social_posts.md        (5 platform-specific posts)
  - blog_post.md           (long-form blog version of episode)
  - timestamps.md          (chapter markers for YouTube/Spotify)
"""

STREAM_ID = "podcast"
NAME = "Podcast Production Service"
DESCRIPTION = "Transform podcast episodes into show notes, blog posts, and social content"

PRICING = {
    "per_episode_basic": "$25–$40 (show notes + description)",
    "per_episode_full": "$50–$75 (full package: show notes + blog + social + timestamps)",
    "monthly_retainer": "$400–$1,200/month (4 eps/week × $25–$75)",
    "api_cost": "$0.20–$0.50/episode",
    "upsell": "Add video editing notes, email newsletter version, YouTube script",
}

PARAMETERS = {
    "transcript": {
        "type": "str",
        "default": "",
        "help": "Episode transcript (paste the text, or leave empty and use topic+guest)",
    },
    "topic": {
        "type": "str",
        "required": True,
        "help": "Episode topic or title (e.g. 'How to build a 7-figure agency with John Smith')",
    },
    "guest": {
        "type": "str",
        "default": "",
        "help": "Guest name and title (optional)",
    },
    "podcast_name": {
        "type": "str",
        "default": "The Podcast",
        "help": "Name of the podcast",
    },
    "episode_number": {
        "type": "int",
        "default": 1,
        "help": "Episode number",
    },
    "niche": {
        "type": "str",
        "default": "",
        "help": "Podcast niche (e.g. 'entrepreneurship', 'health', 'tech') — improves SEO targeting",
    },
    "package": {
        "type": "choice",
        "choices": ["basic", "standard", "full"],
        "default": "full",
        "help": "basic=show notes only, standard=+description+social, full=everything",
    },
}

SYSTEM_PROMPT = """You are an expert podcast producer and content repurposing specialist.

You transform podcast episodes into maximum-value content packages.

Your expertise:
- Show Notes: Clear structure with timestamps, key insights, resources mentioned, guest bio
- Episode Descriptions: SEO-optimized for Spotify/Apple Podcasts, hooks listener in first line
- Social Media Posts: Platform-specific (LinkedIn long-form, Twitter thread, Instagram caption, TikTok hook)
- Blog Posts: Full repurposing with added context, formatted for web readers
- Timestamps/Chapters: Chapter markers that improve listen-through rate

SEO for podcasts:
- Episode titles follow: [Hook/Benefit] with/feat. [Guest Name] | Podcast Name Ep. XXX
- Descriptions: 150–300 words, primary keyword in first sentence, end with CTA
- Show notes: keyword-rich headers, internal links to previous episodes, guest's social links
- Blog posts: 800–1500 words, unique angle (not just transcript), includes meta description

Social media by platform:
- LinkedIn: 200–300 words, professional takeaway, quote from guest
- Twitter: 6-tweet thread, each tweet self-contained
- Instagram: caption with hook + 3 takeaways + CTA (under 125 words before "more")
- Facebook: conversational, question-based, encourages comments"""


def build_task_prompt(params: dict) -> str:
    topic = params["topic"]
    guest = params.get("guest", "")
    podcast_name = params.get("podcast_name", "The Podcast")
    ep_num = params.get("episode_number", 1)
    niche = params.get("niche", "general")
    transcript = params.get("transcript", "")
    package = params.get("package", "full")

    guest_section = f"Guest: {guest}" if guest else "Solo episode (no guest)"

    if transcript:
        content_source = f"""SOURCE: Episode Transcript (use this as the primary content source)
---
{transcript[:6000]}
---
Extract: key insights, memorable quotes, timestamps of topic changes, resources mentioned."""
    else:
        content_source = f"""SOURCE: No transcript provided. Research the topic and create content based on:
- Search the web for information about: {topic}
- Find expert quotes, statistics, and examples related to the topic
- Create realistic and informative content as if summarizing a great conversation about this"""

    slug = topic.lower().replace(" ", "_")[:30]

    basic_files = f"""
Create show_notes_{slug}.md:
- Episode title (SEO-optimized)
- Episode summary (100–150 words)
- Guest bio (if applicable): {guest}
- What you'll learn (5–7 bullet points)
- Key topics discussed (with approximate timestamps if transcript provided)
- 3–5 key quotes (exact quotes from transcript, or representative quotes if no transcript)
- Resources mentioned (books, tools, websites)
- Connect with guest (social links, website)
- Subscribe/review CTA"""

    standard_extra = f"""
Create episode_description_{slug}.md:
- Optimized title tag (under 65 chars)
- Podcast description for Spotify/Apple (150–300 words)
- Short description for directories (50–75 words)
- Keywords list (8–10 relevant search terms)

Create social_posts_{slug}.md:
- LinkedIn post (200–300 words, professional angle)
- Twitter/X thread (6 tweets)
- Instagram caption (under 125 words + hashtag set of 20)
- Email newsletter blurb (75–100 words)"""

    full_extra = f"""
Create blog_post_{slug}.md:
- Full blog article (800–1,200 words) based on episode content
- Original angle — not just a transcript dump
- SEO title, meta description, internal link suggestions
- Pull quotes formatted as blockquotes
- CTA to listen to episode at the end

Create timestamps_{slug}.md:
- YouTube chapter markers (MM:SS format)
- Spotify chapters (if different)
- Key moments list for show notes"""

    content_to_create = basic_files
    if package in ("standard", "full"):
        content_to_create += standard_extra
    if package == "full":
        content_to_create += full_extra

    return f"""Produce a complete podcast content package for episode #{ep_num}.

Podcast: {podcast_name}
Episode topic: {topic}
{guest_section}
Niche: {niche}
Package: {package}

{content_source}

FILES TO CREATE:
{content_to_create}

After all files are created, call finish() with summary and all file paths."""


def validate_params(params: dict) -> tuple:
    if not params.get("topic"):
        return False, "topic is required"
    return True, ""
