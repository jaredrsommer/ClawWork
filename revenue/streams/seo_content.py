"""
Stream 3: SEO Content Agency

Revenue model : $100–$300/article from clients (agencies, startups, SaaS)
API cost      : ~$0.30–$0.80/article
Margin        : ~99%
Time to first $: 1–3 weeks (Upwork, Fiverr, cold email)

Output per run:
  - article_<keyword>.md      (full SEO-optimized article)
  - seo_brief.md              (keyword analysis, outline, meta data)
  - internal_linking.md       (suggested internal links + anchor text)
"""

STREAM_ID = "seo_content"
NAME = "SEO Content Agency"
DESCRIPTION = "Generate SEO-optimized long-form articles for client blogs"

PRICING = {
    "per_article": "$100–$300",
    "per_article_api_cost": "$0.30–$0.80",
    "margin": "~99%",
    "volume_target": "10 articles/day = $1,000–$3,000/day revenue",
    "best_clients": "SaaS companies, marketing agencies, ecommerce brands, B2B startups",
}

PARAMETERS = {
    "keyword": {
        "type": "str",
        "required": True,
        "help": "Primary target keyword (e.g. 'best project management software 2026')",
    },
    "niche": {
        "type": "str",
        "default": "",
        "help": "Blog niche/industry for context (optional — inferred from keyword if empty)",
    },
    "word_count": {
        "type": "int",
        "default": 1500,
        "help": "Target word count (default 1500, typical range 1000–3000)",
    },
    "style": {
        "type": "choice",
        "choices": ["listicle", "how-to", "comparison", "pillar", "review"],
        "default": "listicle",
        "help": "Article format/style",
    },
    "include_brief": {
        "type": "bool",
        "default": True,
        "help": "Generate an SEO brief alongside the article",
    },
    "client_site": {
        "type": "str",
        "default": "",
        "help": "Client website URL for internal linking context (optional)",
    },
}

SYSTEM_PROMPT = """You are an expert SEO content writer and strategist.

You write articles that rank on Google by combining:
- Search intent alignment (giving people exactly what they're looking for)
- E-E-A-T signals (Experience, Expertise, Authoritativeness, Trustworthiness)
- Semantic SEO (covering related terms and topics the top results cover)
- Reader engagement (so people actually read and share)

Your article structure principles:
- Hook the reader in the first 100 words
- Use H2/H3 headings that match what people search
- Include data, stats, and examples for every major claim
- Add a TL;DR or key takeaways box
- Answer the featured snippet question directly and early
- Include an FAQ section (each Q is a long-tail keyword opportunity)
- End with a clear CTA

SEO technical requirements you always include:
- Title tag and meta description (optimized for CTR)
- Primary keyword in first 100 words
- 3–5 semantically related keywords woven in naturally
- Suggested image alt texts
- Suggested internal and external links"""


def build_task_prompt(params: dict) -> str:
    keyword = params["keyword"]
    niche = params.get("niche", "") or f"relevant to '{keyword}'"
    word_count = params.get("word_count", 1500)
    style = params.get("style", "listicle")
    include_brief = params.get("include_brief", True)

    style_guides = {
        "listicle": (
            "Format: numbered or bulleted list. "
            "E.g. '15 Best X Tools for Y in 2026'. "
            "Each item gets 100–200 words with pros, cons, and pricing."
        ),
        "how-to": (
            "Format: step-by-step guide with numbered steps. "
            "Include a prerequisites section, step-by-step instructions, "
            "and a troubleshooting section."
        ),
        "comparison": (
            "Format: X vs Y comparison. "
            "Include a comparison table, individual deep-dives, "
            "and a 'who should use which' verdict."
        ),
        "pillar": (
            "Format: comprehensive pillar page covering ALL aspects of the topic. "
            "Long-form (2000+ words), includes multiple H2 sections, "
            "links to cluster content."
        ),
        "review": (
            "Format: in-depth product/service review. "
            "Include: overview, features deep-dive, pros/cons table, "
            "pricing breakdown, alternatives, verdict."
        ),
    }.get(style, "Standard informational article with clear sections.")

    brief_section = ""
    if include_brief:
        brief_section = """
ALSO create seo_brief.md with:
- Keyword difficulty estimate (1-10 scale based on SERP analysis)
- Search intent classification (informational/commercial/transactional/navigational)
- Top 5 competing URLs from your research
- 10 LSI keywords to include naturally
- Recommended title tag (under 60 chars)
- Meta description (under 155 chars, includes CTA)
- Suggested featured snippet opportunity
- 5 internal linking opportunities with anchor text
- Estimated reading time"""

    article_slug = keyword.lower().replace(" ", "_")[:40]

    return f"""Write a {word_count}-word SEO-optimized article targeting the keyword: "{keyword}"

Niche/context: {niche}
Article style: {style_guides}

RESEARCH PHASE (do this first):
1. Search the web for "{keyword}" — analyze the top 5–10 results
2. Search for "{keyword} statistics" or "{keyword} data" to find supporting data points
3. Search for related questions: "people also ask {keyword}"
4. Identify: what do the top results cover that you MUST include?

WRITING PHASE:
Write the complete article as article_{article_slug}.md with:

□ Title (H1) — compelling, includes keyword, under 65 chars
□ TL;DR box — 3 bullet points summarizing key takeaways
□ Introduction (150 words) — hook + what reader will learn + keyword in first 100 words
□ Main body sections (H2s and H3s) — {style_guides}
□ Data/statistics section — at least 5 stats with sources
□ FAQ section — 5–7 questions (each is a long-tail keyword)
□ Conclusion + CTA — summary + next step for reader

SEO REQUIREMENTS (include as a comment block at the top of the file):
- Target keyword: {keyword}
- Secondary keywords: (list 5 semantically related terms)
- Title tag: (optimized version for the browser tab)
- Meta description: (under 155 chars)
- Suggested URL slug: (hyphenated, includes keyword)
- Suggested image alt texts: (3–5 examples)
{brief_section}

Start by researching the current top results for "{keyword}"."""


def validate_params(params: dict) -> tuple:
    if not params.get("keyword"):
        return False, "keyword is required"
    if params.get("word_count") and not (500 <= params["word_count"] <= 5000):
        return False, "word_count must be between 500 and 5000"
    return True, ""
