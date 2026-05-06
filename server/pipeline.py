from dotenv import load_dotenv
from anthropic import Anthropic
import os
import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a medical intake assistant. Analyze patient messages and return structured JSON.
 
Return ONLY valid JSON with this exact schema:
{
  "intent": "<one of: reschedule_appointment, cancel_appointment, new_appointment, urgent_symptom_report, prescription_refill, document_request, provider_inquiry, billing_dispute, general_inquiry, none>",
  "entities": {
    "specialty": "<medical department or field e.g. cardiology, dermatology, orthopedics — NOT appointment type if mentioned, else null>",
    "provider": "<specific doctor name if mentioned, else null>",
    "original_date": "<specific date in YYYY-MM-DD format(only to identify what appointment they are rescheduling or cancelling)"
    "schedule_date": "<specific date or date range in YYYY-MM-DD format using the current date for what date they are scheduling too"
        "For a range like 'next week' or 'any day next week': use YYYY-MM-DD to YYYY-MM-DD covering Monday to Friday of that week. "
        "For 'this week': Current day to Friday of the current week. "
        "Else null if no date mentioned.>"
    "preferred_time": "<time preference like morning/afternoon, else null>",
        "If they say anytime just put any here"
    "insurance": "<insurance name if mentioned, else null>",
    "symptoms": ["<list of symptoms if mentioned>"](e.g. fever, pain, or any other symptomatic information),
    "medication": "<specific brand or generic drug name only (e.g. lisinopril, aspirin). If the patient describes a drug by category(e.g. 'blood pressure medication', 'my anxiety pill', 'water pill') set this to null
    "urgency": "<high/medium/low based on clinical language; always pick one>",
    "appointment_type": "<type of visit e.g. annual physical — NOT medical specialty if mentioned, else null>"
  },
  "confidence": <float 0.0 to 1.0 — how confident you are in the intent classification>,
  "reasoning": "<one sentence explaining why you chose this intent>"
}
"document_request: use when patient asks for a signature or a form(e.g. referral)
"none: use when the message is a greeting, casual conversation, or has no relation to medical scheduling, appointments, symptoms, prescriptions, or billing and you had no previous intent given to you"
"general_inquiry: patient is asking about office information, hours, etc"
"provider_inquiry: patient is asking about a doctor or staff member(may need to ask them which one they are talking about)"
 
Be precise. Extract only what is explicitly stated. Do not infer specialty from symptoms."""


def call_bot(message: str, previous_context: dict = None, timezone: str = "UTC") -> dict:
    """Calls chatbot with patient message and returns JSON response"""

    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    current_time = datetime.now(tz).strftime("%A, %B %d, %Y %H:%M %Z")
    if previous_context:
        history = previous_context.get("conversation_history", [])
        history_text = "\n".join([f"User: {m}" for m in history])
        user_content = f"""Conversation so far:
                        {history_text}

                        Previous extraction: {json.dumps(previous_context['previous_json'])}
                        User follow up: {message}
                        Current date/time: {current_time}

                        Update the extraction with the new information provided."""
    else:
        user_content = f"""Current date/time: {current_time}

                        User message: {message}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )
    raw = response.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        log.error("Failed to parse LLM response: %s\nRaw output: %s", e, raw)
        raise ValueError(f"LLM returned invalid JSON: {raw[:200]}")

    return result


def generate_follow_up(entities: dict, intent: str, reason: str, missing_fields: list) -> list:
    """Generates follow up questions to get full information from patient"""
    system_prompt = """
                    You are a medical intake assistant. Generate short friendly follow-up questions to collect missing patient information. 
                    Use simple everyday language — do not use medical jargon like 'specialty' or technical terms the patient may not 
                    understand. Do not assume or suggest any specific dates, times, or details. Return ONLY a valid JSON array of question strings, nothing else.
                    """

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f""" Reason for follow-up question: {reason}
                        Extracted intent: {intent}
                        Extracted entities: {json.dumps(entities)}
                        Missing required fields: {missing_fields}
                        Generate one short friendly question per missing field."""
        }]
    )
    raw = response.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError as e:
        log.error("Failed to parse follow-up questions: %s\nRaw output: %s", e, raw)
        return [f"Could you provide your {field}?" for field in missing_fields]

def generate_summarized_title(intent: str, entities: dict, conversation_history: list) -> str:
    """Generates a short human-readable title for a task to display on the dashboard."""
    history_text = " → ".join(conversation_history) if conversation_history else ""
 
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            system="Return ONLY a short title summarizing the patient's request. No preamble, no quotes.",
            messages=[{
                "role": "user",
                "content": f"""Intent: {intent}
                Entities: {json.dumps(entities)}
                Messages: {history_text}
                """
            }]
        )
        return response.content[0].text.strip()
    except Exception as e:
        log.error("Failed to generate title: %s", e)
        # Fallback, derive a basic title from intent + key entity
        specialty = entities.get("specialty") or entities.get("appointment_type") or ""
        base = intent.replace("_", " ").title()
        return f"{base} — {specialty.title()}" if specialty else base