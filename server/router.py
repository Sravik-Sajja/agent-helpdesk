HUMAN_HANDOFF_INTENTS = {"urgent_symptom_report", "billing_dispute"}
SELF_SCHEDULE_INTENTS = {"reschedule_appointment", "cancel_appointment", "new_appointment"}
STAFF_ROUTED_INTENTS = {"prescription_refill", "document_request"}
AUTO_RESPONSE_INTENTS = {"provider_inquiry", "general_inquiry"}
NO_INTENT = {"none"}

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
        if not entities.get("specialty") and not entities.get("provider") and not entities.get("appointment_type"): missing.append("specialty/provider/appointment_type")

        #Ignore preferred_time for cancel_appointment
        if intent == "reschedule_appointment" or intent == "new_appointment":
            if not entities.get("preferred_time"): missing.append("preferred_time")
        
        #Get original appointment date for reshedule appointment
        if intent == "reschedule_appointment" or intent == "cancel_appointment":
            if not entities.get("original_date"): missing.append("original_date")
        if intent == "reschedule_appointment" or intent == "new_appointment":
            if not entities.get("schedule_date"): missing.append("schedule_date")

        if missing:
            return "follow_up_questions", f"Missing {', '.join(missing)} for self-scheduling", missing
        else:
            return "self_schedule", "Sufficient detail for patient self-scheduling", []

    if intent in STAFF_ROUTED_INTENTS:
        missing = []
        if intent == "prescription_refill" and not entities.get("medication"):
            missing.append("medication name")
        if intent == "document_request" and not entities.get("specialty") and not entities.get("provider"):
            missing.append("type of doctor or care they need")

        if missing:
            return "follow_up_questions", f"Missing {', '.join(missing)}", missing
        else: 
            return "human_handoff", f"Sufficient detail collected for '{intent}' — routing to staff", []
    
    if intent in AUTO_RESPONSE_INTENTS:
        missing = []
        if intent == "provider_inquiry":
            provider = (entities.get("provider") or "").lower()
            if not provider:
                missing.append("doctor or provider name")
            else:
                # Would query providers table here e.g. SELECT * FROM providers WHERE name = ?
                return "auto_response", f"Provider lookup for {provider} — would pull from DB", []
        if intent == "general_inquiry":
            # Would query FAQ/knowledge base table here
            return "auto_response", "General inquiry — would pull from database", []
        
        if missing:
            return "follow_up_questions", f"Missing {', '.join(missing)}", missing

    
    if intent in NO_INTENT:
        return "clarify", "No useful information", []

    # Fallback
    return "follow_up_questions", "Unrecognized intent — defaulting to follow-up", ["intent"]