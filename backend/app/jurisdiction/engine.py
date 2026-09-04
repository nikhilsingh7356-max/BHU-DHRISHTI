from typing import Any


def evaluate_jurisdiction_rules(rules: list, project: Any, db=None) -> dict:
    best_result = None
    best_confidence = 0.0
    best_rule = None

    for rule in rules:
        conditions = rule.conditions or {}
        score = 0.0
        total = 0.0

        if "project_type" in conditions:
            total += 1.0
            if project.project_type == conditions["project_type"]:
                score += 1.0

        if "purpose_contains" in conditions:
            total += 1.0
            if project.purpose and conditions["purpose_contains"].lower() in project.purpose.lower():
                score += 1.0

        if "public_category" in conditions:
            total += 1.0
            if project.public_category == conditions["public_category"]:
                score += 1.0

        if "public_category_in" in conditions:
            total += 1.0
            allowed = conditions["public_category_in"]
            if isinstance(allowed, list) and project.public_category in allowed:
                score += 1.0

        if "estimated_cost_min" in conditions:
            total += 1.0
            if project.estimated_cost is not None and float(project.estimated_cost) >= float(conditions["estimated_cost_min"]):
                score += 1.0

        if "priority_min" in conditions:
            total += 1.0
            if project.priority >= conditions["priority_min"]:
                score += 1.0

        if total > 0:
            confidence = score / total
            if confidence > best_confidence:
                best_confidence = confidence
                best_result = rule.result
                best_rule = rule

    if best_result is None:
        return {
            "appropriate_govt": None,
            "acquiring_body": None,
            "authority": None,
            "confidence": 0.0,
            "reason": "No jurisdiction rule matched",
            "rule_id": None
        }

    return {
        "appropriate_govt": best_result.get("appropriate_govt"),
        "acquiring_body": best_result.get("acquiring_body"),
        "authority": best_result.get("authority"),
        "confidence": round(best_confidence, 2),
        "reason": f"Matched rule {best_rule.rule_code} with confidence {round(best_confidence, 2)}",
        "rule_id": str(best_rule.id)
    }
