import os
import json
import boto3
from glossary import get_lang_glossary, add_corrections

MODEL_ID = "openai.gpt-oss-120b-1:0"

CORRECTION_PROMPT = """You are a medical translation post-editor specializing in IFU (Instructions for Use) documents.

A neural machine translation model has translated the following English medical text to {target_language}. Your tasks:
1. Using the terminology glossary below as a reference, fix any terms that were mistranslated.
2. Identify any additional terminology errors and ensure the tone is strictly professional, clinical, and compliant with regulatory frameworks (e.g., EU MDR, FDA, ISO).

Only fix terminology and tone. Do not restructure unnecessarily. Change as little as possible.
{glossary_section}

Return a JSON object with exactly this structure:
{{
  "corrected": "the corrected {target_language} translation (return unchanged if no corrections needed)",
  "new_issues": [
    {{
      "original": "English term from the source",
      "correct": "correct {target_language} translation for this term"
    }}
  ]
}}

SOURCE (English):
{source}

NLLB TRANSLATION ({target_language}):
{translation}

Respond with only the JSON object, no additional text."""


def _get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )


def correct_translation(
    source: str,
    translation: str,
    target_lang: str,
    target_lang_name: str,
) -> dict:
    """
    Post-edit an NLLB translation using Bedrock with the glossary as context.
    Returns { corrected: str, new_issues: [{original, correct}] }
    Auto-saves any newly found issues to the glossary.
    """
    lang_pair = f"en-{target_lang}"
    glossary = get_lang_glossary(lang_pair)

    if glossary:
        entries = "\n".join(f"  {en} → {tgt}" for en, tgt in glossary.items())
        glossary_section = (
            f"\nTERMINOLOGY GLOSSARY (English → {target_lang_name}):\n"
            f"{entries}\n"
            f"Apply these terms exactly where they appear in the translation.\n"
        )
    else:
        glossary_section = f"\nNo glossary entries yet for English → {target_lang_name}.\n"

    prompt = CORRECTION_PROMPT.format(
        target_language=target_lang_name,
        glossary_section=glossary_section,
        source=source[:8000],
        translation=translation[:8000],
    )

    response = _get_bedrock_client().converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )

    content = response["output"]["message"]["content"]
    text_block = next((c for c in content if "text" in c), None)
    if text_block is None:
        raise ValueError("No text block in Bedrock response")

    raw_text = text_block["text"].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    result = _parse_bedrock_json(raw_text, translation)

    new_issues = result.get("new_issues", [])
    if new_issues:
        add_corrections(new_issues, lang_pair)

    return {
        "corrected": result.get("corrected", translation),
        "new_issues": new_issues,
    }


def _parse_bedrock_json(raw_text: str, fallback_translation: str) -> dict:
    """
    Parse Bedrock JSON response robustly.
    Bedrock sometimes returns unescaped quotes or newlines inside JSON strings
    which breaks standard json.loads. Falls back to the original translation
    rather than crashing the whole correction step.
    """
    # Attempt 1: standard parse
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # Attempt 2: extract just the corrected field with regex
    # Handles cases where the JSON is otherwise malformed but the corrected text is there
    import re
    match = re.search(r'"corrected"\s*:\s*"(.*?)"(?:\s*,|\s*})', raw_text, re.DOTALL)
    if match:
        corrected = match.group(1).replace('\\"', '"').replace('\\n', ' ')
        return {"corrected": corrected, "new_issues": []}

    # Attempt 3: give up on correction, return original — don't crash the request
    return {"corrected": fallback_translation, "new_issues": []}
