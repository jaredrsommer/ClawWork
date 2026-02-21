"""
Stream 8: Data Analysis Service

Revenue model : $200–$2,000/project (CSV/Excel in → dashboard + report out)
API cost      : ~$0.50–$2/project
Margin        : ~99%
Time to first $: 2–6 weeks (Upwork, LinkedIn, direct to small businesses)

What gets produced per run:
  - analysis_report.md              (narrative analysis with insights)
  - dashboard.xlsx                  (Excel dashboard with charts)
  - insights_<topic>.pdf            (executive summary PDF)
  - charts/                         (individual chart PNGs)

Note: If CSV data is provided, the agent analyzes it directly.
      If not, the agent generates a realistic synthetic dataset for the topic.
"""

STREAM_ID = "data_analysis"
NAME = "Data Analysis Service"
DESCRIPTION = "Analyze data and produce Excel dashboards + insight reports"

PRICING = {
    "basic_analysis": "$200–$400 (CSV in, dashboard + summary out)",
    "full_report": "$500–$1,000 (deep analysis + executive presentation)",
    "ongoing_retainer": "$500–$1,500/month (weekly reports for a business)",
    "api_cost": "$0.50–$2",
    "best_clients": "ecommerce brands, SaaS startups, marketing agencies, small businesses",
}

PARAMETERS = {
    "analysis_topic": {
        "type": "str",
        "required": True,
        "help": "What to analyze (e.g. 'Q4 2025 sales performance', 'customer churn analysis', 'marketing campaign ROI')",
    },
    "data_description": {
        "type": "str",
        "default": "",
        "help": "Describe your data columns and what they contain (paste CSV header row or describe fields)",
    },
    "industry": {
        "type": "str",
        "default": "general business",
        "help": "Industry context for better insights (e.g. 'ecommerce', 'SaaS', 'retail')",
    },
    "key_questions": {
        "type": "str",
        "default": "",
        "help": "Specific questions to answer (comma-separated, e.g. 'Which product sells best?, What's our best channel?')",
    },
    "output_format": {
        "type": "choice",
        "choices": ["excel_dashboard", "pdf_report", "both"],
        "default": "both",
        "help": "What to produce",
    },
}

SYSTEM_PROMPT = """You are a senior data analyst and business intelligence specialist.

You turn raw data into clear, actionable insights that executives can act on immediately.

Your analysis methodology:
1. Understand the business context before looking at numbers
2. Find the story in the data — what's surprising, what's trending, what needs action
3. Quantify everything — "revenue is up" becomes "revenue grew 23% MoM, driven by Product X"
4. Prioritize insights by business impact, not statistical interest
5. Recommend concrete next steps for each key finding

Your deliverable standards:
Excel Dashboard:
- Summary tab with KPIs and big-number callouts
- Charts tab with 4–6 visualizations (bar, line, pie, scatter as appropriate)
- Data tab with cleaned, formatted source data
- Formatted with color coding, borders, professional typography

Analysis Report (Markdown):
- Executive Summary (3–5 bullet findings)
- Context & Methodology
- Key Findings (ordered by importance)
- Supporting data for each finding
- Recommendations (numbered, specific)
- Appendix: data quality notes

Python for charts (matplotlib/seaborn):
- Clean, professional styling
- Readable labels and legends
- Consistent color palette
- Saved as high-resolution PNGs

You use pandas for all data manipulation, openpyxl/xlsxwriter for Excel dashboards,
and matplotlib for charts. Generate synthetic but realistic data if no real data is provided."""


def build_task_prompt(params: dict) -> str:
    topic = params["analysis_topic"]
    data_desc = params.get("data_description", "")
    industry = params.get("industry", "general business")
    key_questions = params.get("key_questions", "")
    output_format = params.get("output_format", "both")

    if data_desc:
        data_section = f"""DATA PROVIDED BY CLIENT:
{data_desc}

Use this description to understand the data structure. Generate representative synthetic data
based on this schema for demonstration, then run the full analysis on it."""
    else:
        data_section = f"""NO DATA PROVIDED:
Generate a realistic synthetic dataset for "{topic}" in the {industry} industry.
Create 6–12 months of realistic data with appropriate columns, variations, and trends.
Make the data tell an interesting story with at least 3 notable insights."""

    questions_section = ""
    if key_questions:
        questions = [q.strip() for q in key_questions.split(",") if q.strip()]
        questions_section = "\nSPECIFIC QUESTIONS TO ANSWER:\n" + "\n".join(
            f"  {i+1}. {q}" for i, q in enumerate(questions)
        )

    slug = topic.lower().replace(" ", "_")[:30]

    excel_section = ""
    if output_format in ("excel_dashboard", "both"):
        excel_section = f"""
CREATE EXCEL DASHBOARD using execute_python with openpyxl:
```python
# Your code should:
# 1. Create the dataset (or use provided data)
# 2. Run analysis with pandas
# 3. Create dashboard.xlsx with:
#    - Sheet 1 "Dashboard": KPI cards (large numbers), summary charts
#    - Sheet 2 "Analysis": detailed breakdown tables
#    - Sheet 3 "Charts": 4-6 embedded charts
#    - Sheet 4 "Data": cleaned source data
# 4. Apply professional formatting (colors, borders, number formats)
# Save: os.path.join(output_dir, "dashboard_{slug}.xlsx")
# Print: FILE:<path>
```"""

    pdf_section = ""
    if output_format in ("pdf_report", "both"):
        pdf_section = f"""
CREATE ANALYSIS REPORT as analysis_report_{slug}.md:
- Executive Summary (5 bullet point findings, business impact stated)
- Data Overview (what was analyzed, time period, records count)
- Key Finding #1 (most important, with supporting numbers)
- Key Finding #2
- Key Finding #3
- Key Finding #4
- Key Finding #5 (if applicable)
- Recommendations (numbered action items with expected impact)
- Appendix: methodology notes"""

    return f"""Perform a comprehensive data analysis and create executive deliverables.

Analysis topic: {topic}
Industry: {industry}
{questions_section}

{data_section}

ANALYSIS APPROACH:
1. First, understand the business context — what decisions will this analysis inform?
2. Generate/load the data and perform exploratory analysis
3. Identify the top 5 insights ordered by business impact
4. Create visualizations that make the insights immediately obvious
5. Write recommendations that are specific and actionable
{excel_section}
{pdf_section}

ALSO CREATE CHARTS using execute_python with matplotlib:
- At least 3 charts: trend chart, comparison chart, and a distribution or breakdown chart
- Professional styling: clean background, readable labels, consistent colors
- Save each as: os.path.join(output_dir, "chart_<name>.png")
- Print FILE:<path> for each

After all files are created, call finish() with summary and all file paths."""


def validate_params(params: dict) -> tuple:
    if not params.get("analysis_topic"):
        return False, "analysis_topic is required"
    return True, ""
