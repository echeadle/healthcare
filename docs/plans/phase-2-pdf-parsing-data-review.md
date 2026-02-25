# Phase 2: PDF Parsing & Data Review

## Context

Phase 1 is complete — Pydantic models (`GlucoseEntry`, `ExerciseEntry`, `MoodEntry`, `ReportSession`), JSON storage (`save_session`/`load_session`), and the Home page are all working with tests passing. Phase 2 implements the core data pipeline: parsing Dexcom Clarity glucose PDFs and letting the user review/correct the extracted data.

**Problem:** The user's glucose PDF labels all food entries as "Meal" and includes 14 days of data. They need to upload the PDF, select relevant dates (typically 5), correct meal types (breakfast/lunch/dinner/snack), and save corrections — all before mood entry and report generation in Phase 3.

**Outcome:** A working `src/pdf_parser.py`, functional Upload page, functional Review page, and parser tests validated against the real sample PDF.

---

## User Story

As a patient, I want to upload my Dexcom Clarity PDF and review the extracted glucose data so that I can correct meal types and fix any parsing errors before generating my report.

## Feature Metadata

- **Type**: New Capability
- **Complexity**: Medium
- **Systems Affected**: `src/pdf_parser.py` (new), `app/pages/1_Upload.py`, `app/pages/2_Review_Data.py`, `tests/test_pdf_parser.py` (new)
- **Dependencies**: pdfplumber (already in pyproject.toml), pandas (bundled with Streamlit)

---

## Mandatory Reading Before Implementation

| File | Why |
|------|-----|
| `src/models.py` | Exact field names/types for `GlucoseEntry`, `ExerciseEntry`, `MealType` enum |
| `src/storage.py` | `save_session`/`load_session` signatures and patterns |
| `app/Home.py` | Streamlit patterns, session state key (`current_session_id`) |
| `tests/test_storage.py` | Test patterns: class groupings, `tmp_path` fixtures, imports |
| `docs/samples/clarity_2026-02-18_to_2026-02-22.pdf` | The actual PDF to parse — ground truth for all parsing logic |
| `docs/samples/report_2026-02-18_to_2026-02-22.md` | Expected output format showing correct meal type assignments |

---

## PDF Format (Dexcom Clarity "Daily" View)

The sample PDF (11 pages, 14 days) uses `pdfplumber.extract_tables()`. Only `tables[0]` per page has useful data. Three row types after extraction:

| Row Type | Identification | Content |
|----------|---------------|---------|
| **Day Header** | 1 non-None value matching date regex | Contains "Sun, Feb 22, 2026" embedded in chart noise |
| **Data Row** | 6 non-None values (after filtering None) | `[time, "CGM", event_type, details, "--", "NNN mg/dL"]` |
| **Skip** | Everything else (blanks, footers) | Ignore |

**Event types:** `"Meal"` (food) and `"Walking"` (exercise)
**Date format in PDF:** `"Sun, Feb 22, 2026"` → convert to ISO `"2026-02-22"`
**Glucose format:** `"117 mg/dL"` → parse to int `117`
**Exercise details:** `"33 min • 88 BPM"` (U+2022 bullet) → parse duration and heart rate

---

## Implementation Plan

### Task 1: CREATE `src/pdf_parser.py`

Pure business logic, no UI dependencies.

**Constants/patterns:**
- `_DATE_PATTERN = re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\w{3}) (\d{1,2}), (\d{4})")`
- `_GLUCOSE_PATTERN = re.compile(r"^(\d+) mg/dL$")`
- `_EXERCISE_PATTERN = re.compile(r"^(\d+) min \u2022 (\d+) BPM$")`

**`ParseResult` dataclass:**
```python
@dataclass
class ParseResult:
    glucose_entries: list[GlucoseEntry]
    exercise_entries: list[ExerciseEntry]
    available_dates: list[str]   # sorted ascending ISO dates
    warnings: list[str]          # parse issues for UI display
```

**Private helpers:**
- `_parse_iso_date(match) -> str` — regex match to ISO date string
- `_classify_row(row) -> tuple[str, list[str]]` — returns `("header"|"data"|"skip", values)`
- `_parse_glucose_value(s) -> int | None` — strip "mg/dL", cast to int
- `_parse_exercise_details(s) -> tuple[int, int] | None` — parse duration and BPM

**Public functions:**
- `parse_pdf(pdf_path: Path) -> ParseResult` — main entry point. Iterates pages, processes `tables[0]`, tracks `current_date` from header rows, creates `GlucoseEntry` (with `meal_type=MealType.BREAKFAST` as default) and `ExerciseEntry` objects. Populates `available_dates` from all parsed entries.
- `filter_by_dates(result: ParseResult, selected_dates: list[str]) -> ParseResult` — returns new `ParseResult` filtered to selected dates only.

**Key decisions:**
- All "Meal" entries default to `MealType.BREAKFAST` — user corrects on Review page
- Unparseable rows generate warnings (never silently dropped)
- `available_dates` computed from actual parsed entries, not from header rows

**VALIDATE:** `uv run pytest tests/test_pdf_parser.py -v` (after Task 2)

