import pdfplumber
from langdetect import detect, LangDetectException
import pysbd
import os 
from tqdm import tqdm

def extract_text_pages(pdf_path):
    """
    Extract text from each page of the PDF.
    Returns a list of strings, each corresponding to one page.
    """
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            tables = page.extract_tables()  #also handle tables if needed        
            for table in tables:
                for row in table:
                    row_text = ' '.join(cell for cell in row if cell)
                    page_text += "\n" + row_text
            pages_text.append(page_text)
    return pages_text

def split_into_paragraphs(text):
    """
    Split text into paragraphs based on blank lines or newlines.
    Modify this logic as needed depending on the structure of your PDF text.
    """
    # A simple approach: split by double newlines first
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return paragraphs

def segment_sentences(text, lang_code='en'):
    """
    Segment text into sentences using pysbd.
    If lang_code not supported by pysbd, default to 'en'.
    """
    # Supported languages by pysbd  
    supported_languages = {'en', 'fr', 'de', 'es', 'it', 'ja', 'zh', 'ar', 'hi', 'mr', 'ru', 'ta', 'te', 'tr'}
    if lang_code not in supported_languages:
        lang_code = 'en'
    seg = pysbd.Segmenter(language=lang_code, clean=True)
    sentences = seg.segment(text)
    # Strip whitespace from each sentence
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def detect_language(text):
    """
    Detect language of the given text using langdetect.
    If detection fails, default to English.
    """
    try:
        return detect(text)
    except LangDetectException:
        return 'en'    

def process_pdf(pdf_path):
    """
    Process a single PDF file and return extracted sentences.
    Args:
        pdf_path (str): Path to the PDF file.
    Returns:
        list: Extracted sentences.
    """
    all_sentences = []
    pages_text = extract_text_pages(pdf_path)
    if not any(pages_text):
        return []

    for page_text in pages_text:
        if not page_text.strip():
            continue
        paragraphs = split_into_paragraphs(page_text)
        for paragraph in paragraphs:
            para_lang = detect_language(paragraph)
            para_sentences = segment_sentences(paragraph, lang_code=para_lang)
            all_sentences.extend(para_sentences)

    return all_sentences

def read_pdf_batch(batch, output_dir):
    """
    Process a batch of PDFs and save results to the output directory.
    Args:
        batch (list): A batch of PDF file paths.
        output_dir (str): Path to the output directory.
    """
    loop = tqdm(batch, desc="Processing PDFs")
    for pdf_path in loop:
        sentences = process_pdf(pdf_path)
        output_file = os.path.join(output_dir, os.path.basename(pdf_path) + ".txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sentences))
        loop.set_postfix({"Processed": os.path.basename(pdf_path)})

if __name__ == "__main__":
    pdf_path = "/Users/archismanchakraborti/Desktop/Languagetranslator/src/language_grouper/test.pdf"  # Replace with your PDF file path

    all_sentences = []
    pages_text = extract_text_pages(pdf_path)
    if not any(pages_text):
        print("No text found in PDF. Ensure PDF has selectable text or try another method.")
        exit(1)
    
    # Process each page separately
    for page_idx, page_text in enumerate(pages_text, start=1):
        if not page_text.strip():
            continue
        # Split page into paragraphs (or lines)
        paragraphs = split_into_paragraphs(page_text)
        
        for paragraph in paragraphs:
            # Detect language of the paragraph
            para_lang = detect_language(paragraph)
            # Segment sentences according to detected language
            para_sentences = segment_sentences(paragraph, lang_code=para_lang)
            all_sentences.extend(para_sentences)
    
    # join sentences from all pages as a paragraph
    all_sentences = ' '.join(all_sentences)
    print(all_sentences)