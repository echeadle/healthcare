# Healthcare Report Assistant — Design Document

**Date**: 2026-02-24
**Status**: Approved

## Overview

A Streamlit multi-page application that takes glucose monitoring PDF exports and mood data, lets the user review and correct the data, and generates a final report PDF for their healthcare advisor.

## Problem Statement

The user tracks glucose readings via a monitoring app and mood via a paper template. The glucose app exports a PDF where all food items are labeled "meal" instead of the user's preferred categories (breakfast, lunch, dinner, snack). The user must manually compile this data into a final report for their advisor. This app automates that process.

## Architecture

**Approach**: Multi-Page Streamlit (Approach B)

Each workflow step gets its own Streamlit page. Shared state managed via `st.session_state`. This provides clean separation of concerns while keeping MVP complexity low, and maps naturally to a future Docker deployment.

## Tech Stack

| Component | Library | Rationale |
|-----------|---------|-----------|
| Language | Python 3.12+ | User preference |
| Package Manager | UV | User preference |
| UI Framework | Streamlit (multi-page) | User preference, rapid prototyping |
| PDF Parsing | pdfplumber | Best for extracting tables from mixed-format PDFs |
| PDF Generation | ReportLab | Full layout control, can replicate existing report template |
| LLM Integration | LiteLLM | Unified interface for multiple LLM providers |
| Environment | python-dotenv | User preference |
| Data Storage (MVP) | JSON files | Simple, supports nested data structures |
| Data Validation | Pydantic | Clean data models, validation of parsed PDF data |

## Project Structure

```
healthcare/
├── app/
│   ├── Home.py                    # Main entry point / landing page
│   └── pages/
│       ├── 1_Upload.py            # Upload glucose PDF
│       ├── 2_Review_Data.py       # Review & correct extracted data
│       ├── 3_Mood_Entry.py        # Enter mood data
│       ├── 4_Chat.py              # AI chat agent
│       └── 5_Generate_Report.py   # Generate final PDF
├── src/
│   ├── pdf_parser.py              # pdfplumber extraction logic
│   ├── pdf_generator.py           # ReportLab report generation
│   ├── models.py                  # Pydantic data models
│   ├── storage.py                 # JSON file read/write
│   └── llm_client.py             # LiteLLM wrapper
├── data/
│   ├── uploads/                   # Uploaded PDFs
│   ├── sessions/                  # Saved session data (JSON)
│   └── reports/                   # Generated report PDFs
├── templates/
│   └── report_template.json       # Final report structure/config
├── .env
├── .env.example
├── pyproject.toml
└── README.md
```

## Data Models

### GlucoseEntry
- `date`: date of reading
- `time`: time of reading
- `glucose_reading`: mg/dL value
- `food_item`: what was eaten
- `meal_type`: breakfast / lunch / dinner / snack (user-corrected)
- `notes`: additional info from PDF

### MoodEntry
- `date`: date of entry
- `time`: time of entry
- Additional fields TBD based on the user's mood template PDF

### ReportSession
- `date_range_start`, `date_range_end`: overall range
- `selected_dates`: specific days to include (typically 5)
- `glucose_entries[]`: list of GlucoseEntry
- `mood_entries[]`: list of MoodEntry
- `status`: draft / finalized

All stored as JSON in `data/sessions/`.

## Page-by-Page Workflow

### Home Page
- Welcome/overview
- Quick status of any in-progress sessions

### Page 1 — Upload
- File uploader for glucose monitoring PDF
- Date picker for date range (defaults to last 5 days, excluding today)
- "Extract Data" button parses PDF with pdfplumber
- Preview of extracted data before proceeding

### Page 2 — Review Data
- Table of extracted glucose entries for selected dates
- Dropdown per row for meal_type (breakfast/lunch/dinner/snack)
- Editable cells for corrections to parsing errors
- "Save" button to persist corrections

### Page 3 — Mood Entry
- Form based on mood template structure
- One entry per day for each selected date
- Save to session

### Page 4 — Chat
- Chat interface with Claude via LiteLLM
- General Q&A for MVP
- Post-MVP: nutrition lookup, food research

### Page 5 — Generate Report
- Preview of final report with all data combined
- "Generate PDF" button creates report via ReportLab
- Download button for generated PDF

## PDF Parsing Strategy

1. Use pdfplumber to extract tables page by page
2. Identify data tables by looking for columns (date, time, glucose, food/meal)
3. Parse rows into GlucoseEntry objects, validate with Pydantic
4. Filter by selected date range
5. Default all meal_type to "meal" — user corrects in Review page
6. Skip pages with only charts
7. Parser is configurable (column positions, header names) for tuning once sample PDF is provided

## PDF Report Generation

1. ReportLab generates the final PDF
2. Replicates the user's current report template layout
3. Populates fields from session data (glucose + mood)
4. Template structure stored in `templates/report_template.json` for easy modification
5. Future: allow report format redesign through the UI

## MVP Scope

- Upload & parse glucose PDF
- Date range selection (typically 5 days, flexible)
- Review table with meal type dropdowns
- Mood data entry based on template
- AI chat (Claude via LiteLLM, general Q&A)
- Generate final report PDF
- Local JSON storage

## Post-MVP Roadmap

- Nutrition API integration (calorie lookup for food items)
- Weight tracking in reports
- Report template redesign through the UI
- Docker containers (Streamlit UI container + Postgres DB container)
- Experiment with different LLMs via LiteLLM
- Auto-suggest meal types based on time of day
