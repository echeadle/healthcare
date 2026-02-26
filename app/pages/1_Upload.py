from pathlib import Path, PurePosixPath

import streamlit as st

from src.pdf_parser import filter_by_dates, parse_pdf
from src.storage import load_session, save_session

st.set_page_config(page_title="Upload Glucose PDF", layout="wide")

st.title("Upload Glucose PDF")

# --- Session guard ---
if "current_session_id" not in st.session_state:
    st.warning("No active session. Please create one on the Home page first.")
    st.stop()

session_id = st.session_state["current_session_id"]
try:
    session = load_session(session_id)
except FileNotFoundError:
    st.error("Session file not found. Please return to the Home page and create a new session.")
    st.stop()

st.info(f"Session: **{session.name}**")

# --- File uploader ---
uploaded_file = st.file_uploader("Upload your Dexcom Clarity PDF", type=["pdf"])

if uploaded_file is not None:
    # Save uploaded file to data/uploads/
    uploads_dir = Path("data/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_name = PurePosixPath(uploaded_file.name).name
    pdf_path = uploads_dir / safe_name
    pdf_path.write_bytes(uploaded_file.getvalue())

    # Parse PDF (cache result to avoid re-parsing on rerun)
    current_filename = uploaded_file.name
    if (
        st.session_state.get("_upload_filename") != current_filename
        or "_upload_parse_result" not in st.session_state
    ):
        with st.spinner("Parsing PDF..."):
            result = parse_pdf(pdf_path)
        st.session_state["_upload_parse_result"] = result
        st.session_state["_upload_filename"] = current_filename
    else:
        result = st.session_state["_upload_parse_result"]

    # --- Parse summary ---
    st.subheader("Parse Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Meal Entries", len(result.glucose_entries))
    with col2:
        st.metric("Exercise Entries", len(result.exercise_entries))
    with col3:
        st.metric("Days Found", len(result.available_dates))

    if result.available_dates:
        st.caption(
            f"Date range: {result.available_dates[0]} to {result.available_dates[-1]}"
        )

    # --- Warnings ---
    if result.warnings:
        with st.expander(f"Parse Warnings ({len(result.warnings)})", expanded=True):
            for warning in result.warnings:
                st.warning(warning)

    # --- Date selection ---
    st.subheader("Select Dates for Report")
    # Default to last 5 dates (most recent, excluding the very last which may be today/incomplete)
    available = result.available_dates
    if len(available) > 5:
        # Skip the most recent (potentially incomplete), take the 5 before it
        default_dates = available[-6:-1]
    else:
        default_dates = available

    selected_dates = st.multiselect(
        "Choose which dates to include in your report",
        options=available,
        default=default_dates,
    )

    if selected_dates:
        filtered = filter_by_dates(result, selected_dates)
        st.caption(
            f"Selected: {len(filtered.glucose_entries)} meals, "
            f"{len(filtered.exercise_entries)} exercises across {len(selected_dates)} days"
        )

    # --- Confirm and continue ---
    st.divider()
    if st.button("Confirm and Continue", type="primary", disabled=not selected_dates):
        filtered = filter_by_dates(result, selected_dates)
        session.glucose_entries = filtered.glucose_entries
        session.exercise_entries = filtered.exercise_entries
        session.selected_dates = sorted(selected_dates)
        session.source_filename = current_filename
        if selected_dates:
            session.date_range_start = sorted(selected_dates)[0]
            session.date_range_end = sorted(selected_dates)[-1]
        save_session(session)
        st.success("Data saved! Navigating to Review page...")
        st.switch_page("pages/2_Review_Data.py")
