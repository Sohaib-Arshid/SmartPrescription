import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.utils.image import download_image, cleanup_image
from src.services.preprocess import preprocess_image
from src.services.ocr.runner import run_ocr_pipeline
from src.services.ocr.comparator import compare_ocr
from src.services.ocr.fusion import fuse_ocr
from src.services.groq import parse_prescription

logger = logging.getLogger(__name__)

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

        candidates = run_ocr_pipeline(processed_image_path)

        if not candidates:
            raise ValueError("No OCR result generated.")

        best_result = compare_ocr(candidates)

        fused_text = fuse_ocr(candidates)

        logger.info(
            "Best OCR engine=%s variant=%s score=%s",
            best_result.engine,
            best_result.image_type,
            best_result.score,
        )

        structured_data = parse_prescription(fused_text)

        return {
            "status": "success",
            "prescriptionId": request.prescriptionId,
            "ocrEngine": best_result.engine,
            "ocrVariant": best_result.image_type,
            "ocrScore": best_result.score,
            "rawText": fused_text,
            "structuredData": structured_data,
        }

    except Exception as exc:
        logger.exception("Prescription processing failed for id=%s", request.prescriptionId)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    finally:
        cleanup_image(raw_image_path)
        cleanup_image(processed_image_path)