from traceback import format_exc

from fastapi import APIRouter
from pydantic import BaseModel

from src.utils.image import download_image, cleanup_image
from src.services.preprocess import preprocess_image
from src.services.ocr import extract_text

router = APIRouter()


class ProcessRequest(BaseModel):
    prescriptionId: str
    imageUrl: str


@router.post("/process")
def process(request: ProcessRequest):
    raw_image_path = None
    processed_image_path = None

    try:
        # Step 1: Download
        raw_image_path = download_image(request.imageUrl)

        # Step 2: Preprocess
        processed_image_path = preprocess_image(raw_image_path)

        # Step 3: OCR
        raw_text = extract_text(processed_image_path)

        return {
            "status": "success",
            "prescriptionId": request.prescriptionId,
            "rawText": raw_text,
        }

    except Exception as e:
        print(format_exc())

        return {
            "status": "failed",
            "prescriptionId": request.prescriptionId,
            "error": str(e),
        }

    finally:
        # Always clean up temp files to avoid PermissionError on the next request
        cleanup_image(raw_image_path)
        cleanup_image(processed_image_path)
