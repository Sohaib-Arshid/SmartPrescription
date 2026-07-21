import logging
from dataclasses import dataclass

from src.services.enhance.enhance import generate_enhanced_images
from src.services.ocr.easy_ocr import extract_text as easy_extract
from src.services.ocr.paddle_ocr import extract_text as paddle_extract

logger = logging.getLogger(__name__)

# EasyOCR on CPU takes ~10-15s per image. Running it on every variant would
# make a single request take 60-90s. We run PaddleOCR on all variants (fast),
# rank the results, then run EasyOCR only on the top N variants by text length
# as a proxy for image quality. This keeps total latency acceptable while still
# getting EasyOCR's complementary character recognition where it matters most.
EASY_OCR_TOP_N = 2


@dataclass
class OCRCandidate:
    image_type: str
    engine: str
    image_path: str
    text: str


def _run_paddle(image_type: str, image_path: str) -> OCRCandidate | None:
    try:
        text = paddle_extract(image_path)
        logger.info("[PaddleOCR] %-12s -> %d chars", image_type, len(text))
        return OCRCandidate(image_type=image_type, engine="PaddleOCR",
                            image_path=image_path, text=text)
    except Exception:
        logger.exception("PaddleOCR failed on %s", image_type)
        return None


def _run_easy(image_type: str, image_path: str) -> OCRCandidate | None:
    try:
        text = easy_extract(image_path)
        logger.info("[EasyOCR]   %-12s -> %d chars", image_type, len(text))
        return OCRCandidate(image_type=image_type, engine="EasyOCR",
                            image_path=image_path, text=text)
    except Exception:
        logger.exception("EasyOCR failed on %s", image_type)
        return None


def run_ocr_pipeline(image_path: str, save_dir: str) -> list[OCRCandidate]:
    enhanced = generate_enhanced_images(image_path, save_dir=save_dir)

    paddle_results: list[OCRCandidate] = []
    for image_type, img_path in enhanced.items():
        candidate = _run_paddle(image_type, img_path)
        if candidate:
            paddle_results.append(candidate)

    # Select the top-N variants by text length for EasyOCR
    top_variants = sorted(paddle_results, key=lambda c: len(c.text), reverse=True)
    easy_targets = top_variants[:EASY_OCR_TOP_N]

    easy_results: list[OCRCandidate] = []
    for candidate in easy_targets:
        result = _run_easy(candidate.image_type, candidate.image_path)
        if result:
            easy_results.append(result)

    all_results = paddle_results + easy_results

    logger.info(
        "OCR pipeline done: %d paddle + %d easy = %d total candidates",
        len(paddle_results), len(easy_results), len(all_results),
    )

    return all_results
