import json
import logging
from typing import Any

from groq import Groq

from src.config.settings import GROQ_API_KEY

logger = logging.getLogger(__name__)

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM = (
    "You are a clinical pharmacologist. Analyze the provided list of drug names "
    "for known drug-drug interactions. Return ONLY valid JSON. No explanation."
)

_PROMPT = """\
Given these medicines from a prescription: {medicines}

List all clinically significant drug-drug interactions between them.
For each interaction return:
- drugA: first drug name
- drugB: second drug name
- severity: one of "mild", "moderate", "severe"
- description: brief clinical description of the interaction

If there are no interactions return an empty array.

Return JSON:
{{
    "interactions": [
        {{
            "drugA": "",
            "drugB": "",
            "severity": "",
            "description": ""
        }}
    ]
}}
"""


def check_interactions(medicine_names: list[str]) -> list[dict[str, Any]]:
    if len(medicine_names) < 2:
        return []

    names_str = ", ".join(medicine_names)
    prompt = _PROMPT.format(medicines=names_str)

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        output = response.choices[0].message.content.strip()
        data = json.loads(output)
        return data.get("interactions", [])

    except Exception:
        logger.exception("Drug interaction check failed for: %s", names_str)
        return []
