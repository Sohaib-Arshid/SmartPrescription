import re
from difflib import SequenceMatcher

from src.services.ocr.runner import OCRCandidate

SIMILARITY_THRESHOLD = 0.90

MEDICINE_WORDS = frozenset({
    "tab",
    "tablet",
    "cap",
    "capsule",
    "mg",
    "ml",
    "mcg",
    "syrup",
    "inj",
    "drop",
    "cream",
    "ointment",
    "od",
    "bd",
    "tid",
    "qid",
    "hs",
    "sos",
})

_WHITESPACE_PATTERN = re.compile(r"\s+")
_NON_ALLOWED_PATTERN = re.compile(r"[^a-z0-9()%/.\- ]")
_MG_PATTERN = re.compile(r"\d+\s?mg")
_ML_PATTERN = re.compile(r"\d+\s?ml")


def _normalize(line: str) -> str:
    line = line.lower()
    line = _WHITESPACE_PATTERN.sub(" ", line)
    line = _NON_ALLOWED_PATTERN.sub("", line)
    return line.strip()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        _normalize(a),
        _normalize(b),
    ).ratio()


def _is_useful(line: str) -> bool:
    line = line.strip()
    if len(line) < 3:
        return False

    letters = sum(c.isalpha() for c in line)
    return letters >= 2


def _line_score(line: str) -> int:
    score = 0
    lower = line.lower()

    for word in MEDICINE_WORDS:
        if word in lower:
            score += 25

    score += len(_MG_PATTERN.findall(lower)) * 20
    score += len(_ML_PATTERN.findall(lower)) * 20

    score += len(line)

    return score


def fuse_ocr(candidates: list[OCRCandidate]) -> str:
    if not candidates:
        return ""

    collected_lines = [
        line.strip()
        for candidate in candidates
        for line in candidate.text.splitlines()
        if _is_useful(line.strip())
    ]

    unique_lines: list[str] = []

    for line in collected_lines:
        duplicate = False

        for saved in unique_lines:
            if _similar(line, saved) >= SIMILARITY_THRESHOLD:
                duplicate = True
                if _line_score(line) > _line_score(saved):
                    unique_lines.remove(saved)
                    unique_lines.append(line)
                break

        if not duplicate:
            unique_lines.append(line)

    unique_lines.sort(key=_line_score, reverse=True)

    return "\n".join(unique_lines)