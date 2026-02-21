"""
Stream 9: Niche Newsletter Production

Revenue model : Sponsorships ($50–$500/issue at 500–2,000 subs), premium subscriptions
               At 2,000 subs in a lucrative niche: $200–$500/issue × 4/month = $800–$2,000 MRR
API cost      : ~$0.20–$0.50/issue
Margin        : ~99%
Time to first $: 2–6 months (building audience takes time, but compounding)

Best niches: finance, AI/tech, real estate, legal, healthcare, B2B SaaS

Output per run (one newsletter issue):
  - newsletter_issue_<N>.md     (full newsletter, send-ready)
  - subject_lines.md            (5 A/B testable subject line options)
  - social_promo.md             (3 social posts promoting the issue)
"""

STREAM_ID = "newsletter"
NAME = "Niche Newsletter Production"
DESCRIPTION = "Generate a complete newsletter issue with subject lines and social promotion"

PRICING = {
    "sponsorship_at_500_subs": "$50–$150/issue",
    "sponsorship_at_2000_subs": "$200–$500/issue",
    "premium_subscription": "$9–$29/month/subscriber",
    "api_cost_per_issue": "$0.20–$0.50",
    "growth_path": "500 subs (3 months) → sponsors → 2,000 subs (6–12 months) → $800–$2,000 MRR",
}

PARAMETERS = {
    "newsletter_name": {
        "type": "str",
        "required": True,
        "help": "Name of the newsletter (e.g. 'The AI Brief', 'Real Estate Weekly')",
    },
    "niche": {
        "type": "str",
        "required": True,
        "help": "Newsletter niche (e.g. 'artificial intelligence', 'real estate investing', 'personal finance')",
    },
    "issue_number": {
        "type": "int",
        "default": 1,
        "help": "Issue number",
    },
    "frequency": {
        "type": "choice",
        "choices": ["daily", "weekly", "biweekly"],
        "default": "weekly",
        "help": "Publishing frequency (affects tone and content depth)",
    },
    "format": {
        "type": "choice",
        "choices": ["curated", "original", "hybrid"],
        "default": "hybrid",
        "help": "curated=link roundup with commentary, original=original content, hybrid=both",
    },
    "target_audience": {
        "type": "str",
        "default": "professionals",
        "help": "Who reads this newsletter (e.g. 'startup founders', 'retail investors', 'marketing managers')",
    },
    "sponsor_slot": {
        "type": "str",
        "default": "",
        "help": "Sponsor name and product to feature (optional — adds a sponsor section)",
    },
    "tone": {
        "type": "choice",
        "choices": ["professional", "casual", "analytical", "opinionated"],
        "default": "professional",
        "help": "Newsletter voice/tone",
    },
}

SYSTEM_PROMPT = """You are a newsletter editor and writer for high-quality niche publications.

You write newsletters that:
- Feel like a message from a trusted expert friend, not a corporate blast
- Lead with the most interesting/urgent news first
- Add original commentary and perspective — not just links
- Are scannable: clear sections, bold key points, short paragraphs
- Build loyalty: consistent voice, inside jokes, recurring segments

Newsletter structure best practices:
- Subject line: creates curiosity or urgency, under 50 chars, personalized feel
- Preview text: complements subject line, adds context
- Opening: hook the reader in the first 2 sentences (a surprising stat, bold claim, or story)
- Body: 3–5 sections, each self-contained
- Sponsor slot: natural integration, not disruptive
- CTA: one clear action per issue (reply, click, share, upgrade)
- Footer: minimal, required legal text

Writing style:
- Short sentences. Active voice. No jargon.
- Data and examples to back every claim
- Personal anecdotes and opinions to differentiate from generic content
- Consistent recurring segments that readers look forward to

You always research real, current news and trends before writing the issue."""


def build_task_prompt(params: dict) -> str:
    name = params["newsletter_name"]
    niche = params["niche"]
    issue_num = params.get("issue_number", 1)
    frequency = params.get("frequency", "weekly")
    fmt = params.get("format", "hybrid")
    audience = params.get("target_audience", "professionals")
    sponsor = params.get("sponsor_slot", "")
    tone = params.get("tone", "professional")

    format_guidance = {
        "curated": (
            "Format: curated link roundup. Find 5–7 of the best recent articles, tools, "
            "or news in the niche. For each: write 2–4 sentences of original commentary explaining "
            "WHY it matters to the reader. Your curation and POV is the value."
        ),
        "original": (
            "Format: original long-form content. Write one or two original pieces — "
            "a deep-dive analysis, a how-to, or an opinion piece. 400–800 words total. "
            "Back every claim with research."
        ),
        "hybrid": (
            "Format: hybrid. Include 1 original piece (250–400 words) as the main feature, "
            "then 3–5 curated links with 2–3 sentences of commentary each."
        ),
    }.get(fmt, "hybrid")

    sponsor_section = ""
    if sponsor:
        sponsor_section = f"""
SPONSOR SECTION (include naturally in the newsletter):
Sponsor: {sponsor}
Write a 3–4 sentence native sponsor slot that:
- Reads like an editorial recommendation, not an ad
- Clearly states it's sponsored ("Our sponsor this week is...")
- Explains the specific value for {audience}
- Includes a CTA"""

    slug = f"issue_{issue_num:03d}"

    return f"""Write issue #{issue_num} of {name}, a {frequency} newsletter for {audience}.

Niche: {niche}
Tone: {tone}
Format: {format_guidance}
{sponsor_section}

STEP 1: Research
Search for the most important/interesting developments in {niche} from the past week:
- "{niche} news this week"
- "{niche} latest developments"
- "top {niche} stories"
- Any surprising statistics or contrarian takes in {niche}

Find at least 5 solid news items, studies, or insights to work with.

STEP 2: Write the newsletter issue
Create newsletter_{slug}.md with this structure:

---
# {name} — Issue #{issue_num}
*[date]*

## 👋 This Week's Opening
[Hook — surprising stat, bold claim, or compelling question. 2–3 sentences max.
Make the reader feel they're about to learn something valuable.]

## 📰 [Main Feature Title]
[Primary content section — deepest coverage, original analysis, {format_guidance}]

## ⚡ Quick Hits
[3–5 shorter items with 1–3 sentences each — interesting tidbits, tools, quick wins]

{f"## 🤝 From Our Sponsor{chr(10)}[Sponsor slot content]" if sponsor else ""}

## 💡 Insight of the Week
[One powerful quote, stat, or idea — something reader will forward or screenshot]

## 🔗 Further Reading
[3–5 curated links with 1-sentence descriptions]

## 👋 Until Next {frequency.title()},
[Warm close, 1–2 sentences. Tease what's coming next issue.]

---

STEP 3: Create subject lines
Create subject_lines_{slug}.md with:
- 5 different subject line options (A/B testing candidates)
- For each: subject line + preview text + why it works
- Variety: one curiosity, one urgency, one data-driven, one story, one FOMO

STEP 4: Create social promotion posts
Create social_promo_{slug}.md with:
- LinkedIn post announcing this issue (150–200 words, key insight teaser)
- Twitter/X post (2–3 tweets as thread)
- Short caption for Instagram/Facebook
- Email to non-subscribers (referral/growth copy)

After all files created, call finish() with summary and file paths."""


def validate_params(params: dict) -> tuple:
    missing = [k for k, v in PARAMETERS.items() if v.get("required") and not params.get(k)]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    return True, ""
