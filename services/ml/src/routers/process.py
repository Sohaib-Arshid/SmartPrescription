import logging
import os
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.utils.image import download_image, cleanup_image
from src.services.preprocess import preprocess_image
from src.services.ocr import run_ocr_pipeline, compare_ocr, fuse_ocr
from src.services.ocr.cleaner import clean_medical_text
from src.services.ocr.dictionary import correct_medical_text
from src.services.parser import parse_prescription
from src.services.interaction.drug_interaction import check_interactions
from src.services.reminder.scheduler import generate_reminders

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

        variant_dir = f"{_TEMP_DIR}/{uuid.uuid4().hex}"
        os.makedirs(variant_dir, exist_ok=True)

        candidates = run_ocr_pipeline(processed_image_path, save_dir=variant_dir)

        if not candidates:
            raise ValueError("All OCR engines produced no output.")

        best = compare_ocr(candidates)
        fused_text = fuse_ocr(candidates)
        cleaned_text = clean_medical_text(fused_text)
        corrected_text = correct_medical_text(cleaned_text)

        logger.info(
            "Best result: engine=%s variant=%s score=%d",
            best.engine, best.image_type, best.score,
        )

        structured_data: dict[str, Any] = parse_prescription(corrected_text)

        medicines: list[dict[str, Any]] = structured_data.get("medicines") or []
        medicine_names = [m["name"] for m in medicines if m.get("name")]

        drug_interactions = check_interactions(medicine_names)
        reminders = generate_reminders(medicines)
        needs_review, review_reasons, low_confidence_fields = _build_review_metadata(
            structured_data
        )

        return {
            "status": "success",
            "prescriptionId": request.prescriptionId,
            "ocrEngine": best.engine,
            "ocrVariant": best.image_type,
            "ocrScore": best.score,
            "rawText": corrected_text,
            "structuredData": structured_data,
            "drugInteractions": drug_interactions,
            "reminders": reminders,
            "needsUserReview": needs_review,
            "reviewReasons": review_reasons,
            "lowConfidenceFields": low_confidence_fields,
        }

    except Exception as exc:
        logger.exception(
            "Processing failed for prescriptionId=%s", request.prescriptionId
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    finally:
        cleanup_image(raw_image_path)
        cleanup_image(processed_image_path)
        _cleanup_variant_dir(variant_dir)


def _build_review_metadata(
    structured_data: dict[str, Any],
) -> tuple[bool, list[str], list[str]]:
    reasons: list[str] = []
    low_fields: list[str] = []

    medicines: list[dict[str, Any]] = structured_data.get("medicines") or []

    if not medicines:
        reasons.append("No medicines detected")

    for med in medicines:
        name = med.get("name", "")
        confidence = med.get("confidence")

        if med.get("needsReview"):
            reasons.append(f"Low legibility for: {name}")

        if confidence is not None and confidence < 0.7:
            low_fields.append(f"medicines[{name}].confidence")

        for field in ("dosage", "frequency", "duration"):
            if not med.get(field):
                low_fields.append(f"medicines[{name}].{field}")

    overall_confidence = structured_data.get("overallConfidence")
    if overall_confidence is not None and overall_confidence < 0.7:
        reasons.append("Low overall OCR confidence")

    low_fields.extend(structured_data.get("lowConfidenceFields") or [])
    low_fields = list(dict.fromkeys(low_fields))

    needs_review = bool(reasons or low_fields)
    return needs_review, reasons, low_fields


def _cleanup_variant_dir(variant_dir: str | None) -> None:
    if not variant_dir or not os.path.isdir(variant_dir):
        return
    try:
        for f in os.listdir(variant_dir):
            cleanup_image(os.path.join(variant_dir, f))
        os.rmdir(variant_dir)
    except Exception as e:
        logger.warning("Could not clean up variant dir %s: %s", variant_dir, e)
