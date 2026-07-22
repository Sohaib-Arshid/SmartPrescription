from __future__ import annotations

import logging
import os
import traceback
from dataclasses import dataclass, field

import cv2
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

_ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="en",
)

_MIN_SCORE = 0.35


@dataclass
class PaddleWord:
    text: str
    score: float


@dataclass
class PaddleResult:
    words: list[PaddleWord] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def avg_score(self) -> float:
        if not self.words:
            return 0.0
        return sum(w.score for w in self.words) / len(self.words)

    @property
    def min_score(self) -> float:
        if not self.words:
            return 0.0
        return min(w.score for w in self.words)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _validate_image(image_path: str) -> None:
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


def extract_result(image_path: str) -> PaddleResult:
    image_path = _normalize_path(image_path)
    _validate_image(image_path)

    last_exc: Exception | None = None

    for attempt in range(2):
        try:
            raw = _ocr.predict(image_path)
            result = PaddleResult()

            for page in raw:
                rec_texts = page.get("rec_texts", [])
                rec_scores = page.get("rec_scores", [])

                for text, score in zip(rec_texts, rec_scores):
                    text = text.strip()
                    if text and score >= _MIN_SCORE:
                        result.words.append(PaddleWord(text=text, score=float(score)))

            seen: dict[str, PaddleWord] = {}
            for w in result.words:
                if w.text not in seen or w.score > seen[w.text].score:
                    seen[w.text] = w
            result.words = list(seen.values())

            return result

        except Exception as exc:
            last_exc = exc
            logger.warning("PaddleOCR attempt %d failed: %s", attempt + 1, exc)
            traceback.print_exc()

    raise RuntimeError(
        f"PaddleOCR failed after 2 attempts: "
        f"{type(last_exc).__name__}: {last_exc}"
    )


def extract_text(image_path: str) -> str:
    return extract_result(image_path).text
