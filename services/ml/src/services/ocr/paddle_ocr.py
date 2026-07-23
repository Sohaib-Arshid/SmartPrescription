from __future__ import annotations

import gc
import logging
import os
import time
import traceback
from dataclasses import dataclass, field

import cv2
import numpy as np
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

_ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang="en",
    text_det_limit_side_len=640,
    text_det_limit_type="max",
)

_MIN_SCORE = 0.35

# PP-OCRv5_mobile_det uses limit_side_len=960 internally.
# However on machines with limited RAM (~1-2 GB total), PaddleOCR's NormalizeImage
# transform allocates float32 buffers (4× uint8 size) that cannot be satisfied
# even at 960px when system RAM is fragmented at 96%+ usage.
# At 480px: float32 buffer = ~2 MB  → fits even in heavily fragmented RAM.
# OCR accuracy is preserved: text characters are 20-40px tall at this resolution.
_PADDLE_MAX_DIM = 480


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


def _resize_for_paddle(image_path: str) -> tuple[str, bool]:
    """
    Resize image for PaddleOCR using PIL (not cv2) to avoid allocating the
    full decompressed buffer in RAM.  PIL uses JPEG DCT shortcuts and only
    decompresses to the target size, keeping peak RAM proportional to the
    OUTPUT not the original.
    """
    from PIL import Image as _PIL

    with _PIL.open(image_path) as pil_img:
        w, h = pil_img.size
        if max(w, h) <= _PADDLE_MAX_DIM:
            return image_path, False

        pil_img.thumbnail((_PADDLE_MAX_DIM, _PADDLE_MAX_DIM), _PIL.LANCZOS)
        pil_rgb = pil_img.convert("RGB")

        base, ext = os.path.splitext(image_path)
        safe_ext = ext.lower() if ext.lower() in (".jpg", ".jpeg", ".png", ".bmp") else ".jpg"
        tmp_path = (base + f"_paddle{safe_ext}").replace("\\", "/")

        save_kwargs = {"quality": 92} if safe_ext in (".jpg", ".jpeg") else {}
        pil_rgb.save(tmp_path, **save_kwargs)

    logger.debug(
        "Resized for PaddleOCR: %dx%d → %s → %s",
        w, h, f"{pil_rgb.size[0]}x{pil_rgb.size[1]}", tmp_path,
    )
    return tmp_path, True


def extract_result(image_path: str) -> PaddleResult:
    image_path = _normalize_path(image_path)
    _validate_image(image_path)

    paddle_path, is_temp = _resize_for_paddle(image_path)
    last_exc: Exception | None = None

    try:
        for attempt in range(2):
            try:
                raw = _ocr.predict(paddle_path)
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

                gc.collect()
                return result

            except Exception as exc:
                last_exc = exc
                logger.warning("PaddleOCR attempt %d failed: %s", attempt + 1, exc)
                traceback.print_exc()
                gc.collect()
                time.sleep(0.5)

    finally:
        if is_temp and os.path.exists(paddle_path):
            try:
                os.remove(paddle_path)
            except OSError:
                pass

    raise RuntimeError(
        f"PaddleOCR failed after 2 attempts: "
        f"{type(last_exc).__name__}: {last_exc}"
    )


def extract_text(image_path: str) -> str:
    return extract_result(image_path).text
