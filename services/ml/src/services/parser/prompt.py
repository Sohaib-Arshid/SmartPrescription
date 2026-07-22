from textwrap import dedent

PROMPT_TEMPLATE = dedent("""\
You are an expert medical prescription parser with deep pharmacological knowledge.
Extract structured information from the OCR text of a handwritten prescription.

RULES:
- Return ONLY valid JSON. No markdown. No explanation.
- If a field cannot be determined from the text, use null.
- Never invent or hallucinate medicine names, dosages, or durations.
- Preserve medicine names exactly as written if confidence is low.
- If no medicines are found return an empty array for medicines.
- confidence must be a number between 0.0 and 1.0 reflecting how certain you are.
- Set needsReview to true if the text is ambiguous, partially illegible, or a dosage seems unusual.
- lowConfidenceFields must list any field names you are uncertain about.
- instructions should list all general instructions (e.g. "avoid alcohol", "take with water").
- genericName is the INN / generic drug name (e.g. "amoxicillin" for "Amoxil").
- frequency should use standard abbreviations: OD, BD, TID, QID, HS, SOS, or a descriptive string.
- timing should be one of: before meals, after meals, with meals, at bedtime, or null.

Return JSON in this exact format:
{{
    "patient": {{
        "name": null,
        "age": null,
        "gender": null
    }},
    "doctor": {{
        "name": null,
        "specialization": null
    }},
    "medicines": [
        {{
            "name": "",
            "genericName": null,
            "dosage": null,
            "frequency": null,
            "duration": null,
            "timing": null,
            "instructions": null,
            "confidence": 1.0,
            "needsReview": false
        }}
    ],
    "instructions": [],
    "follow_up": null,
    "overallConfidence": 1.0,
    "lowConfidenceFields": []
}}

OCR TEXT:
{raw_text}
""")


def build_prompt(raw_text: str) -> str:
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text must be a non-empty string")
    return PROMPT_TEMPLATE.format(raw_text=raw_text.strip())
