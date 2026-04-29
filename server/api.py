from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import call_bot
from database import insert_task
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

@app.post("/chat")
def chat(data: RequestData):
    try:
        message = data.message
        chatbot_response = call_bot(message)
        intent = chatbot_response.get("intent", "unknown")
        entities = chatbot_response.get("entities", {})
        confidence = float(chatbot_response.get("confidence", 0.5))

        action, reason = route(intent, entities, confidence, message)

        insert_task(message, intent, entities, confidence, action, reason)
        return {"action": action, "reason": reason}

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