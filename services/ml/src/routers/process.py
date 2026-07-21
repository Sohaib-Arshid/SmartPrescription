import logging
import os
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.utils.image import download_image, cleanup_image
from src.services.preprocess import preprocess_image
from src.services.ocr import run_ocr_pipeline, compare_ocr, fuse_ocr
from src.services.parser import parse_prescription

logger = logging.getLogger(__name__)

router = APIRouter()

_TEMP_DIR = os.path.abspath("temp").replace("\\", "/")


class ProcessRequest(BaseModel):
    prescriptionId: str
    imageUrl: str


@router.post("/process")
def process(request: ProcessRequest):
    raw_image_path = None
    processed_image_path = None
    variant_dir = None

    try:
        raw_image_path = download_image(request.imageUrl)

        processed_image_path = preprocess_image(raw_image_path)

        # Each request gets its own subdirectory for enhanced variants so
        # concurrent requests don't overwrite each other's files.
        variant_dir = f"{_TEMP_DIR}/{uuid.uuid4().hex}"
        os.makedirs(variant_dir, exist_ok=True)

        candidates = run_ocr_pipeline(processed_image_path, save_dir=variant_dir)

        if not candidates:
            raise ValueError("All OCR engines produced no output.")

        best = compare_ocr(candidates)
        fused_text = fuse_ocr(candidates)

        logger.info(
            "Best result: engine=%s variant=%s score=%d",
            best.engine, best.image_type, best.score,
        )

        structured_data = parse_prescription(fused_text)

        return {
            "status": "success",
            "prescriptionId": request.prescriptionId,
            "ocrEngine": best.engine,
            "ocrVariant": best.image_type,
            "ocrScore": best.score,
            "rawText": fused_text,
            "structuredData": structured_data,
        }

    except Exception as exc:
        logger.exception("Processing failed for prescriptionId=%s", request.prescriptionId)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    finally:
        cleanup_image(raw_image_path)
        cleanup_image(processed_image_path)
        _cleanup_variant_dir(variant_dir)


def _cleanup_variant_dir(variant_dir: str | None) -> None:
    if not variant_dir or not os.path.isdir(variant_dir):
        return
    try:
        for f in os.listdir(variant_dir):
            cleanup_image(os.path.join(variant_dir, f))
        os.rmdir(variant_dir)
    except Exception as e:
        logger.warning("Could not clean up variant dir %s: %s", variant_dir, e)
