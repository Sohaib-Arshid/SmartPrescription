import logging
from dataclasses import dataclass

from src.services.enhance.enhance import generate_enhanced_images
from src.services.ocr.easy_ocr import extract_text as easy_extract
from src.services.ocr.paddle_ocr import extract_text as paddle_extract

logger = logging.getLogger(__name__)


@dataclass
class OCRCandidate:
    image_type: str
    engine: str
    image_path: str
    text: str


def _run_paddle(image_type: str, image_path: str):

    try:

        text = paddle_extract(image_path)

        logger.info(
            "[PaddleOCR] %-12s -> %d chars",
            image_type,
            len(text),
        )

        return OCRCandidate(
            image_type=image_type,
            engine="PaddleOCR",
            image_path=image_path,
            text=text,
        )

    except Exception as e:

        logger.exception(
            "PaddleOCR failed on %s : %s",
            image_type,
            e,
        )

        return None


def _run_easy(image_type: str, image_path: str):

    try:

        text = easy_extract(image_path)

        logger.info(
            "[EasyOCR]   %-12s -> %d chars",
            image_type,
            len(text),
        )

        return OCRCandidate(
            image_type=image_type,
            engine="EasyOCR",
            image_path=image_path,
            text=text,
        )

    except Exception as e:

        logger.exception(
            "EasyOCR failed on %s : %s",
            image_type,
            e,
        )

        return None


def run_ocr_pipeline(image_path: str):

    enhanced_images = generate_enhanced_images(image_path)

    results = []

    for image_type, img_path in enhanced_images.items():

        paddle = _run_paddle(image_type, img_path)

        if paddle:
            results.append(paddle)

        easy = _run_easy(image_type, img_path)

        if easy:
            results.append(easy)

    logger.info(
        "OCR Pipeline Finished. %d OCR Results Generated.",
        len(results),
    )

    return results