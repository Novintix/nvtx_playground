import json
from pathlib import Path

GLOSSARY_PATH = Path(__file__).parent / "glossary.json"


def load_glossary() -> dict:
    """Load full glossary. Structure: { "en-fr": { "term": "translation" }, ... }"""
    if not GLOSSARY_PATH.exists():
        return {}
    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_glossary(glossary: dict) -> None:
    with open(GLOSSARY_PATH, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False, indent=2)


def get_lang_glossary(lang_pair: str) -> dict[str, str]:
    """Return glossary entries for a specific language pair e.g. 'en-fr'."""
    return load_glossary().get(lang_pair, {})


def add_corrections(corrections: list[dict], lang_pair: str) -> int:
    """
    Merge corrections into the glossary for a specific language pair.
    Each correction: { "original": English term, "correct": target language term }
    Last write wins. Returns number of entries added/updated.
    """
    glossary = load_glossary()
    if lang_pair not in glossary:
        glossary[lang_pair] = {}
    count = 0
    for c in corrections:
        original = c.get("original", "").strip()
        correct = c.get("correct", "").strip()
        if original and correct:
            glossary[lang_pair][original] = correct
            count += 1
    save_glossary(glossary)
    return count
