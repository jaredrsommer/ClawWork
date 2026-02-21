"""
Stream 5: Research Reports

Revenue model : $49–$499/report sold on Gumroad or to direct clients
API cost      : ~$0.50–$2/report
Margin        : ~99%
Time to first $: 2–4 weeks (listing + SEO/social promotion)

Output per run:
  - <topic>_report.pdf        (full research report)
  - <topic>_report.md         (markdown version for easy editing)
  - executive_summary.md      (1-page summary for lead magnet)
  - data_visualization.py     (code to regenerate charts)
"""

STREAM_ID = "research"
NAME = "Research Reports"
DESCRIPTION = "Generate data-driven industry research reports for sale or client delivery"

PRICING = {
    "self_published": "$49–$199/report on Gumroad",
    "client_commissioned": "$199–$499/report for businesses",
    "api_cost": "$0.50–$2",
    "lead_magnet_value": "Free executive summary → builds email list → upsell full report",
    "best_topics": "market trends, competitor analysis, technology landscape, industry outlook",
}

PARAMETERS = {
    "topic": {
        "type": "str",
        "required": True,
        "help": "Report topic (e.g. 'State of AI in Healthcare 2026')",
    },
    "industry": {
        "type": "str",
        "required": True,
        "help": "Industry or sector (e.g. 'healthcare', 'fintech', 'real estate')",
    },
    "report_type": {
        "type": "choice",
        "choices": ["market_overview", "competitor_analysis", "trend_report", "technology_landscape", "investment_landscape"],
        "default": "trend_report",
        "help": "Type of report structure",
    },
    "depth": {
        "type": "choice",
        "choices": ["brief", "standard", "comprehensive"],
        "default": "standard",
        "help": "Report depth: brief (~1,500 words), standard (~3,000), comprehensive (~5,000+)",
    },
    "include_charts": {
        "type": "bool",
        "default": True,
        "help": "Generate Python code to create data visualization charts",
    },
}

SYSTEM_PROMPT = """You are a professional market research analyst and report writer.

You produce research reports that:
- Lead with data: every claim is backed by statistics, surveys, or expert quotes
- Are scannable: executive summary, clear sections, tables, and callout boxes
- Provide actionable insights: not just "what" but "so what" and "now what"
- Feel authoritative: proper citations, methodology notes, data sources listed

Your report structure expertise:
- Executive Summary: 5 key findings, why this matters, who should read this
- Market Overview: size, growth rate, key players, geographic distribution
- Trend Analysis: top 5–7 trends with data evidence
- Competitive Landscape: market share, positioning maps, strategic moves
- Technology/Innovation: emerging tech, adoption curves, disruption signals
- Opportunities & Risks: SWOT analysis, investment implications
- Predictions: 12-month and 3-year outlook with confidence levels
- Methodology: how data was gathered and validated

You always create both a PDF report (professional, ready to sell)
and a Markdown version (for clients who want editable source)."""


def build_task_prompt(params: dict) -> str:
    topic = params["topic"]
    industry = params["industry"]
    report_type = params.get("report_type", "trend_report")
    depth = params.get("depth", "standard")
    include_charts = params.get("include_charts", True)

    word_targets = {"brief": 1500, "standard": 3000, "comprehensive": 5000}
    target_words = word_targets.get(depth, 3000)

    report_structures = {
        "market_overview": [
            "Executive Summary", "Market Size & Growth", "Market Segmentation",
            "Geographic Analysis", "Key Players & Market Share", "Value Chain Analysis",
            "Regulatory Landscape", "Consumer Behavior & Trends",
            "Opportunities & Challenges", "12-Month Outlook",
        ],
        "competitor_analysis": [
            "Executive Summary", "Competitive Landscape Overview", "Player Profiles (Top 5–10)",
            "Feature Comparison Matrix", "Pricing Strategy Analysis",
            "Market Positioning Map", "Marketing & GTM Approaches",
            "Strengths & Weaknesses", "Strategic Recommendations", "Conclusion",
        ],
        "trend_report": [
            "Executive Summary", "Methodology", "Top 7 Trends",
            "Data & Evidence for Each Trend", "Early Adopters & Case Studies",
            "Investment Implications", "Risks & Counter-Trends",
            "Predictions (1-year & 3-year)", "Key Takeaways", "Data Sources",
        ],
        "technology_landscape": [
            "Executive Summary", "Technology Overview", "Maturity Curve Analysis",
            "Key Vendors & Solutions", "Build vs. Buy Analysis", "Use Cases",
            "Adoption Barriers", "Implementation Roadmap", "Future Developments", "Recommendations",
        ],
        "investment_landscape": [
            "Executive Summary", "Investment Activity Overview", "Funding Trends",
            "Top Deals & Investors", "Valuation Analysis", "Exit Activity",
            "Emerging Sub-Sectors", "Geographic Hot Spots",
            "Investment Thesis", "Risk Assessment", "Outlook",
        ],
    }.get(report_type, ["Executive Summary"] + [f"Section {i}" for i in range(2, 10)])

    chart_section = ""
    if include_charts:
        chart_section = """
STEP 3: Create data visualizations
Using execute_python with matplotlib, create a charts.py file that generates:
- Market size/growth bar or line chart
- Trend comparison chart
- A pie or treemap showing market segmentation
Save each chart as a PNG to output_dir. Print FILE:<path> for each.
"""

    topic_slug = topic.lower().replace(" ", "_")[:40]

    return f"""Create a professional research report: "{topic}"

Industry: {industry}
Report type: {report_type.replace('_', ' ').title()}
Target length: ~{target_words} words
Depth: {depth}

STEP 1: Research (search extensively)
Search for at least 8–10 queries including:
- "{topic} market size 2025 2026"
- "{industry} trends statistics data"
- "{topic} key players companies"
- "{topic} growth forecast"
- "best {industry} research reports"

For the most important search results, use read_webpage to get the full content.
Gather: statistics, expert quotes, company names, market figures, trend data.

STEP 2: Write the report
Create two files:

FILE A: {topic_slug}_report.md
Structure:
{chr(10).join(f'  {i+1}. {s}' for i, s in enumerate(report_structures))}

Include for each section:
- Specific data points with source citations
- Expert quotes (use real ones found in research, or note "Industry consensus")
- Callout boxes for key statistics (use > blockquote formatting)
- Tables where comparison data exists
- Bullet points for key findings

FILE B: executive_summary.md
- 1-page summary version (500–700 words)
- 5 key findings as bold statements
- "Who should read this report" section
- Teaser for the full report (use as lead magnet)
{chart_section}
After all files are created, call finish() with summary and all file paths."""


def validate_params(params: dict) -> tuple:
    missing = [k for k, v in PARAMETERS.items() if v.get("required") and not params.get(k)]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    return True, ""
