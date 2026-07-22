from __future__ import annotations

import re
from difflib import SequenceMatcher

from src.services.ocr.runner import OCRCandidate

_SIMILARITY_THRESHOLD = 0.82

_MEDICINE_WORDS = frozenset({
    "tab", "tablet", "cap", "capsule", "mg", "ml", "mcg",
    "syrup", "inj", "drop", "cream", "ointment",
    "od", "bd", "tid", "qid", "hs", "sos",
})

_WHITESPACE = re.compile(r'\s+')
_NORM_STRIP = re.compile(r'[^a-z0-9()/.\- ]')
_MG = re.compile(r'\d+\s*mg', re.IGNORECASE)
_ML = re.compile(r'\d+\s*ml', re.IGNORECASE)
_MCG = re.compile(r'\d+\s*mcg', re.IGNORECASE)
_FREQ = re.compile(r'\b(?:od|bd|tid|qid|hs|sos)\b', re.IGNORECASE)

_LINE_SPLIT = re.compile(r'\n')


def _normalize(s: str) -> str:
    return _NORM_STRIP.sub('', _WHITESPACE.sub(' ', s.lower())).strip()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _is_useful(line: str) -> bool:
    line = line.strip()
    return len(line) >= 3 and sum(c.isalpha() for c in line) >= 2


def _medical_weight(line: str) -> float:
    lower = line.lower()
    score = float(len(line))
    score += sum(12.0 for w in _MEDICINE_WORDS if w in lower)
    score += len(_MG.findall(lower)) * 20.0
    score += len(_ML.findall(lower)) * 20.0
    score += len(_MCG.findall(lower)) * 20.0
    score += len(_FREQ.findall(lower)) * 15.0
    return score


def _candidate_weight(candidate: OCRCandidate) -> float:
    base = 1.0
    if candidate.engine == "PaddleOCR" and candidate.words:
        base = 0.5 + candidate.avg_confidence
    elif candidate.engine == "EasyOCR":
        base = 0.85
    return base


def _split_lines(text: str) -> list[str]:
    return [seg.strip() for seg in _LINE_SPLIT.split(text) if seg.strip()]


def fuse_ocr(candidates: list[OCRCandidate]) -> str:
    if not candidates:
        return ""

    weighted_lines: list[tuple[str, float]] = []
    for candidate in candidates:
        cw = _candidate_weight(candidate)
        for line in _split_lines(candidate.text):
            if _is_useful(line):
                weighted_lines.append((line, cw))

    unique: list[str] = []
    unique_weights: list[float] = []

    for line, weight in weighted_lines:
        matched_idx = next(
            (i for i, saved in enumerate(unique)
             if _similarity(line, saved) >= _SIMILARITY_THRESHOLD),
            None,
        )
        if matched_idx is None:
            unique.append(line)
            unique_weights.append(weight * _medical_weight(line))
        else:
            new_score = weight * _medical_weight(line)
            if new_score > unique_weights[matched_idx]:
                unique[matched_idx] = line
                unique_weights[matched_idx] = new_score

    paired = sorted(zip(unique_weights, unique), reverse=True)
    return '\n'.join(line for _, line in paired)
