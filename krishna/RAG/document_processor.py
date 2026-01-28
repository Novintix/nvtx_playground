import io
import os
from typing import List, Dict, Any, Tuple
import uuid
from io import BytesIO

# PDF processing
from pypdf import PdfReader

# DOCX processing
import docx

# Image processing
from PIL import Image
import pytesseract

# Text chunking
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file."""
    pdf_file = BytesIO(file_content)
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from a DOCX file."""
    docx_file = BytesIO(file_content)
    doc = docx.Document(docx_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_text_from_image(file_content: bytes) -> str:
    """Extract text from an image using OCR."""
    image = Image.open(BytesIO(file_content))
    text = pytesseract.image_to_string(image)
    return text

def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from a TXT file."""
    return file_content.decode('utf-8', errors='replace')

def split_text_into_chunks(text: str, filename: str) -> List[Dict[str, Any]]:
    """Split text into chunks using LangChain's text splitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )
    
    chunks = text_splitter.split_text(text)
    
    # Create document chunks with metadata
    document_chunks = []
    for i, chunk in enumerate(chunks):
        doc_id = str(uuid.uuid4())
        document_chunks.append({
            "id": doc_id,
            "text": chunk,
            "metadata": {
                "source": filename,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        })
    
    return document_chunks

def process_document(file_content: bytes, filename: str, content_type: str) -> List[Dict[str, Any]]:
    """
    Process a document based on its content type and return text chunks.
    
    Args:
        file_content: The binary content of the file
        filename: The name of the file
        content_type: The MIME type of the file
    
    Returns:
        A list of document chunks with text and metadata
    """
    text = ""
    print(f"Processing document: {filename}, type: {content_type}")
    
    try:
        # Extract text based on file type
        if content_type == "application/pdf":
            text = extract_text_from_pdf(file_content)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = extract_text_from_docx(file_content)
        elif content_type in ["image/png", "image/jpeg", "image/jpg"]:
            text = extract_text_from_image(file_content)
        elif content_type == "text/plain":
            text = extract_text_from_txt(file_content)
        else:
            # Try to determine type from filename extension if content_type is not helpful
            ext = os.path.splitext(filename)[1].lower()
            print(f"Content type not recognized, trying extension: {ext}")
            if ext == ".pdf":
                text = extract_text_from_pdf(file_content)
            elif ext == ".docx":
                text = extract_text_from_docx(file_content)
            elif ext in [".png", ".jpg", ".jpeg"]:
                text = extract_text_from_image(file_content)
            elif ext == ".txt":
                text = extract_text_from_txt(file_content)
            else:
                # Default to treating as plain text
                print(f"Unknown file type, trying as plain text")
                text = extract_text_from_txt(file_content)
    
        print(f"Extracted text length: {len(text)} characters")
        if len(text.strip()) == 0:
            print("WARNING: No text extracted from document")
            return []
        
        # Split text into chunks
        document_chunks = split_text_into_chunks(text, filename)
        print(f"Created {len(document_chunks)} chunks")
        
        return document_chunks
    
    except Exception as e:
        print(f"Error processing document {filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

