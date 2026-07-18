from fastapi import FastAPI
from src.config.settings import PORT
from src.routers.process import router

app = FastAPI(title="Prescription ML Service")

app.include_router(router, prefix="/api/v1")

@app.get("/")
def home():
    return {
        "message": "ML Service is running"
    }