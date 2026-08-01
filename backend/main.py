from fastapi import FastAPI

app = FastAPI(
    title="Melo-AI",
    version="0.1.0"
)

@app.get("/")
def home():
    return {
        "name": "Melo-AI",
        "status": "running"
    }