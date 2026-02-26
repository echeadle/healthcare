# E2E Test Report — Healthcare Report Assistant

**Date:** 2026-02-25
**Tester:** Claude Code (automated)
**App Version:** Phase 2 (commit `4ff1555`)
**Browser:** Chromium (via agent-browser 0.15.0)

---

## Summary

| Metric | Value |
|--------|-------|
| Journeys Tested | 6 |
| Screenshots Captured | 28 |
| Issues Found (code analysis) | 8 |
| Issues Fixed During Testing | 5 |
| Remaining Issues | 3 |
| Test Suite Status | 62/62 passing |

---

## Journey 1: Session Creation (Home Page)

**Task:** Create a new session with name, start date, and end date.

### Steps Executed

1. Navigated to `http://localhost:8501/`
2. Verified page renders with title, description, form, and Existing Sessions list
3. Filled "Session name" with "E2E Test Week"
4. Set Start date to 2026/02/18
5. Set End date to 2026/02/22
6. Clicked "Start New Session"
7. Verified session JSON file created at `data/sessions/<uuid>.json`
8. Scrolled down — verified session appears in Existing Sessions list with "draft" status

### Screenshots

| Screenshot | Description |
|------------|-------------|
| `e2e-screenshots/00-initial-load.png` | Initial app load — Home page with form and sidebar |
| `e2e-screenshots/home/01-form-filled.png` | Form filled with session name and dates |
| `e2e-screenshots/home/02-session-created.png` | Page after form submit (success message missing — bug) |
| `e2e-screenshots/home/02b-full-page.png` | Full page view after submit |
| `e2e-screenshots/home/03-scrolled-down.png` | Existing Sessions list showing new session with "draft" status |
| `e2e-screenshots/home/04-success-message.png` | After fix: success message now visible |

### Data Validation

```json
{
  "id": "c06fdf1d-d874-4114-ba92-aeb310fe80f4",
  "name": "E2E Test Week",
  "created_at": "2026-02-26T01:45:08.081249+00:00",
  "date_range_start": "2026-02-18",
  "date_range_end": "2026-02-22",
  "selected_dates": [],
  "glucose_entries": [],
  "exercise_entries": [],
  "mood_entries": [],
  "status": "draft",
  "source_filename": ""
}
```

Verified: UUID4 format, correct name, correct dates, empty entry lists, status "draft".

### Issues Found & Fixed

**Issue: Success message invisible after session creation**
- **Severity:** Medium (UX)
- **File:** `app/Home.py:40-41`
- **Problem:** `st.success()` at line 40 was immediately cleared by `st.rerun()` at line 41. The user never saw confirmation that the session was created.
- **Fix:** Used a `st.session_state["_session_created"]` flag that survives the rerun, then display the success message on the next render cycle.
- **Verified:** Re-tested — success message now displays correctly.

**Issue: No date range validation**
- **Severity:** Medium (data integrity)
- **File:** `app/Home.py:31`
- **Problem:** Users could create sessions with end date before start date with no error.
- **Fix:** Added `if date_end < date_start: st.error(...)` validation before session creation.

---

## Journey 2: PDF Upload and Date Selection

**Task:** Upload a Dexcom Clarity PDF, review parse results, select dates, and confirm.

### Steps Executed

1. Navigated to Upload page via sidebar
2. Verified session guard displays "Session: E2E Upload Test"
3. Uploaded sample PDF `docs/samples/clarity_2026-02-18_to_2026-02-22.pdf` (332.7KB)
4. Verified parse summary: 64 Meal Entries, 5 Exercise Entries, 14 Days Found
5. Verified date range caption: "2026-02-10 to 2026-02-23"
6. Verified date multi-select defaults to 5 dates (2026-02-18 through 2026-02-22)
7. Verified live caption: "Selected: 20 meals, 3 exercises across 5 days"
8. Clicked "Confirm and Continue"
9. Verified auto-navigation to Review Data page
10. Verified session JSON updated with 20 glucose entries, 3 exercise entries

### Screenshots

