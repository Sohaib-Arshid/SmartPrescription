import logging
import os
import traceback

import cv2
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

# Load only once
ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="en",
)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _validate_image(image_path: str):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if os.path.getsize(image_path) == 0:
        raise ValueError("Image is empty")

    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Unable to read image")

    h, w = img.shape[:2]

    if h < 20 or w < 20:
        raise ValueError("Image too small")

    return img


def extract_text(image_path: str) -> str:
    image_path = _normalize_path(image_path)

    _validate_image(image_path)

    last_exception = None

    for attempt in range(2):

        try:

            result = ocr.predict(image_path)

            texts = []

            for page in result:

                rec_texts = page.get("rec_texts", [])
                rec_scores = page.get("rec_scores", [])

                for text, score in zip(rec_texts, rec_scores):

                    text = text.strip()

                    if not text:
                        continue

                    # Handwritten prescriptions produce lower confidence scores;
                    # 0.35 retains borderline-legible text without drowning in noise.
                    if score < 0.35:
                        continue

                    texts.append(text)

            # Remove duplicates while preserving order
            texts = list(dict.fromkeys(texts))

            return " ".join(texts).strip()

        except Exception as e:

            last_exception = e

            logger.warning(
                "OCR attempt %s failed: %s",
                attempt + 1,
                str(e),
            )

            traceback.print_exc()

    raise RuntimeError(
        f"PaddleOCR failed after 2 attempts.\n"
        f"{type(last_exception).__name__}: {last_exception}"
    )