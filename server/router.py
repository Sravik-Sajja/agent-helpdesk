HUMAN_HANDOFF_INTENTS = {"urgent_symptom_report", "billing_dispute"}
SELF_SCHEDULE_INTENTS = {"reschedule_appointment", "cancel_appointment", "new_appointment"}
FOLLOW_UP_INTENTS = {"prescription_refill", "referral_request", "provider_inquiry", "general_inquiry"}

LOW_CONFIDENCE_THRESHOLD = 0.55


def route(intent: str, entities: dict, confidence: float, raw_message: str) -> tuple[str, str]:
    """Determine the routing action for a patient request."""
    message_lower = raw_message.lower()

    # Low confidence, ask follow up questions
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return "follow_up_questions", f"Confidence {confidence:.0%} below threshold — need clarification"

    # Ai flags urgency as high
    urgency = entities.get("urgency", "").lower()
    if urgency == "high":
        return "human_handoff", "AI flagged urgency as high"

    # Intent-based routing
    if intent in HUMAN_HANDOFF_INTENTS:
        return "human_handoff", f"Intent '{intent}' requires human handling"

    if intent in SELF_SCHEDULE_INTENTS:
        # Needs insurance + specialty to self-schedule
        if entities.get("specialty") and entities.get("date") or entities.get("preferred_time"):
            return "self_schedule", "Sufficient detail for patient self-scheduling"
        else:
            return "follow_up_questions", "Missing specialty or time preference for self-scheduling"

    if intent in FOLLOW_UP_INTENTS:
        return "follow_up_questions", f"Intent '{intent}' requires additional information"

    # Fallback
    return "follow_up_questions", "Unrecognized intent — defaulting to follow-up"