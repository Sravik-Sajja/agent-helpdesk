# Patient Intake AI

A Python + AI workflow application that processes patient chat messages, classifies intent, extracts clinical entities, routes requests to the appropriate action, and surfaces everything in a live task dashboard.

---

## What It Does

When a patient sends a message like *"I need to reschedule my cardiology appointment — I'm free any afternoon next week"*, the system:

1. **Classifies intent** — `reschedule_appointment`, `urgent_symptom_report`, `prescription_refill`, etc.
2. **Extracts entities** — specialty, provider, preferred time, insurance, medication, symptoms, urgency
3. **Routes the request** — self-scheduling, human handoff, auto-response, or follow-up questions
4. **Handles multi-turn conversations** — asks clarifying questions and carries context across turns
5. **Logs every resolved task** to SQLite and displays it in a dashboard, sorted by urgency

---

## Architecture

```
client/                  # Static HTML/CSS/JS frontend
├── index.html           # Chat interface
├── index.js             # Chat logic, context management, detail panel
├── dashboard.html       # Task queue dashboard
└── dashboard.js         # Dashboard load, render, status updates

server/
├── api.py               # FastAPI endpoints: /chat, /dashboard, /tasks/:id/status
├── pipeline.py          # LLM calls: intent extraction, follow-up generation, title summarization
├── router.py            # Rule-based routing layer (combines intent + entities + confidence)
├── dashboard.py         # Dashboard query + urgency sort logic
├── database.py          # SQLite schema, insert, read, update
├── evaluate.py          # Accuracy evaluation script (single-turn + multi-turn)
└── data/
    └── conversations.json  # 17 labeled test conversations (single + multi-turn)
```

### Request Lifecycle

```
User message
    │
    ▼
pipeline.call_bot()          ← Claude Haiku: returns intent, entities, confidence, reasoning
    │
    ▼
router.route()               ← Rule engine: maps intent + entities + confidence → action
    │
    ├─ follow_up_questions → pipeline.generate_follow_up() → return questions to client
    │                        (context stored client-side, replayed on next turn)
    │
    └─ resolved action    → pipeline.generate_summarized_title() → database.insert_task()
                                                                  → return action to client
```

---

## Routing Logic

The routing layer (`router.py`) is intentionally rule-based on top of AI output — this makes behavior predictable, auditable, and easy to modify without retraining anything.

| Condition | Action |
|---|---|
| Confidence < 55% | `follow_up_questions` |
| Urgency flagged `high` by AI | `human_handoff` |
| Intent: `urgent_symptom_report`, `billing_dispute` | `human_handoff` |
| Intent: `reschedule_appointment`, `cancel_appointment`, `new_appointment` | `self_schedule` if all required fields present, else `follow_up_questions` |
| Intent: `prescription_refill`, `document_request` | `human_handoff` if complete, else `follow_up_questions` |
| Intent: `provider_inquiry`, `general_inquiry` | `auto_response` (would query provider/FAQ DB) |
| Intent: `none` | `clarify` |

Required fields per intent are checked explicitly — for example, a reschedule requires `specialty` or `provider`, `original_date`, `schedule_date`, and `preferred_time` before it can route to self-scheduling.

---

## Multi-Turn Conversations

When the router returns `follow_up_questions`, the context (conversation history + previous JSON extraction) is stored client-side and replayed on the next request. The LLM merges the new message with the prior extraction, so entities accumulate across turns without the server needing to maintain session state.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| API framework | FastAPI + Pydantic |
| LLM | Claude Haiku (`claude-haiku-4-5`) via Anthropic SDK |
| Database | SQLite (via `sqlite3`) |
| Frontend | Vanilla HTML/CSS/JS (see note below) |
| Eval | Custom Python script (`evaluate.py`) |

---

## Evaluation
 
Run the eval script against all labeled test conversations:
 
```bash
cd server
python evaluate.py
```
 
The script tests both single-turn and multi-turn conversations, reporting intent accuracy and route accuracy for all conversations. Results print to stdout with ✓/✗ per field.
 
**Entity evaluation is single-turn only.** Multi-turn conversations are only evaluated on intent and route per turn.
 
For single-turn conversations, entity evaluation checks **which categories were extracted**, not whether the extracted value is correct. For example, if the expected entities include `specialty`, the eval verifies that the model returned a non-null `specialty` field — not that it matched the exact string. This tests extraction coverage (did the model recognize what information to pull?) rather than value precision. Urgency is the one exception: it is checked as an exact match since it directly affects routing.
 
The dataset (`server/data/conversations.json`) covers 17 conversations including edge cases: low-confidence vague messages, multi-turn entity accumulation, urgency escalation, and `none` intent (greetings/off-topic).
 
---

## Setup & Running

**Prerequisites:** Python 3.11+, an Anthropic API key

```bash
# 1. Clone and install dependencies
pip install fastapi uvicorn anthropic python-dotenv pydantic

# 2. Set your API key
echo "ANTHROPIC_API_KEY=your_key_here" > server/.env

# 3. Initialize the database
cd server
python database.py

# 4. Start the API server
uvicorn api:app --reload --port 8000

# 5. Open the frontend
# Open client/index.html in your browser (or serve with any static file server)
```