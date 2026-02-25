# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Healthcare Report Assistant — a multi-page Streamlit application that automates compiling glucose monitoring data and mood tracking into a structured PDF report for a healthcare advisor. The user uploads a glucose PDF, corrects meal labels, enters mood data, and generates the final report. Includes an AI chat agent (Claude via LiteLLM) for general Q&A.

This is a personal tool and learning project. Prioritize getting it working over perfection.

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12+ | Application language |
| UV | Package manager |
| Streamlit | Multi-page UI framework |
| pdfplumber | PDF table extraction (glucose reports) |
| ReportLab | PDF report generation |
| LiteLLM | LLM provider abstraction (starting with Anthropic/Claude) |
| Pydantic | Data models and validation |
| python-dotenv | Environment variable management |

---

## Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app/Home.py

# Run tests
uv run pytest

# Type checking
uv run mypy src/
```

---

## Project Structure

```
healthcare/
├── app/                           # Streamlit UI pages
│   ├── Home.py                    # Entry point and landing page
│   └── pages/
│       ├── 1_Upload.py            # Upload glucose PDF
│       ├── 2_Review_Data.py       # Review & correct extracted data
│       ├── 3_Mood_Entry.py        # Enter mood data
│       ├── 4_Chat.py              # AI chat agent
│       └── 5_Generate_Report.py   # Generate final PDF
├── src/                           # Business logic (no UI code here)
│   ├── pdf_parser.py              # pdfplumber extraction logic
│   ├── pdf_generator.py           # ReportLab report generation
│   ├── models.py                  # Pydantic data models
│   ├── storage.py                 # JSON file read/write
│   └── llm_client.py             # LiteLLM wrapper
├── data/                          # Runtime data (gitignored)
│   ├── uploads/                   # Uploaded PDFs
│   ├── sessions/                  # Session data (JSON)
│   └── reports/                   # Generated report PDFs
├── templates/                     # Report template config
│   └── report_template.json
├── tests/                         # Test files
├── docs/                          # Documentation and plans
│   └── plans/                     # Design and implementation plans
├── PRD.md                         # Product Requirements Document
├── pyproject.toml                 # UV project config
├── .env                           # API keys (never commit)
└── .env.example                   # Template for .env
```

---

## Architecture

**Pattern:** Multi-page Streamlit with separated business logic.

- **app/pages/** — Thin UI layer. Each page handles display and user interaction only.
- **src/** — All business logic. Pages import from src/, never the reverse.
- **data/** — Runtime storage. Gitignored. JSON files for MVP, Postgres later.
- **templates/** — Report layout configuration. Stored as JSON so it can be modified without code changes.

**Data Flow:**
```
Upload PDF → pdfplumber (src/pdf_parser.py) → Pydantic models (src/models.py)
  → User review/correction (app/pages/2_Review_Data.py)
  → Save to JSON (src/storage.py)
  → Combine with mood data → ReportLab (src/pdf_generator.py) → Final PDF
```

**State Management:** Use `st.session_state` for in-session state. Persist to JSON files in `data/sessions/` for cross-session continuity.

---

## Code Patterns

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Streamlit pages: `N_Page_Name.py` (number prefix for ordering)
- Constants: `UPPER_SNAKE_CASE`

### File Organization
- One module per concern in `src/`
- UI pages are thin — import logic from `src/`, don't define it inline
- Pydantic models are the single source of truth for data shapes

### Error Handling
- Validate all parsed PDF data through Pydantic before use
- Show user-friendly errors in Streamlit (`st.error()`, `st.warning()`)
- Log detailed errors for debugging
- Never silently drop data — flag parsing issues for user review

### Data Validation
- All data entering the system passes through Pydantic models
- PDF parsing results are validated before display
- User corrections are validated before saving

---

## Testing

- **Run tests**: `uv run pytest`
- **Test location**: `tests/`
- **Pattern**: Test business logic in `src/` directly. UI pages are tested via end-to-end workflows.
- **Focus areas**: PDF parsing accuracy, data model validation, JSON storage round-trips

---

## Validation

```bash
# Before committing, run:
uv run pytest
uv run mypy src/
```

---

## Key Files

| File | Purpose |
|------|---------|
| `PRD.md` | Full product requirements and scope |
| `docs/plans/2026-02-24-healthcare-report-assistant-design.md` | Approved design document |
| `src/models.py` | Pydantic data models — the data contract |
| `src/pdf_parser.py` | Core PDF extraction logic — will need tuning per PDF format |
| `templates/report_template.json` | Report layout config — modify to change report format |
| `.env.example` | Required environment variables |

---

## On-Demand Context

| Topic | File |
|-------|------|
| Full requirements | `PRD.md` |
| Architecture decisions | `docs/plans/2026-02-24-healthcare-report-assistant-design.md` |

---

## Notes

- This is a **single-user local application** — no auth, no multi-tenancy
- The glucose PDF parser will need tuning once a sample PDF is provided
- Mood form fields are TBD until the mood template PDF is uploaded
- The `data/` directory is gitignored — it contains personal health data
- API keys go in `.env`, never hardcoded
- LiteLLM is configured for Anthropic/Claude first, but supports swapping providers
- MVP uses JSON storage; Postgres + Docker is planned for post-MVP
