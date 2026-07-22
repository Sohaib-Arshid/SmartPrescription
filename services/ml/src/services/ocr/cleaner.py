from __future__ import annotations

import re
import unicodedata

_MULTI_SPACE = re.compile(r" {2,}")
_GARBAGE_CHARS = re.compile(r'[^\w\s.,\(\)\[\]\-/+%:\'"@]')
_OCR_ARTIFACTS = re.compile(r'(?<!\w)[|\\!#$^&*~`]{1,3}(?!\w)')
_REPEATED_PUNCT = re.compile(r'([.,\-])\1{2,}')

_SPACED_DIGITS = re.compile(r'(\d)((?:\s+\d)+)(?=\s*(?:m\s*g|m\s*l|m\s*c\s*g|g\s*m)\b)', re.IGNORECASE)

_DOSAGE_NORM: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'(\d+)\s*m\s*g\b', re.IGNORECASE), r'\1mg'),
    (re.compile(r'(\d+)\s*m\s*l\b', re.IGNORECASE), r'\1ml'),
    (re.compile(r'(\d+)\s*m\s*c\s*g\b', re.IGNORECASE), r'\1mcg'),
    (re.compile(r'(\d+)\s*g\s*m\b', re.IGNORECASE), r'\1gm'),
    (re.compile(r'\b0+(\d+)', re.IGNORECASE), r'\1'),
]

_FREQUENCY_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'\b(o\.?d\.?|once\s+daily|1\s*x\s*daily)\b', re.IGNORECASE), 'OD'),
    (re.compile(r'\b(b\.?d\.?|twice\s+daily|2\s*x\s*daily|bis\s+in\s+die)\b', re.IGNORECASE), 'BD'),
    (re.compile(r'\b(t\.?i\.?d\.?|three\s+times\s+daily|3\s*x\s*daily|ter\s+in\s+die)\b', re.IGNORECASE), 'TID'),
    (re.compile(r'\b(q\.?i\.?d\.?|four\s+times\s+daily|4\s*x\s*daily)\b', re.IGNORECASE), 'QID'),
    (re.compile(r'\b(h\.?s\.?|at\s+bedtime|at\s+night|nocte)\b', re.IGNORECASE), 'HS'),
    (re.compile(r'\b(s\.?o\.?s\.?|as\s+needed|when\s+required|prn)\b', re.IGNORECASE), 'SOS'),
]

_OCR_CHAR_FIXES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'\bl\b(?=\s*\d)', re.IGNORECASE), '1'),
    (re.compile(r'\bO\b(?=\s*\d)'), '0'),
    (re.compile(r'(?<=\d)\s*O\b'), '0'),
    (re.compile(r'(?<=\d)\s*l\b', re.IGNORECASE), '1'),
    (re.compile(r'(?<=\d)o(?=m?g\b)', re.IGNORECASE), '0'),
    (re.compile(r'(?<=\d)O(?=m?g\b)'), '0'),
]


def clean_medical_text(text: str) -> str:
    if not text:
        return text

    text = unicodedata.normalize('NFKC', text)
    text = _OCR_ARTIFACTS.sub(' ', text)
    text = _REPEATED_PUNCT.sub(r'\1', text)
    text = _GARBAGE_CHARS.sub(' ', text)

    for pattern, replacement in _OCR_CHAR_FIXES:
        text = pattern.sub(replacement, text)

    text = _SPACED_DIGITS.sub(lambda m: re.sub(r'\s', '', m.group(0)), text)

    for pattern, replacement in _DOSAGE_NORM:
        text = pattern.sub(replacement, text)

    for pattern, replacement in _FREQUENCY_MAP:
        text = pattern.sub(replacement, text)

    lines = [
        _MULTI_SPACE.sub(' ', line).strip()
        for line in text.splitlines()
    ]
    return '\n'.join(line for line in lines if line)