| Screenshot | Description |
|------------|-------------|
| `e2e-screenshots/upload/01-upload-page.png` | Upload page before file selection — shows session guard error (stale session) |
| `e2e-screenshots/upload/02-error-handled.png` | FileNotFoundError shown as friendly message after fix |
| `e2e-screenshots/upload/03-upload-page-ready.png` | Upload page with active session and file uploader |
| `e2e-screenshots/upload/04-upload-after-reload.png` | Session guard: "No active session" warning on page reload |
| `e2e-screenshots/upload/05-pdf-parsed.png` | Parse summary with metrics (64 meals, 5 exercises, 14 days) |
| `e2e-screenshots/upload/06-date-selection.png` | Date selection and metrics visible |
| `e2e-screenshots/upload/07-date-selection-full.png` | Full date multi-select with 5 dates and "Confirm and Continue" button |
| `e2e-screenshots/upload/08-navigated-to-review.png` | Auto-navigated to Review Data page with 20 glucose entries |

### Data Validation

```
Upload Flow Test - glucose: 20 - exercise: 3 - dates: ['2026-02-18', '2026-02-19', '2026-02-20', '2026-02-21', '2026-02-22']
source_filename: clarity_2026-02-18_to_2026-02-22.pdf
date_range_start: 2026-02-18
date_range_end: 2026-02-22
```

Verified: glucose and exercise counts match UI, dates correctly filtered, source filename saved.

### Issues Found & Fixed

**Issue: Unhandled FileNotFoundError on Upload page**
- **Severity:** Critical (crash)
- **File:** `app/pages/1_Upload.py:18`
- **Problem:** `load_session(session_id)` raised raw `FileNotFoundError` traceback when session file was missing (e.g., deleted or session state pointing to stale ID).
- **Fix:** Wrapped in `try/except FileNotFoundError` with friendly `st.error()` message and `st.stop()`.
- **Verified:** Page now shows "Session file not found. Please return to the Home page and create a new session."

**Issue: Path traversal vulnerability in file upload**
- **Severity:** Critical (security)
- **File:** `app/pages/1_Upload.py:29-30`
- **Problem:** `uploaded_file.name` was used directly in path construction. A filename like `../../app/Home.py` could write outside `data/uploads/`.
- **Fix:** Added `PurePosixPath(uploaded_file.name).name` to strip directory components.

---

## Journey 3: Data Review and Correction

**Task:** Review extracted glucose data, edit entries, save corrections, and navigate forward.

### Steps Executed

1. Verified Review Data page renders with session info header
2. Verified "Glucose Entries (20)" editable data table with columns: Date, Time, Food Item, Meal Type, Glucose (mg/dL)
3. Verified all meal types default to "breakfast" (expected — primary correction task for users)
4. Attempted cell editing in the canvas-based data editor (glide-data-grid renders on canvas, limiting automated interaction)
5. Scrolled to Exercise Entries (3) — verified read-only table with date, time, activity, duration, heart rate, glucose
6. Clicked "Save Corrections" — verified "Corrections saved!" success message
7. Clicked "Continue to Mood Entry" — verified navigation to Mood Entry stub page
8. Checked browser console — only Streamlit theme warnings, no JS errors
9. Checked uncaught exceptions — none

### Screenshots

| Screenshot | Description |
|------------|-------------|
| `e2e-screenshots/review/01-annotated.png` | Annotated Review page with element labels |
| `e2e-screenshots/review/02-cell-click.png` | After attempting cell selection in data editor |
| `e2e-screenshots/review/03-after-click.png` | Cell selected (red border) in Glucose column |
| `e2e-screenshots/review/04-buttons-visible.png` | Full glucose table with all columns visible |
| `e2e-screenshots/review/05-exercise-and-buttons.png` | Exercise Entries table and Save/Continue buttons |
| `e2e-screenshots/review/06-save-button.png` | Exercise table and both action buttons visible |
| `e2e-screenshots/review/07-save-result.png` | "Corrections saved!" success message displayed |
| `e2e-screenshots/review/08-navigated-to-mood.png` | Successfully navigated to Mood Entry stub |

