import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from languages import LANGUAGES

MAX_CHUNK_CHARS = 1000

MODELS = {
    "600m": "facebook/nllb-200-distilled-600M",
    # "1.3b": "facebook/nllb-200-distilled-1.3B",
    # "3.3b": "facebook/nllb-200-3.3B",
}

# Cache: model_key -> (tokenizer, model)
_cache: dict[str, tuple] = {}


def _get_model(model_key: str = "600m"):
    if model_key not in _cache:
        model_name = MODELS[model_key]
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        if torch.cuda.is_available():
            model = model.cuda()
        model.eval()
        _cache[model_key] = (tokenizer, model)
    return _cache[model_key]


def _normalize(text: str) -> str:
    """Collapse newlines and extra whitespace into single spaces."""
    return " ".join(text.split())


def _chunk_text(text: str) -> list[str]:
    """Split text into semantic chunks and combine short ones gracefully."""
    try:
        from segmenter import chunk_text_intelligently
        chunks = chunk_text_intelligently(text, max_chars=MAX_CHUNK_CHARS)
        return chunks if chunks else [text]
    except ImportError:
        # Fallback if spacy is not ready
        clean = _normalize(text)
        sentences = clean.split(". ")
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
        return chunks or [clean]


def _translate_batch(chunks: list[str], tokenizer, model, forced_bos_token_id: int) -> list[str]:
    """Translates a batch of text chunks simultaneously."""
    if not chunks:
        return []
        
    device = next(model.parameters()).device
    inputs = tokenizer(
        chunks,
        return_tensors="pt",
        padding=True,          # Pad sequences to match the longest in the batch
        truncation=True,
        max_length=512,        # Encoder input cap
    ).to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_new_tokens=1024,
            num_beams=4,
            length_penalty=1.0,
            early_stopping=False,
        )

    return tokenizer.batch_decode(output_ids, skip_special_tokens=True)


def translate_chunks(text: str, model_key: str = "600m", target_lang: str = "fr", batch_size: int = 16):
    """Generator yielding (translated_chunk, step, total) for each chunk using batching."""
    nllb_code = LANGUAGES.get(target_lang, {}).get("nllb", "fra_Latn")
    tokenizer, model = _get_model(model_key)
    forced_bos_token_id = tokenizer.convert_tokens_to_ids(nllb_code)

    chunks = _chunk_text(text)
    total = len(chunks)
    
    # Process in batches
    for i in range(0, total, batch_size):
        batch_chunks = chunks[i:i + batch_size]
        translated_batch = _translate_batch(batch_chunks, tokenizer, model, forced_bos_token_id)
        
        # Yield each individually so external systems can track progress sequentially
        for j, translated in enumerate(translated_batch):
            yield translated, i + j + 1, total


def translate_text(text: str, model_key: str = "600m", target_lang: str = "fr") -> str:
    return " ".join(chunk for chunk, _, _ in translate_chunks(text, model_key, target_lang))
