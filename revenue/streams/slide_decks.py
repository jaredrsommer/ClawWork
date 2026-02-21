"""
Stream 4: Slide Deck Service

Revenue model : $50–$200/deck for businesses, consultants, job seekers
API cost      : ~$0.50–$1.50/deck
Margin        : ~99%
Time to first $: 1–2 weeks (Fiverr, LinkedIn DMs, Upwork)

Output per run:
  - <name>_presentation.pptx  (full PowerPoint deck)
  - deck_notes.md             (presenter notes for every slide)
  - deck_brief.md             (structure overview and customization guide)
"""

STREAM_ID = "slide_decks"
NAME = "Slide Deck Service"
DESCRIPTION = "Generate professional PowerPoint presentations for any purpose"

PRICING = {
    "per_deck_basic": "$50–$75 (10 slides)",
    "per_deck_premium": "$100–$200 (20+ slides, custom design)",
    "api_cost": "$0.50–$1.50",
    "margin": "~99%",
    "high_value_clients": "startup pitch decks ($500–$2,000), investor decks, board presentations",
}

PARAMETERS = {
    "deck_type": {
        "type": "choice",
        "choices": [
            "pitch_deck", "sales_deck", "investor_deck", "training_deck",
            "keynote", "report_deck", "proposal_deck", "onboarding_deck",
        ],
        "required": True,
        "help": "Type of presentation",
    },
    "topic": {
        "type": "str",
        "required": True,
        "help": "Main topic or company/product being presented",
    },
    "audience": {
        "type": "str",
        "default": "business professionals",
        "help": "Who the presentation is for (e.g. 'VCs', 'sales prospects', 'new employees')",
    },
    "slides": {
        "type": "int",
        "default": 15,
        "help": "Number of slides to generate (default 15)",
    },
    "color_scheme": {
        "type": "choice",
        "choices": ["blue_professional", "dark_modern", "minimal_white", "green_growth", "purple_creative"],
        "default": "blue_professional",
        "help": "Visual theme",
    },
    "company": {
        "type": "str",
        "default": "",
        "help": "Company name (for branding, optional)",
    },
}

SYSTEM_PROMPT = """You are a professional presentation designer and business communication expert.

You create PowerPoint presentations that:
- Tell a clear story with a beginning, middle, and end
- Have strong visual hierarchy (one idea per slide)
- Use data visualizations and charts to support claims
- Keep text minimal — slides support the speaker, not replace them
- Flow naturally so the audience stays engaged

Your technical skills:
- python-pptx for building structured, formatted presentations
- Consistent color schemes, fonts, and layouts throughout
- Charts and graphs using matplotlib or pptx's built-in charts
- Tables, timelines, and process flows

Deck type expertise:
- Pitch decks: Problem → Solution → Market → Product → Business model → Traction → Team → Ask
- Sales decks: Pain → Promise → Proof → Proposal → Price → CTA
- Investor decks: Executive summary → Market opportunity → Solution → Go-to-market → Financials → Team
- Training decks: Objectives → Content modules → Activities → Assessment → Summary

Always use python-pptx via execute_python to create the actual .pptx file.
Print FILE:<path> when done."""


