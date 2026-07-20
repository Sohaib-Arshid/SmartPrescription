from traceback import format_exc

from fastapi import APIRouter
from pydantic import BaseModel

from src.utils.image import download_image, cleanup_image
from src.services.preprocess import preprocess_image
from src.services.ocr.comparator import compare_ocr
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
        # Step 1: Download image
        raw_image_path = download_image(request.imageUrl)

        # Step 2: Preprocess image
        processed_image_path = preprocess_image(raw_image_path)

        # Step 3: Run both OCR engines and choose the best
        best_result = compare_ocr(processed_image_path)

        raw_text = best_result.text

        print("\n==============================")
        print(f"OCR Engine : {best_result.engine}")
        print(f"OCR Score  : {best_result.score}")
        print("==============================\n")

        # Step 4: Send best OCR output to LLM
        structured_data = parse_prescription(raw_text)

        return {
            "status": "success",
            "prescriptionId": request.prescriptionId,
            "ocrEngine": best_result.engine,
            "ocrScore": best_result.score,
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