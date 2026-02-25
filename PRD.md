# Product Requirements Document: Healthcare Report Assistant

**Version:** 1.0
**Date:** 2026-02-24
**Status:** Draft

---

## 1. Executive Summary

The Healthcare Report Assistant is a Python-based Streamlit application that automates the process of compiling healthcare data into a structured report for a healthcare advisor. The user currently tracks glucose readings via a monitoring app and mood via a paper template, then manually compiles this data into a final report — a tedious, error-prone process.

The application will parse glucose monitoring PDF exports, allow the user to review and correct extracted data (notably re-categorizing generic "meal" labels into breakfast, lunch, dinner, or snack), enter mood data digitally, and generate a final report PDF. An integrated AI chat agent provides general Q&A support, with plans to expand into nutrition research.

**MVP Goal:** Deliver a working multi-page Streamlit app that replaces the manual report compilation workflow, enabling the user to upload a glucose PDF, correct meal labels, enter mood data, and generate the final advisor report — all within a single session.

---

## 2. Mission

**Mission Statement:** Simplify and automate personal healthcare data management so the user can focus on health outcomes rather than paperwork.

**Core Principles:**
1. **Speed to value** — Get the reporting workflow running as fast as possible; the user needs this tool now
2. **User control** — The user reviews and corrects all data before report generation; no blind automation
3. **Iterative improvement** — Start with what works (current report format), then improve over time
4. **Learning platform** — This is also a learning project; embrace diverse technologies and experimentation
5. **Simplicity first** — Local files before databases, single app before microservices

---

## 3. Target Users

### Primary User: The Patient (Solo User)

- **Who:** Individual managing personal healthcare data for an advisor
- **Technical comfort:** Comfortable with Python development, CLI tools, and running local applications
- **Current workflow:**
  - Exports glucose data as PDF from a monitoring app
  - Fills out a mood template by hand
  - Manually compiles both into a final report PDF for their advisor
- **Pain points:**
  - Glucose PDF labels all food entries as "meal" — must be manually re-categorized
  - Glucose PDF includes the current (incomplete) day and more days than needed
  - Manual compilation is tedious and time-consuming
  - No easy way to look up nutrition information while preparing the report

---

## 4. MVP Scope

### In Scope (MVP)

