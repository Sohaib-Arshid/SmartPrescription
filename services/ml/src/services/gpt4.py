import json
import logging
from typing import Any

from openai import OpenAI, OpenAIError

from src.config.settings import OPENAI_API_KEY
from src.services.prompt import build_prompt

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


class PrescriptionParseError(Exception):
    pass


def parse_prescription(raw_text: str) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise ValueError("raw_text must be a non-empty string")

    prompt = build_prompt(raw_text)

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )

        output = response.output_text.strip()

        if not output:
            raise PrescriptionParseError("GPT returned an empty response.")

        return json.loads(output)

    except json.JSONDecodeError as e:
        logger.exception("Invalid JSON returned by GPT")
        raise PrescriptionParseError(
            "GPT returned invalid JSON."
        ) from e

    except OpenAIError as e:
        logger.exception("OpenAI API Error")
        raise PrescriptionParseError(
            "Failed to communicate with OpenAI."
        ) from e

    except Exception as e:
        logger.exception("Unexpected GPT parsing error")
        raise PrescriptionParseError(str(e)) from e