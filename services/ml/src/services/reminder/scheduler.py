from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Standard reminder times for each frequency abbreviation.
# Times are in HH:MM 24-hour format.
_FREQUENCY_SCHEDULES: dict[str, list[str]] = {
    "OD":  ["08:00"],
    "BD":  ["08:00", "20:00"],
    "TID": ["08:00", "14:00", "20:00"],
    "QID": ["08:00", "12:00", "16:00", "20:00"],
    "HS":  ["22:00"],
    "SOS": [],
}


def generate_reminders(medicines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reminders: list[dict[str, Any]] = []

    for med in medicines:
        name = med.get("name")
        if not name:
            continue

        frequency_raw: str | None = med.get("frequency")
        if not frequency_raw:
            continue

        frequency = frequency_raw.strip().upper()
        times = _FREQUENCY_SCHEDULES.get(frequency)

        if times is None:
            # Unknown abbreviation — try to infer from descriptive text
            times = _infer_times(frequency_raw)

        for time in times:
            reminders.append({
                "medicine": name,
                "time": time,
                "frequency": frequency_raw,
                "dosage": med.get("dosage"),
                "duration": med.get("duration"),
                "timing": med.get("timing"),
            })

    return reminders


def _infer_times(frequency_text: str) -> list[str]:
    lower = frequency_text.lower()

    if "once" in lower or "daily" in lower:
        return ["08:00"]
    if "twice" in lower:
        return ["08:00", "20:00"]
    if "three" in lower or "thrice" in lower or "3" in lower:
        return ["08:00", "14:00", "20:00"]
    if "four" in lower or "4" in lower:
        return ["08:00", "12:00", "16:00", "20:00"]
    if "night" in lower or "bedtime" in lower or "sleep" in lower:
        return ["22:00"]

    return []
