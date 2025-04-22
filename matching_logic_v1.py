
from typing import Dict, List

def evaluate_conditions(conditions: List[Dict], student_text: str, threshold: float) -> List[Dict]:
    """Evaluates each condition using a placeholder similarity metric."""
    results = []
    for condition in conditions:
        phrase = condition["phrase"]
        # Placeholder similarity logic: exact substring match = 1.0, else 0.0
        similarity = 1.0 if phrase.lower() in student_text.lower() else 0.0
        condition["similarity"] = similarity
        condition["matched"] = similarity >= threshold
        results.append(condition)
    return results

def updated_matching_logic(answer: Dict, matching_rules: Dict) -> Dict:
    output_points = []
    needs_review = False
    matched_labels = []
    nullify_triggered = False
    penalty_log = []

    student_text = answer["Answer_Text"]

    for point in answer["Mark_Points"]:
        label = point["Label"]
        predicted_sim = point.get("Predicted_Similarity", 0.0)  # Default to 0.0 if not included
        rule = matching_rules.get(label, {})
        
        logic_type = rule.get("logic", "AND")
        threshold = rule.get("threshold", 0.85)
        max_score = rule.get("max_score", 1.0)
        override_tag = rule.get("override_tag", "")
        conditions = rule.get("conditions", [])
        penalties = rule.get("penalties", [])

        evaluated_conditions = evaluate_conditions(conditions, student_text, threshold)
        condition_matches = [c["matched"] for c in evaluated_conditions]

        if logic_type == "AND":
            matched = all(condition_matches)
        elif logic_type == "OR":
            matched = any(condition_matches)
        else:
            matched = predicted_sim >= threshold

        rationale_parts = []
        for i, c in enumerate(evaluated_conditions):
            status = "Matched" if c["matched"] else "Not matched"
            rationale_parts.append(f"{status} P{label}.{i+1} (sim={c['similarity']:.2f})")

        awarded_score = max_score if matched else 0
        rationale = "; ".join(rationale_parts)
        flagged_for_teacher = False

        # Penalty logic (stubbed for flat deductions)
        penalty_total = 0
        for penalty in penalties:
            penalty_value = penalty.get("deduction", 0)
            penalty_reason = penalty.get("reason", "")
            if matched:
                penalty_log.append(f"Penalty for {label}: {penalty_reason} (-{penalty_value})")
                penalty_total += penalty_value

        awarded_score = max(0, awarded_score - penalty_total)

        # Override handling
        if override_tag:
            flagged_for_teacher = True
            matched = False
            awarded_score = 0
            rationale += f"; Flagged for teacher: {override_tag}"
            needs_review = True

            if override_tag.lower() in ["misconception", "nullify"]:
                nullify_triggered = True

        output_points.append({
            "Label": label,
            "Predicted_Similarity": predicted_sim,
            "Matched": matched,
            "Awarded_Score": awarded_score,
            "Rationale": rationale,
            "Needs_Review": flagged_for_teacher,
            "Override_Tag": override_tag
        })

        if matched:
            matched_labels.append(label)

    # Nullify logic pass: wipe matched scores if a nullifying override was triggered
    if nullify_triggered:
        for p in output_points:
            if p["Matched"]:
                p["Matched"] = False
                p["Awarded_Score"] = 0
                p["Rationale"] += "; Nullified due to misconception or error"
        needs_review = True

    total_score = sum(p["Awarded_Score"] for p in output_points)
    total_possible = sum(matching_rules[p["Label"]]["max_score"] for p in output_points)

    return {
        "Answer_Text": answer["Answer_Text"],
        "Mark_Points": output_points,
        "Total_Possible_Score": total_possible,
        "Total_Final_Score": total_score,
        "Needs_Review": needs_review,
        "Feedback": "; ".join(penalty_log)
    }
