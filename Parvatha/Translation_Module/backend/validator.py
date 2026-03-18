import os
import json
import boto3
from typing import Optional
from glossary import get_lang_glossary

MODEL_ID = "openai.gpt-oss-120b-1:0"

VALIDATION_PROMPT = """You are a medical translation quality expert. You will evaluate an English-to-{target_language} translation of an IFU (Instructions for Use) document.

{glossary}
Here is a batch of {batch_size} translated segments. For each segment, evaluate:
1. Translation Accuracy: Does the {target_language} translation faithfully convey the same meaning as the English source in a professional, formal medical tone?
2. Regulatory & Medical Terminology: Are medical terms explicitly compliant with strict medical regulatory frameworks (e.g., EU MDR, FDA, ISO standards) and standard {target_language} clinical vocabulary?

Identify every specific term, phrase, or sentence that was mistranslated or is sub-optimal. 
If there are no issues for a segment, return an empty array for its corrections.

Return your response as a JSON object containing a "results" array. The array must contain exactly {batch_size} objects, perfectly matching the order of the inputs.
Format:
{{
  "results": [
    {{
      "result": "PASS" or "FAIL",
      "accuracy_note": "one sentence explanation",
      "terminology_note": "one sentence explanation",
      "corrections": [
        {{
          "original": "English term or phrase",
          "mistranslated": "incorrect {target_language} used",
          "correct": "correct {target_language} term or phrase",
          "context": "why this matters"
        }}
      ]
    }}
  ]
}}

SEGMENTS TO VALIDATE:
{segments_json}

Respond with only the JSON object, no additional text."""

def _get_bedrock_client():
    return boto3.client(
        service_name="bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

def validate_translation_batch(
    sources: list[str],
    translations: list[str],
    target_lang_name: str,
    target_lang: str = "en",
) -> dict:
    if not sources:
        return {"results": []}

    client = _get_bedrock_client()
    
    # Load glossary for the language pair
    lang_pair = f"en-{target_lang}"
    glossary = get_lang_glossary(lang_pair)
    
    glossary_section = ""
    if glossary:
        entries = "\n".join(f"  {en} → {tgt}" for en, tgt in glossary.items())
        glossary_section = f"\n\nMANDATORY TERMINOLOGY GLOSSARY (English → {target_lang_name}):\n{entries}\n\nYou MUST use these exact terms in your validation. Any deviation from these terms should be flagged as an error.\n"
    
    # Bundle into structured text
    bundled_segments = []
    for i, (src, tgt) in enumerate(zip(sources, translations)):
        bundled_segments.append({
            "index": i,
            "source_english": src,
            "translation_target": tgt
        })
        
    segments_json = json.dumps(bundled_segments, indent=2, ensure_ascii=False)
    
    prompt = VALIDATION_PROMPT.format(
        target_language=target_lang_name,
        batch_size=len(sources),
        segments_json=segments_json,
        glossary=glossary_section,
    )

    response = client.converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )

    content = response["output"]["message"]["content"]
    text_block = next((c for c in content if "text" in c), None)
    if text_block is None:
        raise ValueError(f"No text block in Bedrock response: {content}")
    raw_text = text_block["text"].strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        parsed = json.loads(raw_text)
        # Ensure it always has a results array even if LLM slightly hallucinates format
        if "results" not in parsed:
            return {"results": [parsed] if isinstance(parsed, dict) else parsed}
        return parsed
    except json.JSONDecodeError:
        print(f"[VALIDATION ERROR] Failed to parse GPT output. Raw text:\n{raw_text}")
        return {"results": [{"result": "ERROR", "accuracy_note": "Failed to parse API response", "terminology_note": "", "corrections": []} for _ in sources]}
