import pandas as pd
import streamlit as st

from src.models import GlucoseEntry, MealType
from src.storage import load_session, save_session

st.set_page_config(page_title="Review & Correct Data", layout="wide")

st.title("Review & Correct Data")

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

st.info(f"Session: **{session.name}** ({session.date_range_start} to {session.date_range_end})")

# --- No data guard ---
if not session.glucose_entries:
    st.info("No glucose data found. Please upload a PDF on the Upload page first.")
    st.stop()

# --- Glucose entries table ---
st.subheader(f"Glucose Entries ({len(session.glucose_entries)})")

# Build DataFrame from entries
glucose_data = [
    {
        "date": e.date,
        "time": e.time,
        "food_item": e.food_item,
        "meal_type": e.meal_type.value,
        "glucose_reading": e.glucose_reading,
    }
    for e in session.glucose_entries
]
df = pd.DataFrame(glucose_data)

meal_type_options = [mt.value for mt in MealType]

edited_df = st.data_editor(
    df,
    column_config={
        "date": st.column_config.TextColumn("Date", disabled=True),
        "time": st.column_config.TextColumn("Time", disabled=True),
        "food_item": st.column_config.TextColumn("Food Item", width="large"),
        "meal_type": st.column_config.SelectboxColumn(
            "Meal Type",
            options=meal_type_options,
            required=True,
        ),
        "glucose_reading": st.column_config.NumberColumn(
            "Glucose (mg/dL)",
            min_value=1,
            max_value=600,
        ),
    },
    use_container_width=True,
    num_rows="fixed",
    key="glucose_editor",
)

# --- Exercise entries (read-only) ---
if session.exercise_entries:
    st.subheader(f"Exercise Entries ({len(session.exercise_entries)})")
    exercise_data = [
        {
            "date": e.date,
            "time": e.time,
            "activity": e.activity_type,
            "duration (min)": e.duration_minutes,
            "heart rate (BPM)": e.heart_rate_bpm,
            "glucose (mg/dL)": e.glucose_reading,
        }
        for e in session.exercise_entries
    ]
    st.dataframe(pd.DataFrame(exercise_data), use_container_width=True)

# --- Save corrections ---
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("Save Corrections", type="primary"):
        try:
            updated_entries = []
            for _, row in edited_df.iterrows():
                entry = GlucoseEntry(
                    date=str(row["date"]),
                    time=str(row["time"]),
                    glucose_reading=int(row["glucose_reading"]),
                    food_item=str(row["food_item"]),
                    meal_type=MealType(str(row["meal_type"])),
                )
                updated_entries.append(entry)
            session.glucose_entries = updated_entries
            save_session(session)
            st.success("Corrections saved!")
        except Exception as e:
            st.error(f"Validation error: {e}")

with col2:
    if st.button("Continue to Mood Entry"):
        if not df.equals(edited_df):
            st.warning("You have unsaved changes. Please click 'Save Corrections' first.")
        else:
            st.switch_page("pages/3_Mood_Entry.py")
