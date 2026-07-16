from fastapi import APIRouter
from pydantic import BaseModel
from src.utils.image import download_image

router = APIRouter()

class ProcessRequest(BaseModel):
    prescriptionId: str
    imageUrl: str

@router.post("/process")
def process(request: ProcessRequest):

    image_path = download_image(request.imageUrl)

    print(image_path)

    return {
        "status": "success",
        "path": image_path
    }