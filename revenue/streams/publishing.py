"""
Stream 7: Amazon KDP Publishing

Revenue model : $2–$7/sale at 35–70% royalty on KDP
               100 books × 5 sales/month × $3.50 avg = $1,750 MRR passive
API cost      : ~$1–$3/book
Margin        : ~99% after creation
Time to first $: 1–3 months (publishing + ranking)

Output per run:
  - <title>_manuscript.md    (full book manuscript, ready for formatting)
  - <title>_manuscript.docx  (Word doc, KDP-upload ready)
  - kdp_metadata.md          (title, subtitle, description, keywords, categories)
  - chapter_outline.md       (detailed chapter plan)
"""

STREAM_ID = "publishing"
NAME = "Amazon KDP Publishing"
DESCRIPTION = "Generate complete book manuscripts for Amazon Kindle publishing"

PRICING = {
    "per_book_royalty": "$2–$7/sale (35–70% of list price)",
    "scale_target": "100 books × 5 sales × $3.50 = $1,750/month passive",
    "api_cost_per_book": "$1–$3",
    "best_niches": "self-help, business/entrepreneurship, how-to guides, career, finance",
    "important_note": "Human editing pass STRONGLY recommended before publishing (Amazon policy)",
}

PARAMETERS = {
    "title": {
        "type": "str",
        "required": True,
        "help": "Book title (e.g. 'The 5AM Framework: How Morning Routines Build Millionaires')",
    },
    "genre": {
        "type": "choice",
        "choices": [
            "self_help", "business", "how_to", "personal_finance",
            "productivity", "career", "health_wellness", "relationships",
        ],
        "required": True,
        "help": "Book genre/category",
    },
    "target_reader": {
        "type": "str",
        "default": "general adult readers",
        "help": "Who is this book for? (e.g. 'entrepreneurs in their 30s', 'new managers')",
    },
    "length": {
        "type": "choice",
        "choices": ["short", "medium", "full"],
        "default": "medium",
        "help": "short=10k words (~40 pages), medium=20k words (~80 pages), full=30k words (~120 pages)",
    },
    "chapters": {
        "type": "int",
        "default": 8,
        "help": "Number of chapters (default 8)",
    },
    "tone": {
        "type": "choice",
        "choices": ["authoritative", "conversational", "motivational", "academic"],
        "default": "conversational",
        "help": "Writing tone",
    },
}

SYSTEM_PROMPT = """You are a professional nonfiction author and ghostwriter specializing in KDP publishing.

You write books that:
- Hook readers with a powerful introduction that makes them feel understood
- Deliver genuine, actionable value — not just recycled common wisdom
- Use stories, case studies, and examples to make concepts concrete
- Build on each chapter to create a coherent transformation journey
- End each chapter with action steps so readers actually implement

Your KDP optimization skills:
- Titles: benefit-driven, keyword-rich, searchable on Amazon
- Subtitles: clarify the specific promise ("How to..." or "The X-Step System for...")
- Book descriptions: follow AIDA (Attention, Interest, Desire, Action)
- Keywords: target phrases readers actually search on Amazon
- Categories: find the right niche where you can rank (avoid over-crowded categories)

Structure every book:
1. Introduction: Why this book, the transformation promise, the author's story
2. Part 1: Foundation (chapters 1–2): Understanding the problem
3. Part 2: Framework (chapters 3–5): The core methodology
4. Part 3: Implementation (chapters 6–8): Putting it into practice
5. Conclusion: The reader's future, next steps, call to action
6. Appendix/Resources: Templates, checklists, further reading

Write at a 9th-grade reading level for maximum accessibility. Use active voice."""


def build_task_prompt(params: dict) -> str:
    title = params["title"]
    genre = params.get("genre", "self_help")
    target_reader = params.get("target_reader", "general adult readers")
    length = params.get("length", "medium")
    chapters = params.get("chapters", 8)
    tone = params.get("tone", "conversational")

    word_targets = {"short": 10000, "medium": 20000, "full": 30000}
    target_words = word_targets.get(length, 20000)
    words_per_chapter = target_words // chapters

    slug = title.lower().replace(" ", "_")[:35]

    return f"""Write a complete nonfiction book manuscript.

Title: {title}
Genre: {genre.replace('_', ' ').title()}
Target reader: {target_reader}
Target length: ~{target_words:,} words ({chapters} chapters × ~{words_per_chapter:,} words each)
Tone: {tone}

STEP 1: Research
Search for:
- Top Amazon bestsellers in the {genre.replace('_', ' ')} category (for structure and positioning)
- Key concepts, frameworks, and ideas related to "{title}"
- Statistics, studies, and expert quotes to cite in the book
- Real success stories or case studies to include

STEP 2: Create chapter outline
Create chapter_outline_{slug}.md with:
- Full chapter-by-chapter outline (chapter title + 5–7 bullet points of what's covered)
- 3 key takeaways per chapter
- Story/case study planned for each chapter
- Action exercise for each chapter end

STEP 3: Write the manuscript
Create {slug}_manuscript.md with the COMPLETE book text:

Front matter:
- Title page
- Copyright page (note: [Year] [Author Name])
- Table of contents
- Dedication
- Introduction (800–1,200 words)

Main chapters ({chapters} chapters, ~{words_per_chapter:,} words each):
For each chapter:
- Chapter number and title
- Opening story or hook
- Core content (the teaching)
- Supporting evidence (stats, examples, case studies)
- Practical application section
- Chapter summary (3 key points)
- Action step: one thing to do TODAY

Back matter:
- Conclusion (500–800 words)
- About the Author (placeholder)
- Acknowledgments
- References/Further Reading

Also create {slug}_manuscript.docx using execute_python with python-docx,
formatted for KDP publishing (12pt Times New Roman, 1" margins, proper heading styles).
Print FILE:<path> when saved.

STEP 4: Create KDP metadata
Create kdp_metadata_{slug}.md with:
- Book title and subtitle
- 7 Amazon backend keywords (what readers search)
- 2 BISAC categories (browse nodes)
- Amazon book description (400–600 words, HTML formatted for KDP)
- A+ Content ideas (enhanced brand content)
- Back cover blurb (200 words)
- Pricing recommendation

After all files are created, call finish() with summary and all file paths."""


def validate_params(params: dict) -> tuple:
    missing = [k for k, v in PARAMETERS.items() if v.get("required") and not params.get(k)]
    if missing:
        return False, f"Missing required parameters: {', '.join(missing)}"
    return True, ""
