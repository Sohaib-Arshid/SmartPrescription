from __future__ import annotations

import re
import unicodedata

_MULTI_SPACE = re.compile(r" {2,}")
_GARBAGE_CHARS = re.compile(r"[^\w\s\.\,\(\)\[\]\-\/\+\%\:\'\"]")
_OCR_ARTIFACTS = re.compile(r"(?<!\w)[|\\!@#\$\^&\*~`]{1,3}(?!\w)")
_REPEATED_PUNCT = re.compile(r"([.\-,])\1{2,}")

_DOSAGE_NORM = [
    (re.compile(r"(\d+)\s*m\s*g\b", re.IGNORECASE), r"\1mg"),
    (re.compile(r"(\d+)\s*m\s*l\b", re.IGNORECASE), r"\1ml"),
    (re.compile(r"(\d+)\s*m\s*c\s*g\b", re.IGNORECASE), r"\1mcg"),
    (re.compile(r"(\d+)\s*g\s*m\b", re.IGNORECASE), r"\1gm"),
    (re.compile(r"\b0+(\d)", re.IGNORECASE), r"\1"),
]

_FREQUENCY_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(o\.?d\.?|once\s+daily|1\s*x\s*daily)\b", re.IGNORECASE), "OD"),
    (re.compile(r"\b(b\.?d\.?|twice\s+daily|2\s*x\s*daily|bis\s+in\s+die)\b", re.IGNORECASE), "BD"),
    (re.compile(r"\b(t\.?i\.?d\.?|three\s+times\s+daily|3\s*x\s*daily|ter\s+in\s+die)\b", re.IGNORECASE), "TID"),
    (re.compile(r"\b(q\.?i\.?d\.?|four\s+times\s+daily|4\s*x\s*daily)\b", re.IGNORECASE), "QID"),
    (re.compile(r"\b(h\.?s\.?|at\s+bedtime|at\s+night|nocte)\b", re.IGNORECASE), "HS"),
    (re.compile(r"\b(s\.?o\.?s\.?|as\s+needed|when\s+required|prn)\b", re.IGNORECASE), "SOS"),
]

_COMMON_OCR_ERRORS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bl\b(?=\d)", re.IGNORECASE), "1"),
    (re.compile(r"\bO\b(?=\d)", re.IGNORECASE), "0"),
    (re.compile(r"(?<=\d)O\b", re.IGNORECASE), "0"),
    (re.compile(r"(?<=\d)l\b", re.IGNORECASE), "1"),
    (re.compile(r"\bRx\b", re.IGNORECASE), "Rx"),
    (re.compile(r"\bdosage\b", re.IGNORECASE), "dosage"),
]


def clean_medical_text(text: str) -> str:
    if not text:
        return text

    text = unicodedata.normalize("NFKC", text)
    text = _OCR_ARTIFACTS.sub(" ", text)
    text = _GARBAGE_CHARS.sub(" ", text)
    text = _REPEATED_PUNCT.sub(r"\1", text)

    for pattern, replacement in _OCR_ARTIFACTS, []:
        pass

    for pattern, replacement in _DOSAGE_NORM:
        text = pattern.sub(replacement, text)

    for pattern, replacement in _FREQUENCY_MAP:
        text = pattern.sub(replacement, text)

    for pattern, replacement in _COMMON_OCR_ERRORS:
        text = pattern.sub(replacement, text)

    lines = []
    for line in text.splitlines():
        line = _MULTI_SPACE.sub(" ", line).strip()
        if line:
            lines.append(line)

    return "\n".join(lines)
