"""
Stream 10: SaaS API / White-Label Agent Service

Revenue model : $99–$999/month SaaS subscriptions
               Clients POST tasks → receive deliverable files back
API cost      : ~$0.50–$3/task (passed to customer)
Margin        : 60–90% (after compute and API costs)
Time to first $: 1–3 months (requires product work)
Highest ceiling: Uncapped — recurring B2B revenue

The SaaS API server is at: python revenue/run.py api

This stream module helps you:
  - Generate the API documentation (OpenAPI / Markdown)
  - Generate a pricing page copy
  - Generate a landing page copy
  - Generate a sales email sequence for outreach

Run this stream to produce the marketing/sales assets for selling the API.
"""

STREAM_ID = "saas_api"
NAME = "SaaS API Documentation & Marketing"
DESCRIPTION = "Generate API docs, pricing page, and sales copy for the Revenue API"

PRICING = {
    "tier_starter": "$99/month — 50 tasks/month",
    "tier_growth": "$299/month — 200 tasks/month",
    "tier_pro": "$799/month — 1,000 tasks/month",
    "tier_enterprise": "$1,999+/month — unlimited + SLA",
    "api_cost_per_task": "$0.50–$3 (variable)",
    "break_even_at": "2 Growth customers covers your own API costs",
}

PARAMETERS = {
    "asset_type": {
        "type": "choice",
        "choices": ["api_docs", "landing_page", "pricing_page", "email_sequence", "full_kit"],
        "default": "full_kit",
        "help": "Which marketing asset to generate",
    },
    "product_name": {
        "type": "str",
        "default": "ContentAPI",
        "help": "Name of your SaaS product",
    },
    "target_customer": {
        "type": "str",
        "default": "marketing agencies and content teams",
        "help": "Who buys this (e.g. 'marketing agencies', 'solo consultants', 'SaaS companies')",
    },
    "api_base_url": {
        "type": "str",
        "default": "https://api.yourdomain.com/v1",
        "help": "Your API's base URL",
    },
}

SYSTEM_PROMPT = """You are a SaaS product marketer and technical writer.

You create materials that:
- Make APIs feel accessible, not scary
- Lead with benefits, not features ("Get a 2,000-word SEO article in 30 seconds" not "POST /generate")
- Make pricing feel like a no-brainer ROI, not a cost
- Use social proof, specific examples, and demos

API Documentation style:
- Clear endpoint description + what it does in plain English
- Request/response examples in multiple languages (Python, JavaScript, cURL)
- Error codes and what to do about them
- Rate limits and authentication guide
- Quick-start guide (get a result in 5 minutes)

Landing page principles:
- Headline: your #1 benefit in under 8 words
- Subhead: who it's for and the mechanism
- Social proof: specific numbers ("1,200 agencies use ContentAPI")
- Features: translate to outcomes ("Automatic SEO optimization" → "Rank without an SEO team")
- FAQ: kill the top 5 objections
- CTA: low-friction ("Start free trial" not "Contact sales")

Email sequences:
- Day 0: Welcome, one quick win
- Day 2: The problem you solve better than anyone
- Day 4: Social proof + case study
- Day 7: Product education — the aha moment
- Day 14: Direct ask / upgrade"""


def build_task_prompt(params: dict) -> str:
    asset_type = params.get("asset_type", "full_kit")
    product_name = params.get("product_name", "ContentAPI")
    target = params.get("target_customer", "marketing agencies and content teams")
    api_base = params.get("api_base_url", "https://api.yourdomain.com/v1")

    assets_to_create = []

    if asset_type in ("api_docs", "full_kit"):
        assets_to_create.append(f"""
CREATE api_documentation.md:
- Overview: what the API does and who it's for
- Authentication: Bearer token, example in Python/JS/cURL
- Base URL: {api_base}
- Endpoints (for each of the 10 revenue streams):
  POST /v1/ghostwriting
  POST /v1/products
  POST /v1/seo-content
  POST /v1/slide-decks
  POST /v1/research
  POST /v1/podcast
  POST /v1/publishing
  POST /v1/data-analysis
  POST /v1/newsletter
  GET  /v1/sessions/{{session_id}}
  GET  /v1/sessions/{{session_id}}/files/{{filename}}
- For each endpoint: description, request params (JSON schema), response format, example
- Error codes and retry guidance
- Quick-start guide: "Get your first article in 5 minutes"
- SDK code samples in Python, JavaScript, and cURL""")

    if asset_type in ("landing_page", "full_kit"):
        assets_to_create.append(f"""
CREATE landing_page.md:
- Hero section: H1 headline + subhead + primary CTA
- Social proof bar: logos or "[X] teams use {product_name}"
- Problem section: "The old way" vs "The {product_name} way"
- Features section: 6 key capabilities with icons and outcome-focused descriptions
- How it works: 3-step visual (1. Send task → 2. API processes → 3. Get deliverable)
- Use cases section: 4-5 specific use cases with outcomes
- Pricing overview (link to pricing page)
- FAQ: 8 common objections answered
- Final CTA: low-friction offer
- Footer: links, legal""")

    if asset_type in ("pricing_page", "full_kit"):
        assets_to_create.append(f"""
CREATE pricing_page.md:
- 4 tiers with names, prices, limits, and features:
  Starter: $99/month — 50 tasks
  Growth: $299/month — 200 tasks
  Pro: $799/month — 1,000 tasks
  Enterprise: Custom pricing
- For each tier: feature comparison table
- "Most popular" badge on Growth
- Annual pricing (20% discount)
- "What counts as a task?" explanation
- Money-back guarantee copy
- FAQ: 5 pricing-specific questions
- Enterprise CTA section""")

    if asset_type in ("email_sequence", "full_kit"):
        assets_to_create.append(f"""
CREATE email_sequence.md:
Write a 7-email welcome/nurture sequence for new {product_name} trial users:
- Email 1 (Day 0): Welcome + quick win guide
- Email 2 (Day 1): "Here's what others are doing with {product_name}"
- Email 3 (Day 3): Feature spotlight — most valuable capability
- Email 4 (Day 5): Case study — specific ROI story
- Email 5 (Day 7): Educational — how to get the best results
- Email 6 (Day 10): Soft pitch — upgrade before trial ends
- Email 7 (Day 14): Last chance + success story
For each: subject line, preview text, full email body""")

    assets_text = "\n".join(assets_to_create)

    return f"""Create marketing and sales assets for {product_name} — an AI content API for {target}.

Product: {product_name}
Target customer: {target}
Asset type: {asset_type.replace('_', ' ').title()}

The {product_name} API allows {target} to generate:
- LinkedIn/Twitter ghostwriting (10 posts + calendar)
- Digital products (Excel, PowerPoint, PDF templates)
- SEO articles (1,500–3,000 words, ready to publish)
- PowerPoint presentations (10–20 slides)
- Research reports (3,000–5,000 words with data)
- Podcast show notes + blog post + social posts
- Book manuscripts (for KDP publishing)
- Data analysis reports (dashboard + PDF)
- Newsletter issues (fully written, send-ready)

Pricing model (reference this in all assets):
- Starter: $99/month (50 tasks)
- Growth: $299/month (200 tasks)
- Pro: $799/month (1,000 tasks)
- Enterprise: Custom

RESEARCH:
Search for "{product_name} competitor" and similar "AI content API" services.
Understand what differentiates us: fully managed, no prompt engineering needed,
file deliverables (not just text), all 10 content types in one API.

CREATE THESE ASSETS:
{assets_text}

After all files created, call finish() with summary and file paths."""


def validate_params(params: dict) -> tuple:
    return True, ""
