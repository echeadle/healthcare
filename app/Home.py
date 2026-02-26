import streamlit as st
from dotenv import load_dotenv

from src.models import ReportSession
from src.storage import list_sessions, save_session

load_dotenv()

st.set_page_config(page_title="Healthcare Report Assistant", layout="wide")

st.title("Healthcare Report Assistant")
st.markdown(
    "Upload your glucose monitoring PDF, review and correct the data, "
    "enter mood information, and generate your advisor report."
)

st.divider()

# --- Start New Session ---
st.subheader("Start a New Session")

with st.form("new_session_form"):
    session_name = st.text_input("Session name", placeholder="e.g., Week of Feb 18")
    col1, col2 = st.columns(2)
    with col1:
        date_start = st.date_input("Start date")
    with col2:
        date_end = st.date_input("End date")
    submitted = st.form_submit_button("Start New Session")

if submitted and session_name:
    if date_end < date_start:
        st.error("End date must be on or after start date.")
    else:
        session = ReportSession.create_new(
            name=session_name,
            date_range_start=str(date_start),
            date_range_end=str(date_end),
            selected_dates=[],
        )
        save_session(session)
        st.session_state["current_session_id"] = session.id
        st.session_state["_session_created"] = session_name
        st.rerun()

if st.session_state.pop("_session_created", None):
    st.success(f"Session created! Navigate to Upload to continue.")

st.divider()

# --- Existing Sessions ---
st.subheader("Existing Sessions")

sessions = list_sessions()
if sessions:
    for s in sessions:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown(f"**{s['name']}**")
        with col2:
            st.caption(f"{s['date_range_start']} to {s['date_range_end']}")
        with col3:
            status_color = "green" if s["status"] == "finalized" else "orange"
            st.markdown(f":{status_color}[{s['status']}]")
else:
    st.info("No sessions yet. Create one above to get started.")
