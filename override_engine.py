
from datetime import datetime
import copy
from typing import List, Tuple

def apply_teacher_override(student_response: dict, teacher_override: dict, version: str = "v2.0.2") -> Tuple[dict, dict]:
    """
    Applies teacher overrides to a student response.
    Returns the updated response and a structured override log.
    """
    updated_response = copy.deepcopy(student_response)
    override_log = {
        "Student_ID": student_response.get("Student_ID", "unknown"),
        "Answer_Text": student_response["Answer_Text"],
        "Assistant_Version": version,
        "Overrides": [],
        "Total_Possible_Score": student_response.get("Total_Possible_Score", 0),
        "Final_Score": 0,
        "Student_Feedback": []
    }

    total_score = 0
    for point in updated_response["Mark_Points"]:
        label = point["Label"]
        original_score = point.get("Awarded_Score", 0)

        if label in teacher_override:
            tag = teacher_override[label].get("Override_Tag", "")
            comment = teacher_override[label].get("Comment", "")

            # Apply override logic
            if tag.lower() in ["misconception", "nullify"]:
                adjusted_score = 0
                feedback = "Your idea was scientifically incorrect."
            elif tag.lower() == "clarity-tolerated":
                adjusted_score = original_score
                feedback = "Your answer was valid but not clearly phrased."
            else:
                adjusted_score = original_score
                feedback = "Your response was overridden by the teacher."

            # Update point
            point["Override_Tag"] = tag
            point["Override_Comment"] = comment
            point["Awarded_Score"] = adjusted_score

            # Log override
            override_log["Overrides"].append({
                "Label": label,
                "Override_Tag": tag,
                "Comment": comment,
                "Original_Score": original_score,
                "Adjusted_Score": adjusted_score
            })

            override_log["Student_Feedback"].append(f"{label}: {feedback}")
            total_score += adjusted_score
        else:
            total_score += original_score

    updated_response["Total_Final_Score"] = total_score
    override_log["Final_Score"] = total_score

    return updated_response, override_log


def batch_apply_teacher_overrides(responses: List[dict], overrides: List[dict], version: str = "v2.0.2") -> Tuple[List[dict], List[dict]]:
    """
    Apply teacher overrides to a batch of student responses.
    
    responses: list of student_response dicts (from matching_logic)
    overrides: list of teacher_override dicts, one per student (matched by index)
    
    Returns:
    - List of updated student responses
    - List of override logs
    """
    updated_responses = []
    override_logs = []
    
    for response, override in zip(responses, overrides):
        updated, log = apply_teacher_override(response, override, version)
        updated_responses.append(updated)
        override_logs.append(log)
        
    return updated_responses, override_logs
