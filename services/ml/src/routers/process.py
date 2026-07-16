from fastapi import APIRouter
from pydantic import BaseModel
from src.utils.image import download_image
from src.services.preprocess import preprocess_image
from src.services.ocr import extract_text

router = APIRouter()


class ProcessRequest(BaseModel):
    prescriptionId: str
    imageUrl: str


@router.post("/process")
def process(request: ProcessRequest):

    image_path = download_image(request.imageUrl)

    processed_path = preprocess_image(image_path)
    
    raw_text = extract_text(processed_path)


    print(raw_text)

    return {
        "status": "success",
        "rawText": raw_text
    }