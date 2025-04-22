import pandas as pd
import json
import streamlit as st
from datetime import datetime
import os

SYSTEM_VERSION = "v2.0.2"

def flatten_response_for_xlsx(response):
    base = {
        "Student_ID": response.get("Student_ID", "unknown"),
        "Answer_Text": response["Answer_Text"],
        "Total_Final_Score": response["Total_Final_Score"]
    }

    for point in response["Mark_Points"]:
        label = point["Label"]
        base[f"{label}_Score"] = point.get("Awarded_Score", "")
        base[f"{label}_Rationale"] = point.get("Rationale", "")
        base[f"{label}_Override_Tag"] = point.get("Override_Tag", "")
    
    base["Feedback"] = response.get("Feedback", "")
    base["Export_Timestamp"] = datetime.now().isoformat()
    base["System_Version"] = SYSTEM_VERSION
    return base

def export_to_xlsx(responses, filename):
    rows = [flatten_response_for_xlsx(r) for r in responses]
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)

def export_to_training_log_json(override_logs, filename):
    timestamp = datetime.now().isoformat()
    new_entry = {
        "Export_Timestamp": timestamp,
        "System_Version": SYSTEM_VERSION,
        "Overrides": override_logs
    }

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_data = json.load(f)
        if isinstance(existing_data, list):
            merged_data = existing_data + [new_entry]
        else:
            merged_data = [existing_data, new_entry]
    else:
        merged_data = [new_entry]

    with open(filename, 'w') as f:
        json.dump(merged_data, f, indent=2)

def provide_download_buttons(xlsx_filename, json_filename):
    with open(xlsx_filename, "rb") as xlsx_file:
        st.download_button(
            label="Download Teacher Export (.xlsx)",
            data=xlsx_file,
            file_name=xlsx_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with open(json_filename, "rb") as json_file:
        st.download_button(
            label="Download Training Log (.json)",
            data=json_file,
            file_name=json_filename,
            mime="application/json"
        )

def run_export_engine(responses, override_logs):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    xlsx_filename = f"export_{timestamp}_{SYSTEM_VERSION}.xlsx"
    json_filename = "training_log.json"

    export_to_xlsx(responses, xlsx_filename)
    export_to_training_log_json(override_logs, json_filename)
    provide_download_buttons(xlsx_filename, json_filename)