def build_task_prompt(params: dict) -> str:
    deck_type = params["deck_type"]
    topic = params["topic"]
    audience = params.get("audience", "business professionals")
    slides = params.get("slides", 15)
    color_scheme = params.get("color_scheme", "blue_professional")
    company = params.get("company", "")

    color_configs = {
        "blue_professional": {
            "primary": "1F4E79",
            "accent": "2E75B6",
            "bg": "FFFFFF",
            "text": "1A1A2E",
        },
        "dark_modern": {
            "primary": "1A1A2E",
            "accent": "E94560",
            "bg": "16213E",
            "text": "FFFFFF",
        },
        "minimal_white": {
            "primary": "333333",
            "accent": "FF6B6B",
            "bg": "FAFAFA",
            "text": "222222",
        },
        "green_growth": {
            "primary": "1B5E20",
            "accent": "4CAF50",
            "bg": "FFFFFF",
            "text": "212121",
        },
        "purple_creative": {
            "primary": "4A148C",
            "accent": "E040FB",
            "bg": "FFFFFF",
            "text": "1A1A1A",
        },
    }.get(color_scheme, {"primary": "1F4E79", "accent": "2E75B6", "bg": "FFFFFF", "text": "1A1A2E"})

    deck_structures = {
        "pitch_deck": ["Title/Hook", "Problem", "Solution", "How It Works", "Market Size",
                       "Business Model", "Traction/Proof", "Competition", "Go-To-Market",
                       "Team", "Financial Projections", "The Ask", "Contact/Next Steps"],
        "sales_deck": ["Title", "Agenda", "Your Pain Points", "Our Solution", "Key Features",
                       "Case Study/Proof", "ROI Calculator", "Pricing", "Implementation",
                       "Testimonials", "Why Us", "Next Steps", "Q&A"],
        "investor_deck": ["Executive Summary", "The Problem", "Our Solution", "Market Opportunity",
                          "Product Demo", "Business Model", "Go-To-Market Strategy",
                          "Competitive Landscape", "Financial Projections", "Team", "The Ask"],
        "training_deck": ["Welcome/Objectives", "Agenda", "Module 1: Foundations",
                          "Module 2: Core Concepts", "Activity/Exercise", "Module 3: Advanced",
                          "Case Studies", "Best Practices", "Common Mistakes", "Assessment",
                          "Key Takeaways", "Resources", "Q&A", "Next Steps", "Certificate"],
        "keynote": ["Opening Hook", "Speaker Introduction", "Agenda", "Section 1",
                    "Section 2", "Section 3", "Data/Research", "Case Study", "Insights",
                    "Call to Action", "Audience Q&A", "Closing/Thank You"],
        "report_deck": ["Executive Summary", "Methodology", "Key Findings",
                        "Data Analysis", "Charts/Visualizations", "Recommendations",
                        "Implementation Plan", "Timeline", "Budget/Resources", "Conclusion"],
        "proposal_deck": ["Title", "Executive Summary", "Understanding Your Needs",
                          "Our Approach", "Scope of Work", "Timeline/Milestones",
                          "Deliverables", "Team", "Investment/Pricing", "Terms", "Next Steps"],
        "onboarding_deck": ["Welcome to the Team!", "Company Overview", "Our Mission & Values",
                            "Organization Structure", "Your Role", "First 30/60/90 Days",
                            "Key Tools & Systems", "Key Contacts", "Policies & Benefits",
                            "Resources & Support", "Q&A"],
    }.get(deck_type, ["Title"] + [f"Slide {i}" for i in range(2, slides)])

    company_note = f"Company/brand: {company}" if company else ""
    slug = topic.lower().replace(" ", "_")[:30]

    return f"""Create a professional {deck_type.replace('_', ' ')} PowerPoint presentation.

Topic: {topic}
Audience: {audience}
Slides: {slides}
Color scheme: {color_scheme}
{company_note}

STEP 1: Research
Search the web for information about {topic} to find:
- Key data points, statistics, and market figures
- Real examples or case studies to include
- Industry-standard benchmarks

STEP 2: Create the presentation using execute_python

Write Python code that creates a {slides}-slide PowerPoint using python-pptx.

Suggested slide structure:
{chr(10).join(f'  {i+1}. {s}' for i, s in enumerate(deck_structures[:slides]))}

Color palette (hex, no # prefix):
  Primary:  {color_configs["primary"]}
  Accent:   {color_configs["accent"]}
  Background: {color_configs["bg"]}
  Text:     {color_configs["text"]}

Technical requirements:
- 16:9 widescreen format (Inches(13.33), Inches(7.5))
- Title slides: large title, subtitle, decorative bar using primary color
- Content slides: bold H2 title, bullet points, accent color for emphasis
- Data slides: use pptx charts (bar, line, or pie) with real data
- Include slide numbers in footer
- Save to: os.path.join(output_dir, "{slug}_presentation.pptx")
- Print: FILE:<path>

STEP 3: Create presenter notes
Create deck_notes_{slug}.md with bullet-point speaker notes for each slide (50–100 words/slide).

STEP 4: Call finish() with summary and all file paths."""


def validate_params(params: dict) -> tuple:
    missing = [k for k, v in PARAMETERS.items() if v.get("required") and not params.get(k)]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    return True, ""
