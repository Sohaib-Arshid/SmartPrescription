from fastapi import APIRouter
from pydantic import BaseModel
from src.utils.image import download_image
from src.services.preprocess import preprocess_image

router = APIRouter()


class ProcessRequest(BaseModel):
    prescriptionId: str
    imageUrl: str


@router.post("/process")
def process(request: ProcessRequest):

    image_path = download_image(request.imageUrl)

    processed_path = preprocess_image(image_path)

    print(processed_path)

    return {
        "status": "success",
        "processedImage": processed_path
    }