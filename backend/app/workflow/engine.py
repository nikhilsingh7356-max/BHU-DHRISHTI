VALID_TRANSITIONS = {
    "DRAFT": ["SUBMITTED", "CANCELLED"],
    "SUBMITTED": ["UNDER_REVIEW", "REJECTED", "DRAFT"],
    "UNDER_REVIEW": ["JURISDICTION_CHECK", "GIS_VERIFICATION", "REJECTED", "SUBMITTED"],
    "JURISDICTION_CHECK": ["GIS_VERIFICATION", "PUBLIC_HEARING", "REJECTED"],
    "GIS_VERIFICATION": ["PUBLIC_HEARING", "JURISDICTION_CHECK", "REJECTED"],
    "PUBLIC_HEARING": ["COMPENSATION_ASSESSMENT", "RR_PLANNING", "REJECTED", "GIS_VERIFICATION"],
    "COMPENSATION_ASSESSMENT": ["APPROVED", "REJECTED", "RR_PLANNING", "PUBLIC_HEARING"],
    "RR_PLANNING": ["APPROVED", "REJECTED", "COMPENSATION_ASSESSMENT", "PUBLIC_HEARING"],
    "APPROVED": ["IN_PROGRESS", "COMPLETED", "RR_PLANNING", "CANCELLED"],
    "IN_PROGRESS": ["COMPLETED", "CANCELLED", "REJECTED"],
    "COMPLETED": [],
    "REJECTED": ["DRAFT", "UNDER_REVIEW", "CANCELLED"],
    "CANCELLED": [],
}


def validate_transition(from_status: str, to_status: str) -> bool:
    allowed = VALID_TRANSITIONS.get(from_status, [])
    return to_status in allowed


def get_allowed_transitions(from_status: str) -> list[str]:
    return VALID_TRANSITIONS.get(from_status, [])


def get_task_type_for_transition(to_status: str) -> str:
    task_types = {
        "SUBMITTED": "REVIEW",
        "UNDER_REVIEW": "REVIEW",
        "JURISDICTION_CHECK": "JURISDICTION_CHECK",
        "GIS_VERIFICATION": "GIS_CHECK",
        "PUBLIC_HEARING": "HEARING",
        "COMPENSATION_ASSESSMENT": "COMPENSATION",
        "RR_PLANNING": "RR_PLANNING",
        "APPROVED": "APPROVAL",
        "IN_PROGRESS": "NOTIFICATION",
        "COMPLETED": "NOTIFICATION",
    }
    return task_types.get(to_status, "REVIEW")


def get_task_role_for_transition(to_status: str) -> str:
    role_map = {
        "SUBMITTED": "REVIEWER",
        "UNDER_REVIEW": "REVIEWER",
        "JURISDICTION_CHECK": "CENTRAL_AUTHORITY",
        "GIS_VERIFICATION": "SURVEYOR_GIS_OFFICER",
        "PUBLIC_HEARING": "DISTRICT_ADMIN",
        "COMPENSATION_ASSESSMENT": "COMPENSATION_OFFICER",
        "RR_PLANNING": "RR_OFFICER",
        "APPROVED": "CENTRAL_AUTHORITY",
        "IN_PROGRESS": "PROJECT_SPONSOR",
        "COMPLETED": "PROJECT_SPONSOR",
    }
    return role_map.get(to_status, "VIEWER")
