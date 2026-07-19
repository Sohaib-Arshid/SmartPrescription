from textwrap import dedent


PROMPT_TEMPLATE = dedent("""\
You are an expert medical prescription parser.
Your task is to extract structured information from OCR text.
Rules:
- Return ONLY valid JSON.
- Do not explain anything.
- Do not wrap JSON inside markdown.
- If a field is missing use null.
- Never invent medicines.
- Preserve medicine names exactly if confidence is low.
- If no medicines are found, return an empty medicines array.
- Always return every field defined in the schema.
Return JSON in this format:
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
            "strength": null,
            "dosage": null,
            "frequency": null,
            "duration": null,
            "timing": null,
            "notes": null
        }}
    ],
    "instructions": [],
    "follow_up": null
}}
OCR TEXT:
{raw_text}
""")


def build_prompt(raw_text: str) -> str:
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text must be a non-empty string")

    return PROMPT_TEMPLATE.format(raw_text=raw_text.strip())