"""
Stream 2: Digital Products Factory

Revenue model : Create once, sell forever on Gumroad/Etsy/Payhip
Pricing       : $9–$49 per product
API cost      : ~$1–$3 per product created (one-time)
Margin        : ~99% after creation (zero marginal cost per sale)
Time to first $: 1–4 weeks (listing + discovery)

Product types supported:
  - excel_tracker    (budget, habit, business, fitness trackers)
  - pptx_template    (pitch decks, slide templates, presentation frameworks)
  - pdf_workbook     (guides, planners, worksheets, frameworks)
  - content_kit      (swipe file, caption pack, social media kit)
  - spreadsheet_tool (financial model, business calculator, dashboard)
"""

STREAM_ID = "products"
NAME = "Digital Products Factory"
DESCRIPTION = "Generate sellable digital products (Excel, PowerPoint, PDF) for Gumroad/Etsy"

PRICING = {
    "per_product_price": "$9–$49",
    "api_cost_one_time": "$1–$3",
    "platform_cut": "Gumroad 10%, Etsy $0.20 + 6.5%",
    "target_monthly": "100 products × 10 sales avg = $9,000–$49,000 MRR",
    "best_niches": "personal finance, productivity, business, fitness, real estate",
}

PARAMETERS = {
    "product_type": {
        "type": "choice",
        "choices": ["excel_tracker", "pptx_template", "pdf_workbook", "content_kit", "spreadsheet_tool"],
        "required": True,
        "help": "Type of digital product to create",
    },
    "niche": {
        "type": "str",
        "required": True,
        "help": "Target market niche (e.g. 'personal finance', 'fitness', 'real estate')",
    },
    "product_name": {
        "type": "str",
        "default": "",
        "help": "Specific product name (optional — agent picks a great one if empty)",
    },
    "price_point": {
        "type": "int",
        "default": 27,
        "help": "Target selling price in USD (default $27)",
    },
    "include_listing": {
        "type": "bool",
        "default": True,
        "help": "Also generate a Gumroad/Etsy product listing (title, description, tags)",
    },
}

SYSTEM_PROMPT = """You are a digital product creator who builds high-converting templates and tools.

You specialize in creating products that:
- Solve a specific, painful problem for the buyer
- Look professional and polished (people judge quality by appearance)
- Are immediately usable — no setup required
- Justify their price through clear value delivery

For Excel/Spreadsheet products:
- Use openpyxl or xlsxwriter to create formatted, formula-filled spreadsheets
- Include headers, color-coded sections, dropdowns where helpful
- Add an "Instructions" tab
- Make it feel like a premium tool

For PowerPoint products:
- Use python-pptx to create a fully designed template
- Include 10–20 slides covering common use cases
- Consistent color scheme, fonts, and layouts
- Placeholder text that guides the user

For PDF workbooks:
- Use reportlab to create a structured, printable workbook
- Include exercises, prompts, checklists, and tables
- Professional typography and layout

Always also create:
- A product_listing.md with Gumroad/Etsy title, description, tags, and price recommendation
- A product_preview.md with screenshot descriptions and key selling points"""


def build_task_prompt(params: dict) -> str:
    product_type = params["product_type"]
    niche = params["niche"]
    product_name = params.get("product_name", "")
    price_point = params.get("price_point", 27)
    include_listing = params.get("include_listing", True)

    type_instructions = {
        "excel_tracker": (
            "Create an Excel tracker using execute_python with openpyxl. "
            "Include: formatted headers, color coding, formulas, charts if relevant, "
            "an Instructions tab, and a dashboard/summary view. "
            "Save to output_dir and print FILE:<path>."
        ),
        "pptx_template": (
            "Create a PowerPoint template using execute_python with python-pptx. "
            "Include 12–20 slides: title slide, agenda, content slides (multiple layouts), "
            "quote slide, data/chart slide, team slide, CTA/close slide. "
            "Use a consistent color scheme. Save to output_dir and print FILE:<path>."
        ),
        "pdf_workbook": (
            "Create a PDF workbook using execute_python with reportlab. "
            "Include: cover page, table of contents, 8–12 content pages with text, "
            "exercises/prompts, checklists, and answer spaces. "
            "Professional layout with headers and footers. Save to output_dir and print FILE:<path>."
        ),
        "content_kit": (
            "Create a content kit as a markdown file using create_file. "
            "Include: 30-day content calendar, 50 caption templates, 100 hook ideas, "
            "hashtag packs by platform, content repurposing checklist, "
            "engagement response scripts. File type: md."
        ),
        "spreadsheet_tool": (
            "Create a business/financial spreadsheet tool using execute_python with openpyxl. "
            "Include: input cells clearly marked, formulas that calculate outputs automatically, "
            "a results dashboard, charts, and color coding. "
            "Save to output_dir and print FILE:<path>."
        ),
    }.get(product_type, "Create a useful digital product for the specified niche.")

    name_section = (
        f"Product name: {product_name}"
        if product_name
        else f"Choose a compelling product name that will sell well in the {niche} market."
    )

    listing_section = ""
    if include_listing:
        listing_section = """
After creating the product, also create a product_listing.md file with:
- Optimized title (under 60 chars, keyword-rich)
- Product description (200–400 words, benefits-focused, with bullet points)
- 13 relevant Etsy tags OR 10 Gumroad tags
- Suggested price and pricing psychology justification
- 5 thumbnail description ideas (what screenshots/mockups to create)
- Marketing hook (1-2 sentences for social media promotion)"""

    return f"""Create a premium digital product for the {niche} market.

{name_section}
Product type: {product_type}
Target price: ${price_point}

RESEARCH PHASE:
1. Search the web for best-selling {product_type.replace('_', ' ')} products in the {niche} niche
2. Look at what buyers are saying they want (Reddit, Etsy reviews, Gumroad comments)
3. Identify the #1 pain point this product should solve

CREATION PHASE:
{type_instructions}

QUALITY STANDARD:
- This product should look like it was made by a professional designer
- Every section should provide clear, immediate value
- The buyer should think "this is worth 10x what I paid"
{listing_section}

After all files are created, call finish() with a summary and all file paths."""


def validate_params(params: dict) -> tuple:
    missing = [k for k, v in PARAMETERS.items() if v.get("required") and not params.get(k)]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    valid_types = PARAMETERS["product_type"]["choices"]
    if params.get("product_type") not in valid_types:
        return False, f"product_type must be one of: {', '.join(valid_types)}"
    return True, ""
