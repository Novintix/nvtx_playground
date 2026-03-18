import spacy
from typing import List
import re

# Load the small English pipeline
# We expect en_core_web_sm to be installed via `python -m spacy download en_core_web_sm`
nlp = spacy.load("en_core_web_sm")

def chunk_text_intelligently(text: str, max_chars: int = 1000) -> List[str]:
    """
    Splits text into semantic sentences using spaCy.
    Groups specific warning/caution headers with their sibling sentences.
    Ensures chunks don't exceed max_chars.
    """
    if not text.strip():
        return []

    doc = nlp(text)
    
    # Extract raw sentence strings
    raw_sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    # 1. First pass: merge "WARNING:", "CAUTION:", "NOTE:" blocks with the following sentence.
    merged_sentences = []
    i = 0
    while i < len(raw_sentences):
        sent = raw_sentences[i]
        
        # Check if the sentence is just a header or starts with a header that might be disconnected
        upper_stripped = sent.upper().strip()
        is_header = bool(re.match(r'^(WARNING|CAUTION|NOTE)s?:?$', upper_stripped))
        
        if is_header and i + 1 < len(raw_sentences):
            # Combine header with the next sentence
            combined = f"{sent} {raw_sentences[i+1]}"
            merged_sentences.append(combined)
            i += 2  # skip the next sentence since we consumed it
        else:
            merged_sentences.append(sent)
            i += 1

    # 2. Second pass: Group sentences into chunks up to max_chars
    chunks = []
    current_chunk = ""
    
    for sentence in merged_sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

# Run simple test if executed directly
if __name__ == "__main__":
    test_text = "WARNING: Do not ingest. Dr. Smith strongly advises against this. This applies to 1.5mg doses. Continue safely."
    print("Chunks:", chunk_text_intelligently(test_text))
