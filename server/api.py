from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import call_bot, generate_follow_up
from database import insert_task, update_task_status
from router import route
from dashboard import get_dashboard_data
import logging
log = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    message: str
    previous_context: dict | None = None

@app.post("/chat")
def chat(data: RequestData):
    try:
        message = data.message
        chatbot_response = call_bot(message, data.previous_context)
        intent = chatbot_response.get("intent")
        entities = chatbot_response.get("entities", {})
        confidence = float(chatbot_response.get("confidence", 0.5))

        conversation_history = []
        if data.previous_context:
            conversation_history = data.previous_context.get("conversation_history", [])
        conversation_history.append(message)

        action, reason, missing = route(intent, entities, confidence, message)

        follow_up_questions = []
        if action == "follow_up_questions":
            follow_up_questions = generate_follow_up(entities, reason, missing)

        if action != "follow_up_questions": insert_task(message, intent, entities, confidence, action, data.previous_context, reason)
        return {
            "action": action,
            "reason": reason,
            "follow_up_questions": follow_up_questions if action == "follow_up_questions" else [],
            "context": {
                "conversation_history": conversation_history,
                "previous_json": chatbot_response
            } if action == "follow_up_questions" else None
        }

    except Exception as exc:
        log.error("Chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/dashboard")
def dashboard():
    try:
        tasks = get_dashboard_data()
        return {"tasks": tasks}
    except Exception as exc:
        log.error("Dashboard error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

class StatusUpdate(BaseModel):
    status: str

@app.patch("/tasks/{task_id}/status")
def updateTaskStatus(task_id: int, data: StatusUpdate):
    try:
        update_task_status(task_id, data.status)
        return {"success": True}
    except Exception as exc:
        log.error("Task Update error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))