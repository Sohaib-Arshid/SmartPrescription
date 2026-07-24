import logging
import os
import threading

import cv2
import easyocr

logger = logging.getLogger(__name__)

MIN_CONFIDENCE = 0.35
_reader: easyocr.Reader | None = None
_reader_lock = threading.Lock()


def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        with _reader_lock:
            if _reader is None:
                logger.info("Initializing EasyOCR reader (first use)...")
                _reader = easyocr.Reader(["en"], gpu=False)
                logger.info("EasyOCR reader ready.")
    return _reader


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
        # detail=1 + paragraph=False returns (bbox, text, confidence) for every
        # detected word, allowing confidence filtering. paragraph=True omits the
        # confidence value from the tuple, making filtering impossible.
        results = _get_reader().readtext(image_path, detail=1, paragraph=False)

        texts = [
            text.strip()
            for _, text, confidence in results
            if text.strip() and confidence >= MIN_CONFIDENCE
        ]

        return " ".join(texts)

    except Exception as e:
        logger.exception("EasyOCR failed on %s", image_path)
        raise RuntimeError(f"EasyOCR failed: {type(e).__name__}: {e}") from e
