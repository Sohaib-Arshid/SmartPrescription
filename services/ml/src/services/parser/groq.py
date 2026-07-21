import json
import logging
from typing import Any

from groq import Groq

from src.config.settings import GROQ_API_KEY
from src.services.parser.prompt import build_prompt

logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)


class PrescriptionParseError(Exception):
    pass


def parse_prescription(raw_text: str) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text must be a non-empty string")

    prompt = build_prompt(raw_text)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert medical prescription parser. "
                        "Return ONLY valid JSON. Never explain anything."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={"type": "json_object"},
        )

        output = response.choices[0].message.content.strip()

        if not output:
            raise PrescriptionParseError("Groq returned an empty response.")

        return json.loads(output)

    except json.JSONDecodeError as e:
        logger.exception("Invalid JSON returned by Groq")
        raise PrescriptionParseError(
            "Groq returned invalid JSON."
        ) from e

    except Exception as e:
        logger.exception("Groq API Error")
        raise PrescriptionParseError(
            f"Failed to communicate with Groq: {e}"
        ) from e