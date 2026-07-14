from fastapi import FastAPI

app = FastAPI(title="Prescription ML Service")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ml"}