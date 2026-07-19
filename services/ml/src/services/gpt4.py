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
            temperature=0,
        )
    except OpenAIError as e:
        logger.error("OpenAI request failed: %s", e)
        raise PrescriptionParseError("Failed to get a response from GPT") from e

    output = response.output_text.strip()

    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        logger.error("GPT returned invalid JSON: %s", output)
        raise PrescriptionParseError(f"GPT returned invalid JSON:\n{output}") from e