**Core Functionality:**
- ✅ Upload and parse glucose monitoring PDF (mixed tables and charts)
- ✅ Select date range for reporting (typically 5 days, flexible, excluding incomplete current day)
- ✅ Display extracted glucose data in a reviewable table
- ✅ Dropdown per row to re-categorize meal type (breakfast/lunch/dinner/snack)
- ✅ Editable cells for correcting PDF parsing errors
- ✅ Mood data entry form (based on user's existing mood template)
- ✅ Generate final report PDF matching the user's current report format
- ✅ Download generated report
- ✅ AI chat agent for general Q&A

**Technical:**
- ✅ Multi-page Streamlit application
- ✅ PDF parsing with pdfplumber
- ✅ PDF generation with ReportLab
- ✅ LLM integration via LiteLLM (starting with Anthropic/Claude)
- ✅ Local JSON file storage for session data
- ✅ Pydantic data models for validation
- ✅ UV package management
- ✅ python-dotenv for configuration

### Out of Scope (Post-MVP)

**Features:**
- ❌ Nutrition API integration (calorie lookup for food items)
- ❌ Weight tracking in reports
- ❌ Auto-suggest meal types based on time of day
- ❌ Report template redesign through the UI

**Technical:**
- ❌ Docker containerization (Streamlit UI + Postgres DB)
- ❌ PostgreSQL database
- ❌ Multi-LLM experimentation (infrastructure is ready via LiteLLM, but not a focus for MVP)

---

## 5. User Stories

### Primary User Stories

1. **As a patient, I want to upload my glucose monitoring PDF, so that I don't have to manually transcribe the data.**
   - *Example:* I export a PDF from my glucose app covering the last 10 days. I upload it to the app and it extracts the tabular data automatically.

2. **As a patient, I want to select which dates to include in my report, so that I only report on the relevant days (usually 5) and exclude the incomplete current day.**
   - *Example:* The PDF has data from Feb 14–24, but I only need Feb 18–22. I pick those dates and the app filters accordingly.

3. **As a patient, I want to change the meal type for each food entry from "meal" to the correct category, so that my report accurately reflects when I ate.**
   - *Example:* The PDF shows "Oatmeal — Meal" at 7:30am. I use a dropdown to change "Meal" to "Breakfast."

4. **As a patient, I want to correct any parsing errors in the extracted data, so that my report is accurate.**
   - *Example:* The PDF parser misreads "120 mg/dL" as "12 mg/dL." I edit the cell directly to fix it.

5. **As a patient, I want to enter my mood data digitally instead of filling out a paper form, so that it's included in the final report automatically.**
   - *Example:* For each of my 5 selected days, I fill out the mood form fields in the app.

6. **As a patient, I want to generate a PDF report that matches the format my advisor expects, so that I can submit it directly.**
   - *Example:* I click "Generate Report" and download a PDF that looks like the template my advisor gave me, pre-filled with my data.

7. **As a patient, I want to ask an AI agent general health-related questions while preparing my report, so that I can get quick answers without leaving the app.**
   - *Example:* While reviewing my food entries, I ask the chat "What's a healthy alternative to white rice?" and get a response.

8. **As a patient, I want my session data saved locally, so that I can come back and make corrections before generating the final report.**
   - *Example:* I upload and review data on Monday, then come back Tuesday to enter mood data and generate the report.

---

## 6. Core Architecture & Patterns

### Architecture: Multi-Page Streamlit Application

Each workflow step maps to a dedicated Streamlit page. Shared state is managed via `st.session_state` and persisted to local JSON files.

```
┌─────────────────────────────────────────────────┐
│                  Streamlit UI                    │
│  ┌──────┐ ┌──────┐ ┌────┐ ┌────┐ ┌──────────┐  │
│  │Upload│ │Review│ │Mood│ │Chat│ │Gen Report│  │
│  └──┬───┘ └──┬───┘ └──┬─┘ └──┬─┘ └────┬─────┘  │
│     │        │        │      │         │        │
├─────┼────────┼────────┼──────┼─────────┼────────┤
│     ▼        ▼        ▼      ▼         ▼        │
│  ┌─────────────────────────────────────────┐    │
│  │            src/ (Business Logic)        │    │
│  │  pdf_parser │ models │ storage │ llm    │    │
│  │  pdf_generator                          │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                           │
│                     ▼                           │
│  ┌─────────────────────────────────────────┐    │
│  │         data/ (Local Storage)           │    │
│  │  uploads/ │ sessions/ │ reports/        │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### Directory Structure

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

### Key Design Patterns

- **Separation of concerns:** UI pages (app/) are thin — business logic lives in src/
- **Data validation:** All parsed data flows through Pydantic models before use
- **Configurable parsing:** PDF column positions and header names are configuration, not hardcoded
- **Session-based workflow:** Each report session is a self-contained JSON document
- **Provider abstraction:** LiteLLM abstracts the LLM provider, enabling future experimentation

---

## 7. Features

### Feature 1: PDF Upload & Parsing

**Purpose:** Extract structured glucose data from a Dexcom Clarity PDF export.

**Source Format (Dexcom Clarity "Daily" view):**
- One page per day, newest day first, with a glucose chart and data table
- Table columns: **Time | Device | Event | Details | Insulin Units | Glucose**
- Event types: "Meal" (all food entries) and "Walking" (exercise)
- Exercise details format: "33 min • 88 BPM"
- Glucose values format: "117 mg/dL"
- Device is always "CGM"
- 14 days of data typically included; first page may be an incomplete current day

**Operations:**
- Accept PDF file upload via Streamlit file_uploader
- Parse tables using pdfplumber, page by page
- Extract date header from each page (e.g., "Sun, Feb 22, 2026")
- Parse each table row into a GlucoseEntry
- Separate "Meal" events from "Walking" events
- Return structured data as list of GlucoseEntry and ExerciseEntry objects

**Key Details:**
- Parser targets the specific Dexcom Clarity layout (known columns, known structure)
- Exercise entries are stored separately (different data shape)
- Validates all entries with Pydantic before displaying

### Feature 2: Date Range Selection

**Purpose:** Filter extracted data to the relevant reporting period.

**Operations:**
- Date range picker (start/end dates)
- Default: last 5 complete days (excluding today)
- Flexible: user can select any range and number of days
- Filter glucose entries to selected dates only

### Feature 3: Data Review & Correction

**Purpose:** Let the user verify and fix extracted data before report generation.

**Operations:**
- Display glucose entries in an editable Streamlit data table
- Dropdown per row for meal_type: breakfast, lunch, dinner, snack
- Inline editing for glucose readings, food items, notes
- Save corrections to session JSON

### Feature 4: Mood Data Entry

**Purpose:** Replace the paper mood template with digital entry.

**Mood Template Structure (4 time slots per day):**
- **After Breaking Fast** — time (from first meal), energy (text), mood (1-5)
- **Around Noon** — time (default 12:00 PM), energy (text), mood (1-5)
- **After Dinner** — time (from last meal), energy (text), mood (1-5)
- **Before Bed** — time (optional), energy (text), mood (1-5)

**Energy values:** Free text (e.g., "Tired", "Ok", "Good", "Great")
**Mood values:** Numeric scale 1-5

**Operations:**
- Render form with 4 time slots per day for each selected date
- Pre-populate times from glucose data where possible (first meal → After Breaking Fast, last meal → After Dinner)
- Energy as text input or dropdown with common values
- Mood as numeric selector (1-5)
- Save entries to session JSON

### Feature 5: AI Chat Agent

**Purpose:** Provide general Q&A support while the user prepares their report.

**Operations:**
- Chat interface in Streamlit
- Claude (via LiteLLM) as the backend
- Conversational memory within the session
- MVP scope: general health Q&A only

### Feature 6: Report Generation

**Purpose:** Generate the final PDF report ("5-Day Food, Energy, and Mood Journal") for the user's advisor.

**Output Format:**
- Title: "5-Day Food, Energy, and Mood Journal"
- Header: Name, date range, source PDF filename
- One section per day (newest first), each with a table:
  - Columns: **Event | Time of Day | Details | Energy | Mood**
  - Mood rows (After Breaking Fast, Around Noon, After Dinner, Before Bed) interleaved with food/exercise entries at the correct time positions
  - Meal types corrected (Breakfast, Lunch, Dinner, Snack — not "Meal")
  - Exercise entries included

**Operations:**
- Combine glucose + mood data, ordered by time within each day
- Interleave mood time-slot rows at their correct positions
- Generate PDF using ReportLab matching the report structure above
- Preview before download
- Download button for the generated PDF

---

## 8. Technology Stack

### Core

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Application language |
| UV | Latest | Package management |
| Streamlit | Latest | UI framework (multi-page) |

### Dependencies

| Library | Purpose |
|---------|---------|
| pdfplumber | PDF table extraction |
| reportlab | PDF report generation |
| litellm | LLM provider abstraction |
| pydantic | Data validation and models |
| python-dotenv | Environment variable management |

### Optional / Future Dependencies

| Library | Purpose | Phase |
|---------|---------|-------|
| Nutrition API client (TBD) | Calorie/nutrition lookup | Post-MVP |
| psycopg2 / asyncpg | PostgreSQL client | Post-MVP |
| Docker | Containerization | Post-MVP |

---

## 9. Security & Configuration

### Configuration Management

**Environment Variables (.env):**
```
ANTHROPIC_API_KEY=<your-key>
# Future: additional LLM provider keys
# Future: nutrition API key
```

### Security Scope

**In Scope:**
- ✅ API keys stored in .env, never committed to git
- ✅ .gitignore includes .env, data/uploads/, data/sessions/, data/reports/
- ✅ Input validation on uploaded PDFs (file type, size limits)

**Out of Scope (single-user local app):**
- ❌ User authentication
- ❌ Network access controls
- ❌ Data encryption at rest
- ❌ HIPAA compliance (this is a personal tool, not a clinical system)

### Data Privacy Note

All data stays local on the user's machine. PDF uploads, session data, and generated reports are stored in the local `data/` directory. The only external communication is with the LLM API (Anthropic) for the chat feature.

---

## 10. Success Criteria

### MVP Success Definition

The MVP is successful when the user can complete their full reporting workflow within the app: upload a glucose PDF, select dates, correct meal labels, enter mood data, and generate a final report PDF that matches their advisor's expected format.

### Functional Requirements

- ✅ Successfully parse glucose data from the user's specific PDF format
- ✅ Date range selection filters data correctly (default 5 days, excluding today)
- ✅ All meal types can be re-categorized via dropdown (breakfast/lunch/dinner/snack)
- ✅ Mood data entry covers all fields from the mood template
- ✅ Generated PDF matches the structure of the user's current report template
- ✅ Chat agent responds to general health questions
- ✅ Session data persists across app restarts (JSON storage)

### Quality Indicators

- PDF parsing correctly extracts >90% of glucose entries without manual correction
- Report generation takes under 5 seconds
- App loads and is usable within 3 seconds

### User Experience Goals

- Complete the full workflow (upload → report) in under 15 minutes
- Meal type correction is fast and intuitive (dropdown, not typing)
- Clear indication of which dates are included and data completeness

---

## 11. Implementation Phases

### Phase 1: Project Setup & Data Models

**Goal:** Establish project structure, dependencies, and core data models.

**Deliverables:**
- ✅ Initialize UV project with pyproject.toml
- ✅ Create directory structure (app/, src/, data/, templates/)
- ✅ Define Pydantic models (GlucoseEntry, MoodEntry, ReportSession)
- ✅ Implement JSON storage module (save/load sessions)
- ✅ Configure .env and python-dotenv
- ✅ Basic Home.py with navigation

**Validation:** Models can be instantiated and serialized to/from JSON files.

### Phase 2: PDF Parsing & Data Review

**Goal:** Upload, parse, and review glucose data.

**Deliverables:**
- ✅ Upload page with file uploader and date picker
- ✅ pdfplumber parsing logic for glucose PDF
- ✅ Review page with editable table and meal type dropdowns
- ✅ Save corrected data to session

**Validation:** User can upload their glucose PDF, see extracted data, correct meal types, and save. Requires sample PDF from user for parser tuning.

### Phase 3: Mood Entry & Report Generation

**Goal:** Complete the data pipeline with mood entry and PDF output.

**Deliverables:**
- ✅ Mood entry page with form fields (based on user's template)
- ✅ ReportLab report generation matching the user's template format
- ✅ Report preview and download
- ✅ Generate Report page

**Validation:** User can enter mood data and generate a PDF report that matches their advisor's expected format. Requires mood template and output template from user.

### Phase 4: AI Chat & Polish

**Goal:** Add the AI chat agent and polish the overall experience.

**Deliverables:**
- ✅ LiteLLM client wrapper (configured for Anthropic/Claude)
- ✅ Chat page with conversational interface
- ✅ Home page with session status
- ✅ Error handling and user feedback across all pages
- ✅ End-to-end testing of the full workflow

**Validation:** User can complete the full workflow and use the chat agent for general Q&A.

---

## 12. Future Considerations

### Post-MVP Enhancements

1. **Nutrition API Integration** — Connect to a nutrition database (e.g., USDA FoodData Central, Nutritionix) for calorie and nutrient lookup. The AI agent would use this to answer specific food questions with accurate data.

2. **Weight Tracking** — Add weight as a data point in the report. Could be manual entry or integration with a scale/app.

3. **Report Template Redesign** — The final output form is user-controlled. Build a UI for modifying the report layout without code changes.

4. **Smart Meal Type Suggestions** — Auto-assign meal types based on time of day (7-10am = breakfast, etc.) with user override. Reduces manual dropdown work.

5. **Docker Deployment** — Containerize with two containers: one for the Streamlit UI, one for PostgreSQL. Migrate from JSON storage to Postgres.

6. **Multi-LLM Experimentation** — LiteLLM is already in place. Add configuration to switch between Claude, GPT, Gemini, and local models (Ollama) for comparison.

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **PDF format varies between exports** | Parser breaks on unexpected layouts | Build configurable parser with column mapping; tune with real PDF samples early |
| **pdfplumber can't extract all table data** | Missing or garbled glucose entries | Fall back to manual entry for problem rows; explore alternative parsers (camelot, tabula) if needed |
| **Mood template structure is unknown** | Can't build mood entry form | User will upload template; design form fields to be data-driven from template structure |
| **Report template is complex to replicate** | Generated PDF doesn't match expected format | User will upload example; start with a close approximation and iterate |
| **LiteLLM API costs** | Unexpected API charges during development | Use Claude Haiku for development/testing; set up usage monitoring |

---

## 14. Appendix

### Related Documents

- [Design Document](docs/plans/2026-02-24-healthcare-report-assistant-design.md) — Approved architectural design

### Sample Files (Provided)

All sample files are in `docs/samples/`:

1. **`clarity_2026-02-18_to_2026-02-22.pdf`** — Dexcom Clarity glucose export (14 days, 11 pages, Daily view)
2. **`mood_intake_2026-02-18_to_2026-02-22.md`** — Mood intake worksheet template (markdown)
3. **`report_2026-02-18_to_2026-02-22.md`** — Final output report example (markdown → will generate as PDF)

### Key Dependencies

| Dependency | Documentation |
|-----------|---------------|
| Streamlit | https://docs.streamlit.io |
| pdfplumber | https://github.com/jsvine/pdfplumber |
| ReportLab | https://docs.reportlab.com |
| LiteLLM | https://docs.litellm.ai |
| Pydantic | https://docs.pydantic.dev |
| UV | https://docs.astral.sh/uv |
