"""
Text preprocessing module.
Cleans and normalizes extracted text for better chunking and embedding.
"""

import re
from typing import List, Dict
from logger import setup_logger

logger = setup_logger(__name__)


class TextPreprocessor:
    """
    Preprocesses extracted text by cleaning, normalizing, and structuring.
    """
    
    def __init__(self):
        """Initialize the text preprocessor."""
        logger.info("TextPreprocessor initialized")
    
    def preprocess(self, text: str) -> str:
        """
        Clean and normalize text for better processing.
        
        Args:
            text: Raw text to preprocess
        
        Returns:
            Cleaned and normalized text
        """
        try:
            logger.debug(f"Preprocessing text of length: {len(text)}")
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters but keep punctuation
            text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/]', '', text)
            
            # Normalize line breaks
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # Remove multiple consecutive newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # Strip leading/trailing whitespace
            text = text.strip()
            
            logger.debug(f"Preprocessed text length: {len(text)}")
            return text
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}", exc_info=True)
            raise
    
    def extract_sections(self, text: str) -> List[Dict]:
        """
        Extract logical sections from text based on headers and structure.
        
        Args:
            text: Preprocessed text
        
        Returns:
            List of sections with metadata
        """
        try:
            logger.debug("Extracting sections from text")
            
            # Split by markdown headers or numbered sections
            section_pattern = r'(?:^|\n)(#{1,3}\s+.+?|(?:\d+\.)+\s+.+?)(?=\n)'
            sections = []
            
            matches = list(re.finditer(section_pattern, text))
            
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                section_title = match.group(1).strip()
                section_content = text[start:end].strip()
                
                sections.append({
                    "title": section_title,
                    "content": section_content,
                    "start_pos": start,
                    "end_pos": end
                })
            
            # If no sections found, treat entire text as one section
            if not sections:
                sections.append({
                    "title": "Document Content",
                    "content": text,
                    "start_pos": 0,
                    "end_pos": len(text)
                })
            
            logger.info(f"Extracted {len(sections)} sections")
            return sections
            
        except Exception as e:
            logger.error(f"Section extraction failed: {str(e)}", exc_info=True)
            raise