### Issues Found & Fixed

**Issue: Unhandled FileNotFoundError on Review Data page**
- **Severity:** Critical (crash)
- **File:** `app/pages/2_Review_Data.py:17`
- **Problem:** Same as Upload page — `load_session()` raised raw traceback.
- **Fix:** Wrapped in `try/except FileNotFoundError` with friendly error message.

**Issue: "Continue to Mood Entry" navigates without saving unsaved changes**
- **Severity:** Medium (data loss)
- **File:** `app/pages/2_Review_Data.py:105-107`
- **Problem:** If user edits the data table and clicks "Continue" without clicking "Save Corrections" first, all edits are silently discarded.
- **Fix:** Added `df.equals(edited_df)` check — if data differs, shows warning "You have unsaved changes. Please click 'Save Corrections' first." instead of navigating.
- **Note:** Due to glide-data-grid's canvas-based rendering, full E2E validation of this fix was limited.

### Testing Limitation

The Streamlit `st.data_editor` uses glide-data-grid which renders entirely on an HTML canvas element. This means:
- Individual cells cannot be targeted by CSS selectors
- Standard click/fill browser automation commands don't work on grid cells
- Full cell-editing E2E testing requires coordinate-based mouse events, which are fragile

**Recommendation:** For thorough data editor testing, consider integration tests that directly call the Pydantic validation logic in `src/models.py` (already covered by 62 existing unit tests).

---

## Journey 4: Stub Pages

**Task:** Verify all placeholder pages render correctly.

### Steps Executed

1. Navigated to Mood Entry — verified title, info message, and "Coming in Phase 3." text
2. Navigated to AI Chat — verified title, info message, and "Coming in Phase 4." text
3. Navigated to Generate Report — verified title, info message, and "Coming in Phase 3." text

### Screenshots

| Screenshot | Description |
|------------|-------------|
| `e2e-screenshots/stubs/01-mood-entry.png` | Mood Entry stub page |
| `e2e-screenshots/stubs/02-chat.png` | AI Chat stub page |
| `e2e-screenshots/stubs/03-generate-report.png` | Generate Report stub page |

### Issues Found

None. All stubs render correctly with appropriate placeholder messages.

---

## Journey 5: Session Guards

**Task:** Verify pages with session-dependent content handle missing sessions gracefully.

### Steps Executed

1. Reloaded Upload page directly (clearing session state) — verified "No active session" warning displayed
2. The FileNotFoundError fix (from Journey 2) also addresses the case where `session_id` is in state but the file is deleted

### Screenshots

| Screenshot | Description |
|------------|-------------|
| `e2e-screenshots/upload/04-upload-after-reload.png` | "No active session. Please create one on the Home page first." |
| `e2e-screenshots/upload/02-error-handled.png` | "Session file not found" error (after fix) |

### Issues Found

Session guards work correctly after fixes. Both the "no session in state" and "session file missing" cases are now handled gracefully.

---

## Journey 6: Responsive Testing

**Task:** Verify layout at mobile (375x812), tablet (768x1024), and desktop (1440x900) viewports.

### Steps Executed

1. Set viewport to 375x812 (mobile) — screenshotted Home page
2. Set viewport to 768x1024 (tablet) — screenshotted Home page
3. Set viewport to 1440x900 (desktop) — screenshotted Home page

### Screenshots

| Screenshot | Description |
|------------|-------------|
| `e2e-screenshots/responsive/01-home-mobile.png` | Mobile: stacked layout, full-width inputs, collapsed sidebar |
| `e2e-screenshots/responsive/02-home-tablet.png` | Tablet: side-by-side dates, collapsed sidebar, sessions list visible |
| `e2e-screenshots/responsive/03-home-desktop.png` | Desktop: full sidebar, wide layout, all content visible |

### Findings

