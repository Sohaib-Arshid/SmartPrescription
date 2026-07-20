import logging
import os

import cv2
import easyocr

logger = logging.getLogger(__name__)

# Create reader once
reader = easyocr.Reader(
    ["en"],
    gpu=False,
)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _validate_image(image_path: str) -> None:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if os.path.getsize(image_path) == 0:
        raise ValueError(f"Image is empty: {image_path}")

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Unable to decode image: {image_path}")


def extract_text(image_path: str) -> str:
    image_path = _normalize_path(image_path)

    _validate_image(image_path)

    try:
        result = reader.readtext(
            image_path,
            detail=1,
            paragraph=True,
        )

        texts = []

        for item in result:
            text = item[1].strip()

            if text:
                texts.append(text)

        return " ".join(texts)

    except Exception as e:
        logger.exception("EasyOCR failed")

        raise RuntimeError(
            f"EasyOCR failed: {type(e).__name__}: {e}"
        ) from e