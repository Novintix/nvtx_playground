import sys
import io

# Set UTF-8 encoding for stdout/stderr to handle special characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import json
import requests
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# Get API tokens from environment
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

MAX_CHUNK_CHARS = 1000

# Translation mode: only AWS (gpt-oss-model-120b)
TRANSLATION_MODE = "aws"

# HuggingFace Inference API endpoint for NLLB
HF_API_URL = "https://router.huggingface.co/models/facebook/nllb-200-distilled-600M"

# Language code mapping for NLLB-200
LANGUAGE_CODES = {
    "French": "fra_Latn",
    "German": "deu_Latn",
    "Spanish": "spa_Latn",
    "Japanese": "jpn_Jpan",
    "Chinese": "zho_Hans",
    "Korean": "kor_Hang",
    "Portuguese": "por_Latn",
    "Italian": "ita_Latn",
    "Russian": "rus_Cyrl",
    "Arabic": "arb_Arab",
    "Dutch": "nld_Latn",
    "Finnish": "fin_Latn",
}

# AWS Bedrock model configuration - gpt-oss-model-120b only
AWS_MODEL_ID = "openai.gpt-oss-120b-1:0"


def _fix_reversed_text(text: str) -> str:
    """
    Detect and fix text that appears to be character-reversed.
    This is a workaround for models that output reversed text.
    """
    if not text or len(text) < 4:
        return text
    
    # Check if text appears to be reversed (common pattern: lowercase followed by uppercase at word boundaries)
    # Example: "gnilebal" -> "balancing", "ecnavdA" -> "Advantage"
    
    words = text.split()
    fixed_words = []
    
    for word in words:
        # Check if this word might be reversed
        # Heuristic: if the word has lowercase letters but starts with lowercase 
        # and the original position would make more sense
        if len(word) >= 4:
            # Try reversing and check if it looks like a valid word
            reversed_word = word[::-1]
            
            # If original has unusual patterns like "gn" at start (reversed "ng")
            # or "dA" at end (reversed "Ad"), it's likely reversed
            has_reversed_pattern = (
                word[:2] in ['gn', 'tn', 'sn', 'rn', 'ln', 'dn'] or  # reversed endings like "ing", "and"
                word[-2:] in ['dA', 'dA']  # reversed "Ad"
            )
            
            # Also check if reversing produces more valid-looking patterns
            if has_reversed_pattern:
                # Check if reversing produces valid English-like patterns
                if reversed_word[:2] not in ['gn', 'tn', 'sn'] and reversed_word[-2:] not in ['dA']:
                    fixed_words.append(reversed_word)
                    continue
        
        fixed_words.append(word)
    
    result = ' '.join(fixed_words)
    
    # If result is different and looks more reasonable, use it
    if result != text:
        print(f"[DEBUG] Fixed reversed text: '{text[:30]}...' -> '{result[:30]}...'")
    
    return result


def get_language_code(language_name: str) -> str:
    """Get the NLLB-200 language code for a given language name."""
    return LANGUAGE_CODES.get(language_name, "fra_Latn")


