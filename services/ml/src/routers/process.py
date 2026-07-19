from traceback import format_exc

from fastapi import APIRouter
from pydantic import BaseModel

from src.utils.image import download_image, cleanup_image
from src.services.preprocess import preprocess_image
from src.services.ocr import extract_text
from src.services.gpt4 import parse_prescription

router = APIRouter()


class ProcessRequest(BaseModel):
    prescriptionId: str
    imageUrl: str


@router.post("/process")
def process(request: ProcessRequest):
    raw_image_path = None
    processed_image_path = None

    try:
        raw_image_path = download_image(request.imageUrl)

        processed_image_path = preprocess_image(raw_image_path)
        
        raw_text = extract_text(processed_image_path)
        
        structured_data = parse_prescription(raw_text)

        return {
            "status": "success",
            "prescriptionId": request.prescriptionId,
            "rawText": raw_text,
            "structuredData": structured_data,
        }

    except Exception as e:
        print(format_exc())

        return {
            "status": "failed",
            "prescriptionId": request.prescriptionId,
            "error": str(e),
        }

    finally:
        cleanup_image(raw_image_path)
        cleanup_image(processed_image_path)