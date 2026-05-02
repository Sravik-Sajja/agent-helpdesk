HUMAN_HANDOFF_INTENTS = {"urgent_symptom_report", "billing_dispute"}
SELF_SCHEDULE_INTENTS = {"reschedule_appointment", "cancel_appointment", "new_appointment"}
FOLLOW_UP_INTENTS = {"prescription_refill", "referral_request", "provider_inquiry", "general_inquiry"}

LOW_CONFIDENCE_THRESHOLD = 0.55


def route(intent: str, entities: dict, confidence: float, raw_message: str) -> tuple[str, str, list]:
    """Determine the routing action for a patient request."""
    message_lower = raw_message.lower()

    # Low confidence, ask follow up questions
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return "follow_up_questions", f"Confidence {confidence:.0%} below threshold — need clarification", ["intent"]

    # Ai flags urgency as high
    urgency = entities.get("urgency", "").lower()
    if urgency == "high":
        return "human_handoff", "AI flagged urgency as high", []

    # Intent-based routing
    if intent in HUMAN_HANDOFF_INTENTS:
        return "human_handoff", f"Intent '{intent}' requires human handling", []

    if intent in SELF_SCHEDULE_INTENTS:
        missing = []
        if not entities.get("specialty"): missing.append("specialty")
        if not entities.get("date"): missing.append("date")
        if not entities.get("preferred_time"): missing.append("preferred_time")

        if not missing:
            return "self_schedule", "Sufficient detail for patient self-scheduling", []
        else:
            return "follow_up_questions", f"Missing {', '.join(missing)} for self-scheduling", missing

    if intent in FOLLOW_UP_INTENTS:
        return "follow_up_questions", f"Intent '{intent}' requires additional information", ["additional_info"]

    # Fallback
    return "follow_up_questions", "Unrecognized intent — defaulting to follow-up", ["intent"]