def _translate_via_aws_bedrock(text: str, target_lang: str = "French") -> str:
    """
    Translate text using AWS Bedrock.
    
    Args:
        text: English text to translate
        target_lang: Target language name (e.g., "French", "German")
    
    Returns:
        Translated text
    """
    try:
        # Create Bedrock Runtime client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        # Prepare the prompt for translation using chat format
        prompt = f"""Translate the following English text to {target_lang}. 
Only provide the translation, nothing else.

English: {text}

{target_lang}:"""

        # Request payload for OpenAI model on Bedrock (chat format)
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.1,
            "top_p": 0.9
        }

        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=AWS_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )

        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # DEBUG: Print raw response
        print(f"[DEBUG] Raw AWS response: {json.dumps(response_body)[:500]}...")
        
        # Extract the translated text from the response
        # OpenAI format returns 'choices' array with 'message' object
        if 'choices' in response_body and len(response_body['choices']) > 0:
            translated_text = response_body['choices'][0].get('message', {}).get('content', '')
            translated_text = translated_text.strip()
        else:
            # Fallback: check other possible response formats
            translated_text = response_body.get('completion', '').strip()
        
        # Clean up reasoning/thinking tags if present
        import re
        # Remove <reasoning>...</reasoning> tags
        translated_text = re.sub(r'<reasoning>.*?</reasoning>', '', translated_text, flags=re.DOTALL)
        # Remove <thinking>...</thinking> tags
        translated_text = re.sub(r'<thinking>.*?</thinking>', '', translated_text, flags=re.DOTALL)
        # Remove any other XML-like tags
        translated_text = re.sub(r'<[^>]+>', '', translated_text)
        translated_text = translated_text.strip()
        
        # Clean up the response - remove the prompt if echoed back
        if translated_text.startswith(text):
            translated_text = translated_text[len(text):].strip()
        
        # Remove any trailing markers
        if f"{target_lang}:" in translated_text:
            translated_text = translated_text.split(f"{target_lang}:")[-1].strip()
        
        # Fix reversed text if detected
        translated_text = _fix_reversed_text(translated_text)
            
        return translated_text if translated_text else None

    except ClientError as e:
        print(f"AWS Bedrock error: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        print(f"Translation exception: {str(e)}")
        return None


def _translate_via_hf(text: str, target_lang: str = "fra_Latn") -> str:
    """
    Translate text using HuggingFace Inference API.
    
    Args:
        text: English text to translate
        target_lang: Target language code (e.g., "fra_Latn", "deu_Latn")
    
    Returns:
        Translated text
    """
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": text,
        "parameters": {
            "src_lang": "eng_Latn",
            "tgt_lang": target_lang,
            "task": "translation"
        },
        "options": {
            "use_cache": False
        }
    }
    
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            print(f"HF API error: {response.status_code} - {response.text[:200]}")
            return None
        
        result = response.json()
        
        # Handle different response formats from HF API
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict) and 'translation_text' in result[0]:
                translated = result[0]['translation_text']
                if translated.lower().strip() != text.lower().strip():
                    return translated
                return None
            elif isinstance(result[0], str):
                return result[0]
        if isinstance(result, dict) and 'translation_text' in result:
            translated = result['translation_text']
            if translated.lower().strip() != text.lower().strip():
                return translated
            return None
        
        return None
    except Exception as e:
        print(f"Translation exception: {str(e)}")
        return None


def _translate_with_fallback(text: str, target_lang: str = "French") -> str:
    """
    Translate using only gpt-oss-model-120b via AWS Bedrock.
    No fallback to other models.
    """
    # Use only AWS Bedrock with gpt-oss-model-120b
    translated = _translate_via_aws_bedrock(text, target_lang)
    if translated:
        return translated
    
    # If translation fails, return original text with language indicator
    print(f"Translation failed for: {text[:50]}...")
    return f"[{target_lang}] {text}"


def _chunk_text(text: str) -> list[str]:
    """Split text into chunks at sentence boundaries within char limit."""
    sentences = text.replace("\n", " \n ").split(". ")
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) + 2 <= MAX_CHUNK_CHARS:
            current += sentence + ". "
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sentence + ". "
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text]


def translate_chunks(text: str, target_lang: str = "French"):
    """Generator yielding (translated_chunk, step, total) for each chunk."""
    chunks = _chunk_text(text)
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        translated = _translate_with_fallback(chunk, target_lang)
        yield translated, i + 1, total


def translate_text(text: str, target_lang: str = "French") -> str:
    """Translate English text to target language using available translation API."""
    return " ".join(chunk for chunk, _, _ in translate_chunks(text, target_lang))


def translate_segments(segments: list[dict], target_lang: str = "French"):
    """
    Translate document segments to target language using available translation API.
    
    Args:
        segments: List of dicts with 'id' and 'text' keys
        target_lang: Target language name (e.g., "French", "German")
    
    Yields:
        dicts with 'id', 'type', 'text', and 'translated_text' keys
    """
    for seg in segments:
        text = seg.get("text", "")
        if not text:
            yield {"id": seg.get("id"), "translated_text": "", "type": seg.get("type", "p")}
            continue
        
        # Translate the text in chunks
        chunks = _chunk_text(text)
        translated_parts = []
        
        for chunk in chunks:
            translated = _translate_with_fallback(chunk, target_lang)
            translated_parts.append(translated)
        
        yield {
            "id": seg.get("id"),
            "type": seg.get("type", "p"),
            "text": text,
            "translated_text": " ".join(translated_parts)
        }
