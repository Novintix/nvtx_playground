import re
from typing import Dict

def _clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def patch_triage_summary(notes: Dict) -> Dict:
    """
    Make the triage summary consistent with structured notes.
    If duration exists in notes, ensure summary includes it (and never says unknown).
    """
    summary = _clean_text(notes.get("triage_summary", ""))

    duration = _clean_text(str(notes.get("duration", "")))
    if duration:
        # Remove any "duration ... unknown" phrases
        summary = re.sub(r"duration[^.]*unknown\.?", "", summary, flags=re.IGNORECASE).strip()
        summary = re.sub(r"\s+\|\s+", " | ", summary).strip()

        # Append duration safely if not already present
        if "duration" not in summary.lower() or duration.lower() not in summary.lower():
            if summary and not summary.endswith("."):
                summary += "."
            summary += f" Duration: {duration}."

    notes["triage_summary"] = _clean_text(summary)
    return notes
