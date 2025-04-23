import streamlit as st
import pandas as pd
import json
import uuid
from matching_logic_v1 import updated_matching_logic
from override_engine import apply_teacher_override, batch_apply_teacher_overrides
from export_engine import run_export_engine

st.set_page_config(layout="wide")
st.title("🧠 Mr Low's AI Science Marking Assistant v2.2")

if 'mark_scheme' not in st.session_state:
    st.session_state.mark_scheme = {}
if 'student_responses' not in st.session_state:
    st.session_state.student_responses = []
if 'final_responses' not in st.session_state:
    st.session_state.final_responses = []
if 'override_logs' not in st.session_state:
    st.session_state.override_logs = []

st.sidebar.button("🔄 Clear session", on_click=lambda: st.session_state.clear())

# MARK SCHEME PANEL
st.header("1️⃣ Mark Scheme Entry")
st.markdown("Enter key concepts for P1 to P4. OR logic is default and supports alternative phrases.")

points = ['P1', 'P2', 'P3', 'P4']
for point in points:
    if point == 'P1' or st.checkbox(f"Enable {point}"):
        with st.container():
            cols = st.columns([3, 1])
            phrase = cols[0].text_input(f"{point} Key Phrase")
            max_score = cols[1].selectbox(f"{point} Score", [0.5, 1.0], key=f"score_{point}")

        conditions = [{'phrase': phrase, 'similarity': None}] if phrase else []
        if st.checkbox(f"Add alternative phrase for {point}"):
            alt_phrase = st.text_input(f"Alternative phrase for {point}")
            if alt_phrase:
                conditions.append({'phrase': alt_phrase, 'similarity': None})

        st.session_state.mark_scheme[point] = {
            'conditions': conditions,
            'logic': 'OR',
            'threshold': 0.85,
            'penalties': [],
            'override_tag': '',
            'max_score': max_score
        }

        if st.checkbox(f"Add penalty for {point}"):
            penalty_phrase = st.text_input(f"Penalty Phrase for {point}")
            deduction = st.selectbox(f"Penalty Deduction for {point}", [0.25, 0.5], key=f"penalty_{point}")
            st.session_state.mark_scheme[point]['penalties'].append({'reason': penalty_phrase, 'deduction': deduction})

        if st.checkbox(f"Nullify if matched for {point}"):
            st.session_state.mark_scheme[point]['override_tag'] = 'Nullify'

# STUDENT RESPONSE PANEL
st.header("2️⃣ Student Response Entry")
response_mode = st.radio("Select Input Mode", ["Manual Entry", "Batch Upload"])

if response_mode == "Manual Entry":
    student_text = st.text_area("Student Response")
    if st.button("Run Marking"):
        student_id = f"RSP_{uuid.uuid4().hex[:8]}"
        temp_input = {
            'Student_ID': student_id,
            'Answer_Text': student_text,
            'Mark_Points': [
                {**details, "Label": label} for label, details in st.session_state.mark_scheme.items()
            ]
        }
        result = updated_matching_logic(temp_input, st.session_state.mark_scheme)
        st.session_state.student_responses = [result]
        st.session_state.final_responses = st.session_state.student_responses.copy()
        st.success("Marking completed.")

elif response_mode == "Batch Upload":
    st.markdown("**Upload `.xlsx` with columns: Student_ID, Answer_Text**")
    file = st.file_uploader("Upload File", type=["xlsx"])
    if file and st.button("Run Marking"):
        df = pd.read_excel(file)
        responses = []
        for _, row in df.iterrows():
            ans = {
                "Student_ID": row["Student_ID"],
                "Answer_Text": row["Answer_Text"],
                "Mark_Points": [
                    {**details, "Label": label} for label, details in st.session_state.mark_scheme.items()
                ]
            }
            res = updated_matching_logic(ans, st.session_state.mark_scheme)
            res["Student_ID"] = row["Student_ID"]
            responses.append(res)
        st.session_state.student_responses = responses
        st.session_state.final_responses = responses.copy()
        st.success("Batch marking completed.")

# SCORE PANEL (live view)
st.header("3️⃣ Score")
if st.session_state.final_responses:
    for res in st.session_state.final_responses:
        st.subheader(f"Student ID: {res.get('Student_ID', 'unknown')}")
        st.text_area("Answer", res["Answer_Text"], height=100)
        for pt in res["Mark_Points"]:
            st.markdown(f"**{pt['Label']}** — Score: {pt['Awarded_Score']}, Tag: {pt.get('Override_Tag', '')}\n\n*Rationale*: {pt['Rationale']}")
        st.markdown(f"**Total Score**: {res['Total_Final_Score']}")

# TEACHER OVERRIDE PANEL (optional)
if st.checkbox("✏️ Enable Teacher Overrides"):
    st.header("4️⃣ Teacher Overrides")
    st.markdown("Tag and comment per point if necessary.")
    overrides = []
    for response in st.session_state.student_responses:
        override_dict = {}
        st.subheader(f"Student ID: {response.get('Student_ID', 'unknown')}")
        for pt in response['Mark_Points']:
            tag = st.selectbox(f"Override Tag for {pt['Label']} ({pt['Rationale']})", ["", "Clarity-tolerated", "Misconception", "Context Error"], key=f"tag_{response['Answer_Text']}_{pt['Label']}")
            comment = st.text_input(f"Comment for {pt['Label']}", key=f"comment_{response['Answer_Text']}_{pt['Label']}")
            override_dict[pt['Label']] = {"Override_Tag": tag, "Comment": comment}
        overrides.append(override_dict)

    if st.button("Apply Overrides"):
        final, logs = batch_apply_teacher_overrides(st.session_state.student_responses, overrides)
        st.session_state.final_responses = final
        st.session_state.override_logs = logs
        st.success("Overrides applied. Score view updated.")

# EXPORT PANEL
st.header("5️⃣ Export Files")
if st.session_state.final_responses:
    override_logs = st.session_state.override_logs if 'override_logs' in st.session_state else []
    run_export_engine(st.session_state.final_responses, override_logs)