---

### Task 2: CREATE `tests/test_pdf_parser.py`

Follow existing test patterns from `tests/test_storage.py`.

**Test classes:**

| Class | Tests |
|-------|-------|
| `TestClassifyRow` | Header detection, data row (meal + walking), blank/empty skip |
| `TestDateParsing` | ISO conversion, single-digit days, all day abbreviations, date embedded in noise |
| `TestGlucoseValueParsing` | 2-digit, 3-digit values, invalid inputs return None |
| `TestExerciseDetailsParsing` | Normal parse, single-digit values, non-matching strings |
| `TestParsePdf` | Integration tests with real sample PDF — entry counts, all meals default breakfast, glucose positive, known entries spot-checked (Feb 22 9:40 AM = 117 mg/dL egg omelette), exercise entries (33 min, 88 BPM), no warnings, expected date range |
| `TestFilterByDates` | Filters correctly, empty selection returns empty, warnings preserved, original not mutated |

**Fixture:** `@pytest.fixture(scope="module")` to parse the sample PDF once for all integration tests.

**VALIDATE:** `uv run pytest tests/test_pdf_parser.py -v` — all tests pass

---

### Task 3: UPDATE `app/pages/1_Upload.py`

Replace the stub. Thin UI layer calling `src/pdf_parser.py` and `src/storage.py`.

**Flow:**
1. Session guard — check `st.session_state["current_session_id"]`, show warning + `st.stop()` if missing
2. `st.file_uploader` for PDF (type=["pdf"])
3. On upload: save to `data/uploads/`, call `parse_pdf()`, cache result in `st.session_state["_upload_parse_result"]`
4. Show parse summary (entry counts, date range) and any warnings in expander
5. `st.multiselect` for date selection — default to last 5 complete dates (exclude today)
6. "Confirm and Continue" button: call `filter_by_dates()`, update session with entries/dates/filename, `save_session()`, `st.switch_page("pages/2_Review_Data.py")`

**Session state keys:**
- `_upload_parse_result` — cached ParseResult (avoids re-parsing on rerun)
- `_upload_filename` — tracks which file is currently parsed

**VALIDATE:** Manual — upload sample PDF, verify entry counts match expected data, select dates, confirm navigation works

---

### Task 4: UPDATE `app/pages/2_Review_Data.py`

Replace the stub. Editable table for glucose entries, read-only display for exercise.

**Flow:**
1. Session guard + load session from storage
2. If no glucose entries, show info message + link to Upload page
3. Build pandas DataFrame from `session.glucose_entries`
4. `st.data_editor` with column config:
   - `date`, `time` — disabled (read-only)
   - `food_item` — editable text
   - `meal_type` — `SelectboxColumn` with options `["breakfast", "lunch", "dinner", "snack"]`
   - `glucose_reading` — `NumberColumn` (min=1, max=600)
5. Exercise entries in separate `st.dataframe` (read-only)
6. "Save Corrections" button: rebuild `GlucoseEntry` list from edited DataFrame, validate with Pydantic, save session
7. "Continue to Mood Entry" button: `st.switch_page("pages/3_Mood_Entry.py")`

**Type handling:** `meal_type` comes back as `str` from data_editor — wrap with `MealType(str(...))`. `glucose_reading` may be `float` from pandas — wrap with `int()`.

**VALIDATE:** Manual — load Review page, verify table displays, change meal types, save, reload page to confirm persistence

---

## Verification

### Automated
```bash
uv run pytest tests/test_pdf_parser.py -v    # Parser tests
uv run pytest -v                              # Full test suite (no regressions)
uv run mypy src/                              # Type checking
```

### Manual
1. `uv run streamlit run app/Home.py`
2. Create a new session on Home page
3. Navigate to Upload → upload `docs/samples/clarity_2026-02-18_to_2026-02-22.pdf`
4. Verify: 22 meal entries, 3 exercise entries across 14 dates
5. Select Feb 18-22 → confirm → verify navigation to Review page
6. On Review page: change meal types for Feb 22 entries, save
7. Reload page — verify corrections persisted

### Expected Data (Feb 18-22)
- **Feb 22:** 4 meals + 1 exercise (first meal 9:40 AM, 117 mg/dL, egg omelette)
- **Feb 21:** 4 meals
- **Feb 20:** 4 meals + 1 exercise
- **Feb 19:** 4 meals + 1 exercise
- **Feb 18:** 4 meals
- **Total:** 20 meal entries, 3 exercise entries for the 5-day range

---

## Acceptance Criteria

- [ ] `src/pdf_parser.py` correctly parses the sample Clarity PDF
- [ ] All parser tests pass (`tests/test_pdf_parser.py`)
- [ ] Upload page accepts PDF, shows parsed data summary, allows date selection
- [ ] Review page displays editable glucose table with meal type dropdowns
- [ ] Meal type corrections persist after save
- [ ] Exercise entries displayed (read-only)
- [ ] No regressions — full test suite passes
- [ ] `mypy src/` passes clean
- [ ] Parse warnings surface in UI (never silently drop data)
