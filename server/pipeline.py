from dotenv import load_dotenv
from anthropic import Anthropic
import os
import json

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
SYSTEM_PROMPT = """You are a medical intake assistant. Analyze patient messages and return structured JSON.
 
Return ONLY valid JSON with this exact schema:
{
  "intent": "<one of: reschedule_appointment, cancel_appointment, new_appointment, urgent_symptom_report, prescription_refill, referral_request, provider_inquiry, billing_dispute, general_inquiry>",
  "entities": {
    "specialty": "<medical specialty if mentioned, else null>",
    "provider": "<provider name if mentioned, else null>",
    "date": "<date/time preference if mentioned, else null>",
    "preferred_time": "<time preference like morning/afternoon/weekend, else null>",
    "insurance": "<insurance name if mentioned, else null>",
    "symptoms": ["<list of symptoms if mentioned>"],
    "medication": "<medication name if mentioned, else null>",
    "urgency": "<high/medium/low based on clinical language>",
    "appointment_type": "<type of appointment if mentioned, else null>"
  },
  "confidence": <float 0.0 to 1.0 — how confident you are in the intent classification>,
  "reasoning": "<one sentence explaining why you chose this intent>"
}
 
Be precise. Extract only what is explicitly stated or strongly implied."""

def call_bot(messsage):
    '''Calls chatbot with patient message and returns JSON response'''
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system = SYSTEM_PROMPT,
        messages=[{"role": "user", "content": messsage}]
    )
    raw = response.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
 
    result = json.loads(raw.strip())
    return result
