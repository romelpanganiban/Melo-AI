from fastapi import FastAPI

from api.health import router as health_router
from api.chat import router as chat_router

app = FastAPI(
    title="Melo-AI",
    version="0.1.0"
)

app.include_router(health_router)
app.include_router(chat_router)

@app.get("/")
def home():
    return {
        "name": "Melo-AI",
        "status": "running"
    }