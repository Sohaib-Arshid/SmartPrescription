import re
from dataclasses import dataclass

from src.services.ocr.runner import OCRCandidate

MEDICINE_HINTS = frozenset({
    "tab",
    "tablet",
    "cap",
    "capsule",
    "syrup",
    "inj",
    "drop",
    "cream",
    "ointment",
    "bd",
    "tid",
    "qid",
    "hs",
    "od",
    "sos",
})

_MG_PATTERN = re.compile(r"\d+\s?mg")
_ML_PATTERN = re.compile(r"\d+\s?ml")
_MCG_PATTERN = re.compile(r"\d+\s?mcg")
_FREQUENCY_PATTERN = re.compile(r"\b(od|bd|tid|qid|hs|sos)\b")
_NUMERIC_PATTERN = re.compile(r"\d+")
_ALPHA_PATTERN = re.compile(r"[A-Za-z]")
_GARBAGE_PATTERN = re.compile(r"[^A-Za-z0-9\s.,()/\-]")


@dataclass(slots=True)
class OCRResult:
    engine: str
    image_type: str
    image_path: str
    text: str
    score: int


def score_text(text: str) -> int:
    if not text:
        return 0

    score = 0
    lower = text.lower()
    words = text.split()

    score += len(text)
    score += len(words) * 2

    for hint in MEDICINE_HINTS:
        if hint in lower:
            score += 30

    score += len(_MG_PATTERN.findall(lower)) * 20
    score += len(_ML_PATTERN.findall(lower)) * 20
    score += len(_MCG_PATTERN.findall(lower)) * 20

    score += len(_FREQUENCY_PATTERN.findall(lower)) * 15

    score += len(_NUMERIC_PATTERN.findall(lower)) * 5

    score += len(_ALPHA_PATTERN.findall(text))

    garbage = len(_GARBAGE_PATTERN.findall(text))
    score -= garbage * 3

    return score


def compare_ocr(candidates: list[OCRCandidate]) -> OCRResult:
    if not candidates:
        raise ValueError("No OCR candidates received.")

    results = [
        OCRResult(
            engine=candidate.engine,
            image_type=candidate.image_type,
            image_path=candidate.image_path,
            text=candidate.text,
            score=score_text(candidate.text),
        )
        for candidate in candidates
    ]

    results.sort(key=lambda x: x.score, reverse=True)

    return results[0]