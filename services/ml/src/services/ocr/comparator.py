import re
from dataclasses import dataclass

from src.services.ocr.paddle_ocr import extract_text as paddle_extract
from src.services.ocr.easy_ocr import extract_text as easy_extract


MEDICINE_HINTS = [
    "tab",
    "tablet",
    "cap",
    "capsule",
    "syrup",
    "inj",
    "drop",
    "cream",
    "ointment",
    "mg",
    "ml",
    "mcg",
    "bd",
    "tid",
    "qid",
    "hs",
    "od",
    "sos",
]


@dataclass
class OCRResult:
    engine: str
    text: str
    score: int


def score_text(text: str) -> int:

    if not text:
        return 0

    score = 0

    words = text.split()

    # total length
    score += len(text)

    # number of words
    score += len(words) * 2

    # medicine keywords
    lower = text.lower()

    for word in MEDICINE_HINTS:
        if word in lower:
            score += 30

    # dosage patterns

    score += len(re.findall(r"\d+\s?mg", lower)) * 20
    score += len(re.findall(r"\d+\s?ml", lower)) * 20
    score += len(re.findall(r"\d+x", lower)) * 10
    score += len(re.findall(r"\d+-\d+-\d+", lower)) * 15

    # alphabet ratio

    letters = len(re.findall(r"[A-Za-z]", text))

    score += letters

    return score


def compare_ocr(image_path: str) -> OCRResult:

    paddle_text = ""
    easy_text = ""

    try:
        paddle_text = paddle_extract(image_path)
    except Exception:
        paddle_text = ""

    try:
        easy_text = easy_extract(image_path)
    except Exception:
        easy_text = ""

    paddle = OCRResult(
        engine="PaddleOCR",
        text=paddle_text,
        score=score_text(paddle_text),
    )

    easy = OCRResult(
        engine="EasyOCR",
        text=easy_text,
        score=score_text(easy_text),
    )

    if paddle.score >= easy.score:
        return paddle

    return easy