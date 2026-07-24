from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from src.services.enhance.enhance import generate_enhanced_images
from src.services.ocr.easy_ocr import extract_text as easy_extract
from src.services.ocr.paddle_ocr import PaddleWord, extract_result as paddle_extract_result

logger = logging.getLogger(__name__)

EASY_OCR_TOP_N = 2

_MEDICAL_SCORE_HINTS = frozenset({
    "mg", "ml", "mcg", "tab", "cap", "od", "bd", "tid", "qid", "hs", "sos",
    "tablet", "capsule", "syrup", "inj", "drop", "cream",
})
_DOSAGE_RE = re.compile(r'\d+\s*(?:mg|ml|mcg|gm)\b', re.IGNORECASE)
_FREQ_RE = re.compile(r'\b(?:od|bd|tid|qid|hs|sos)\b', re.IGNORECASE)


@dataclass
class OCRCandidate:
    image_type: str
    engine: str
    image_path: str
    text: str
    words: list[PaddleWord] = field(default_factory=list)

    @property
    def avg_confidence(self) -> float:
        if not self.words:
            return 0.0
        return sum(w.score for w in self.words) / len(self.words)

    @property
    def medical_score(self) -> float:
        lower = self.text.lower()
        hint_count = sum(1 for h in _MEDICAL_SCORE_HINTS if h in lower)
        dosage_count = len(_DOSAGE_RE.findall(lower))
        freq_count = len(_FREQ_RE.findall(lower))
        return (hint_count * 10.0) + (dosage_count * 20.0) + (freq_count * 15.0)


def _run_paddle(image_type: str, image_path: str) -> OCRCandidate | None:
    try:
        result = paddle_extract_result(image_path)
        candidate = OCRCandidate(
            image_type=image_type,
            engine="PaddleOCR",
            image_path=image_path,
            text=result.text,
            words=result.words,
        )
        logger.info(
            "[PaddleOCR] %-16s -> %d chars  avg_conf=%.2f  med_score=%.0f",
            image_type, len(result.text), candidate.avg_confidence, candidate.medical_score,
        )
        return candidate
    except Exception:
        logger.exception("PaddleOCR failed on %s", image_type)
        return None


def _run_easy(image_type: str, image_path: str) -> OCRCandidate | None:
    try:
        text = easy_extract(image_path)
        candidate = OCRCandidate(
            image_type=image_type,
            engine="EasyOCR",
            image_path=image_path,
            text=text,
        )
        logger.info(
            "[EasyOCR]   %-16s -> %d chars",
            image_type, len(text),
        )
        return candidate
    except Exception:
        logger.exception("EasyOCR failed on %s", image_type)
        return None


def _easy_ocr_priority(candidate: OCRCandidate) -> float:
    return candidate.medical_score + candidate.avg_confidence * 50.0 + len(candidate.text) * 0.1


def run_ocr_pipeline(image_path: str, save_dir: str) -> list[OCRCandidate]:
    enhanced = generate_enhanced_images(image_path, save_dir=save_dir)

    paddle_results: list[OCRCandidate] = []
    for image_type, img_path in enhanced.items():
        candidate = _run_paddle(image_type, img_path)
        if candidate:
            paddle_results.append(candidate)

    easy_targets = sorted(paddle_results, key=_easy_ocr_priority, reverse=True)[:EASY_OCR_TOP_N]

    easy_results: list[OCRCandidate] = []
    for candidate in easy_targets:
        result = _run_easy(candidate.image_type, candidate.image_path)
        if result:
            easy_results.append(result)

    all_results = paddle_results + easy_results

    logger.info(
        "OCR pipeline: %d paddle + %d easy = %d total",
        len(paddle_results), len(easy_results), len(all_results),
    )

    print("\n" + "=" * 70)
    print("OCR RESULTS")
    print("=" * 70)

    for candidate in all_results:
        print(f"\nImage Type     : {candidate.image_type}")
        print(f"Engine         : {candidate.engine}")
        print(f"Confidence     : {candidate.avg_confidence:.2f}")
        print(f"Medical Score  : {candidate.medical_score:.0f}")
        print("-" * 70)
        print(candidate.text)
        print("-" * 70)

    print("=" * 70)
    print("OCR PIPELINE COMPLETED")
    print("=" * 70)
    return all_results
