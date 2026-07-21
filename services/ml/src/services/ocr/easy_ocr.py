import logging
import os

import cv2
import easyocr

logger = logging.getLogger(__name__)

_reader = easyocr.Reader(["en"], gpu=False)

MIN_CONFIDENCE = 0.35


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _validate_image(image_path: str) -> None:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if os.path.getsize(image_path) == 0:
        raise ValueError(f"Image is empty: {image_path}")

    if cv2.imread(image_path) is None:
        raise ValueError(f"Unable to decode image: {image_path}")


def extract_text(image_path: str) -> str:
    image_path = _normalize_path(image_path)
    _validate_image(image_path)

    try:
        # detail=1 always returns (bbox, text, confidence) regardless of paragraph mode.
        # paragraph=False preserves per-word confidence so we can filter low-quality reads.
        results = _reader.readtext(image_path, detail=1, paragraph=False)

        texts = [
            text.strip()
            for _, text, confidence in results
            if text.strip() and confidence >= MIN_CONFIDENCE
        ]

        return " ".join(texts)

    except Exception as e:
        logger.exception("EasyOCR failed on %s", image_path)
        raise RuntimeError(f"EasyOCR failed: {type(e).__name__}: {e}") from e