- **Mobile (375x812):** Layout adapts well. Title wraps correctly. Form fields stack vertically. Date inputs are full-width. Sidebar collapses to hamburger icon. Touch targets are appropriately sized.
- **Tablet (768x1024):** Good intermediate layout. Date inputs are side-by-side. Existing Sessions list displays correctly with 3-column layout.
- **Desktop (1440x900):** Full sidebar visible. Wide layout with plenty of space. All content visible without scrolling.

**No responsive issues found.** Streamlit's default responsive behavior handles all viewports well.

---

## All Issues Summary

### Fixed During Testing (5)

| # | Severity | Issue | File | Fix |
|---|----------|-------|------|-----|
| 1 | Critical | Path traversal in upload filename | `app/pages/1_Upload.py:29-30` | Sanitize with `PurePosixPath.name` |
| 2 | Critical | Unhandled FileNotFoundError on Upload page | `app/pages/1_Upload.py:18` | `try/except` with `st.error()` |
| 3 | Critical | Unhandled FileNotFoundError on Review page | `app/pages/2_Review_Data.py:17` | `try/except` with `st.error()` |
| 4 | Medium | Success message cleared by rerun | `app/Home.py:40-41` | Session state flag pattern |
| 5 | Medium | No date range validation | `app/Home.py:31` | `date_end < date_start` check |

### Partially Fixed (1)

| # | Severity | Issue | File | Status |
|---|----------|-------|------|--------|
| 6 | Medium | Silent data loss on Continue without Save | `app/pages/2_Review_Data.py:105-107` | Added `df.equals()` check + warning. Canvas-based editor limits full E2E validation. |

### Remaining (from code analysis, not fixed)

| # | Severity | Issue | File | Notes |
|---|----------|-------|------|-------|
| 7 | Medium | Footer rows can corrupt `current_date` in PDF parser | `src/pdf_parser.py:53-58` | Footer lines with dates (e.g., "Data uploaded: Mon, Feb 23") are classified as date headers. Could mislabel entries in multi-page PDFs. Fix: check for `FOOTER_KEYWORDS` before classifying as header. |
| 8 | Low | Relative default path in storage.py | `src/storage.py:8` | `Path("data/sessions")` resolves relative to CWD. Works when run from project root but breaks otherwise. Fix: anchor to `__file__` parent. |
| 9 | Low | `filter_by_dates` called twice redundantly | `app/pages/1_Upload.py:83,92` | Called once for display caption and again inside button handler. Not a bug but unnecessary duplication. |
| 10 | Low | Bare `[]` defaults on Pydantic list fields | `src/models.py:86-88` | Pydantic v2 handles this correctly, but `Field(default_factory=list)` is more explicit. |

---

## Console & Error Log

- **JavaScript errors:** None
- **Uncaught exceptions:** None
- **Console warnings:** Streamlit theme-related warnings only (`Invalid color passed for primaryColor in theme.sidebar: ""` — repeated). These are cosmetic framework warnings, not application bugs.

---

## Test Suite Verification

After all code changes, the full test suite passes:

```
tests/test_models.py .................                   [ 27%]
tests/test_pdf_parser.py ..................................  [ 82%]
tests/test_storage.py ...........                        [100%]

62 passed in 3.03s
```

---

## Files Modified

| File | Changes |
|------|---------|
| `app/Home.py` | Added date validation, fixed success message persistence |
| `app/pages/1_Upload.py` | Added FileNotFoundError handling, path traversal fix |
| `app/pages/2_Review_Data.py` | Added FileNotFoundError handling, unsaved changes warning |

---

## Recommendations

1. **PDF parser footer handling** (issue #7) should be addressed before processing PDFs from different Dexcom report formats, as mislabeled dates would produce incorrect health data.
2. **Session resume** — The Home page lists existing sessions but provides no way to click into one. Adding a "Resume" button per session row would significantly improve usability.
3. **Data editor testing** — Consider adding integration tests that directly exercise the `GlucoseEntry` validation and `save_session` round-trip for edited data, since the canvas-based UI is difficult to automate.
4. **Anchor storage paths** (issue #8) to `__file__` to make the app runnable from any working directory.
