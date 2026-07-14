from fastapi import FastAPI
from src.config.settings import PORT

app = FastAPI(title="Prescription ML Service")

@app.get("/")
def home():
    return {
        "message": "ML Service is running"
    }