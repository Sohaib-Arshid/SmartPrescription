from __future__ import annotations

import re
import unicodedata

from rapidfuzz import process as rf_process
from rapidfuzz.distance import JaroWinkler

_MEDICINES: list[str] = [
    "Acetaminophen", "Acyclovir", "Albendazole", "Albuterol", "Alendronate",
    "Allopurinol", "Alprazolam", "Amitriptyline", "Amlodipine", "Amoxicillin",
    "Amoxicillin-Clavulanate", "Ampicillin", "Atenolol", "Atorvastatin",
    "Azithromycin", "Baclofen", "Beclomethasone", "Betamethasone", "Bisoprolol",
    "Budesonide", "Bupropion", "Calcium Carbonate", "Captopril", "Carbamazepine",
    "Cetirizine", "Chloramphenicol", "Chlorpheniramine", "Ciprofloxacin",
    "Clarithromycin", "Clindamycin", "Clobetasol", "Clonazepam", "Cloxacillin",
    "Co-Amoxiclav", "Codeine", "Cotrimoxazole", "Dexamethasone", "Diazepam",
    "Diclofenac", "Digoxin", "Diltiazem", "Doxycycline", "Enalapril",
    "Erythromycin", "Esomeprazole", "Ethambutol", "Fexofenadine", "Fluconazole",
    "Fluoxetine", "Fluvoxamine", "Folic Acid", "Furosemide", "Gabapentin",
    "Gentamicin", "Glibenclamide", "Gliclazide", "Glimepiride", "Glipizide",
    "Haloperidol", "Hydralazine", "Hydrocortisone", "Hydroxychloroquine",
    "Ibuprofen", "Insulin", "Ipratropium", "Iron Supplements", "Isoniazid",
    "Isosorbide", "Ivermectin", "Ketoconazole", "Labetalol", "Lansoprazole",
    "Levodopa", "Levofloxacin", "Levothyroxine", "Linezolid", "Lisinopril",
    "Lithium", "Loperamide", "Loratadine", "Lorazepam", "Losartan", "Metformin",
    "Methocarbamol", "Methylprednisolone", "Metoclopramide", "Metoprolol",
    "Metronidazole", "Miconazole", "Midazolam", "Mometasone", "Montelukast",
    "Morphine", "Moxifloxacin", "Naproxen", "Nevirapine", "Nifedipine",
    "Nitrofurantoin", "Norfloxacin", "Nystatin", "Ofloxacin", "Omeprazole",
    "Ondansetron", "Oxytetracycline", "Pantoprazole", "Paracetamol",
    "Paroxetine", "Penicillin", "Phenobarbitone", "Phenytoin", "Pioglitazone",
    "Piroxicam", "Praziquantel", "Prednisolone", "Prednisone", "Pregabalin",
    "Promethazine", "Propranolol", "Pyrazinamide", "Pyridoxine", "Quinine",
    "Rabeprazole", "Ranitidine", "Rifampicin", "Risperidone", "Ritonavir",
    "Rosuvastatin", "Salbutamol", "Sertraline", "Simvastatin", "Sodium Valproate",
    "Spironolactone", "Streptomycin", "Sulfamethoxazole", "Tamoxifen",
    "Tenofovir", "Tetracycline", "Tinidazole", "Tramadol", "Trimethoprim",
    "Valproic Acid", "Venlafaxine", "Verapamil", "Warfarin", "Zidovudine",
    "Zinc Supplements", "Zolpidem",
]

_MEDICINE_LOWER: list[str] = [m.lower() for m in _MEDICINES]

_MIN_TOKEN_LEN = 4
_CORRECTION_THRESHOLD = 82.0
_HIGH_CONFIDENCE_THRESHOLD = 92.0

_NON_ALPHA = re.compile(r"[^a-zA-Z\- ]")
_MULTI_SPACE = re.compile(r" {2,}")


def _ascii_lower(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def correct_word(token: str) -> tuple[str, float]:
    if len(token) < _MIN_TOKEN_LEN:
        return token, 100.0

    token_lower = _ascii_lower(token)

    if token_lower in _MEDICINE_LOWER:
        idx = _MEDICINE_LOWER.index(token_lower)
        return _MEDICINES[idx], 100.0

    match = rf_process.extractOne(
        token_lower,
        _MEDICINE_LOWER,
        scorer=JaroWinkler.similarity,
        score_cutoff=_CORRECTION_THRESHOLD / 100.0,
    )

    if match is None:
        return token, 0.0

    best_lower, sim, idx = match
    confidence = sim * 100.0
    return _MEDICINES[idx], confidence


def correct_medical_text(text: str) -> str:
    tokens = text.split()
    corrected: list[str] = []

    for token in tokens:
        clean = _NON_ALPHA.sub("", token)
        if len(clean) < _MIN_TOKEN_LEN:
            corrected.append(token)
            continue

        replacement, confidence = correct_word(clean)
        if confidence >= _CORRECTION_THRESHOLD:
            corrected.append(replacement)
        else:
            corrected.append(token)

    result = " ".join(corrected)
    return _MULTI_SPACE.sub(" ", result).strip()


def normalize_medicine_name(name: str) -> str:
    replacement, confidence = correct_word(name.strip())
    if confidence >= _HIGH_CONFIDENCE_THRESHOLD:
        return replacement
    return name
