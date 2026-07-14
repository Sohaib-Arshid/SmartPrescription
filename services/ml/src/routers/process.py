from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ProcessRequest(BaseModel):
    prescriptionId: str
    imageUrl: str

@router.post("/process")
def process(request: ProcessRequest):
    print(request)

    return {
        "status": "success",
        "prescriptionId": request.prescriptionId,
        "imageUrl": request.imageUrl
    }