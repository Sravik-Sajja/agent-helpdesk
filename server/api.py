from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import call_bot
from database import insert_task
from router import route

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

@app.post("/initial")
def health_check(data: RequestData):
    message = data.message
    chatbot_response = call_bot(message)
    intent = chatbot_response.get("intent", "unknown")
    entities = chatbot_response.get("entities", {})
    confidence = float(chatbot_response.get("confidence", 0.5))

    action, reason = route(intent, entities, confidence, message)

    insert_task(message, intent, entities, confidence, action, reason)
    return {"action": action, "reason": reason}