import re
from difflib import SequenceMatcher

from src.services.ocr.runner import OCRCandidate

SIMILARITY_THRESHOLD = 0.82

MEDICINE_WORDS = frozenset({
    "tab", "tablet", "cap", "capsule", "mg", "ml", "mcg",
    "syrup", "inj", "drop", "cream", "ointment",
    "od", "bd", "tid", "qid", "hs", "sos",
})

_WHITESPACE = re.compile(r"\s+")
_NON_ALLOWED = re.compile(r"[^a-z0-9()%/.\- ]")
_MG = re.compile(r"\d+\s?mg")
_ML = re.compile(r"\d+\s?ml")
_MCG = re.compile(r"\d+\s?mcg")

# Split on newlines OR on sequences that look like medicine-name boundaries:
# e.g. "Amoxicillin 500mg BD Ibuprofen 400mg" → two segments.
# We split before a capitalized word that follows a dosage/frequency token.
_SEGMENT_SPLIT = re.compile(
    r"\n|(?<=\b(?:od|bd|tid|qid|hs|sos|mg|ml|mcg|days?|tab|cap)\b)\s+(?=[A-Z])",
    re.IGNORECASE,
)


def _normalize(line: str) -> str:
    line = _WHITESPACE.sub(" ", line.lower())
    return _NON_ALLOWED.sub("", line).strip()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _is_useful(line: str) -> bool:
    line = line.strip()
    return len(line) >= 3 and sum(c.isalpha() for c in line) >= 2


def _line_score(line: str) -> int:
    lower = line.lower()
    score = len(line)
    score += sum(25 for w in MEDICINE_WORDS if w in lower)
    score += len(_MG.findall(lower)) * 20
    score += len(_ML.findall(lower)) * 20
    score += len(_MCG.findall(lower)) * 20
    return score


def _split_text(text: str) -> list[str]:
    return [seg.strip() for seg in _SEGMENT_SPLIT.split(text) if seg.strip()]


def fuse_ocr(candidates: list[OCRCandidate]) -> str:
    if not candidates:
        return ""

    lines = [
        seg
        for c in candidates
        for seg in _split_text(c.text)
        if _is_useful(seg)
    ]

    unique: list[str] = []
    for line in lines:
        matched_idx = next(
            (i for i, saved in enumerate(unique)
             if _similar(line, saved) >= SIMILARITY_THRESHOLD),
            None,
        )
        if matched_idx is None:
            unique.append(line)
        elif _line_score(line) > _line_score(unique[matched_idx]):
            unique[matched_idx] = line

    unique.sort(key=_line_score, reverse=True)
    return "\n".join(unique)
