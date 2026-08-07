from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.chat import router as chat_router
from api.session import router as session_router
from api.settings import router as settings_router

app = FastAPI(
    title="Melo-AI",
    version="0.1.0"
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(settings_router)

@app.get("/")
def home():
    return {
        "name": "Melo-AI",
        "status": "running"
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)