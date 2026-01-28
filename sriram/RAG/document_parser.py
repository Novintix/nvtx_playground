"""
Document parsing module using PyMuPDF4LLM.
Handles multi-column PDFs and extracts structured content with metadata.
"""

import pymupdf4llm
from pathlib import Path
from typing import Dict, List
from logger import setup_logger

logger = setup_logger(__name__)


class DocumentParser:
    """
    Parses PDF documents and extracts text with metadata.
    Optimized for multi-column layouts and complex document structures.
    """
    
    def __init__(self):
        """Initialize the document parser."""
        logger.info("DocumentParser initialized")
    
    def parse_pdf(self, file_path: str) -> Dict:
        """
        Parse PDF file and extract structured content with metadata.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            Dictionary containing extracted text, metadata, and page information
        
        Raises:
            Exception: If parsing fails
        """
        try:
            logger.info(f"Starting PDF parsing: {file_path}")
            
            # Use PyMuPDF4LLM for better multi-column handling
            md_text = pymupdf4llm.to_markdown(file_path)
            
            # Extract metadata
            import pymupdf
            doc = pymupdf.open(file_path)
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "total_pages": doc.page_count,
                "file_name": Path(file_path).name
            }
            
            # Extract page-level content
            pages_content = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text("text")
                pages_content.append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "char_count": len(page_text)
                })
            
            doc.close()
            
            result = {
                "full_text": md_text,
                "metadata": metadata,
                "pages": pages_content
            }
            
            logger.info(f"Successfully parsed PDF: {metadata['total_pages']} pages, "
                       f"{len(md_text)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse PDF {file_path}: {str(e)}", exc_info=True)
            raise
