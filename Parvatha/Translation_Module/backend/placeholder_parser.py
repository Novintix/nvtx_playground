import re
from typing import Dict, Tuple, List
from lxml import etree
import copy

# Namespaces commonly used in WordprocessingML
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

def _has_text(element) -> bool:
    """Check if an element or its children contains any text."""
    texts = element.xpath('.//w:t/text()')
    result = ''.join(texts).strip()
    return bool(result)

def extract_and_replace_elements(doc) -> Tuple[List[str], Dict[str, etree._Element]]:
    """
    Takes a docx.Document object.
    Finds tables and paragraphs composed purely of images/shapes.
    Extracts those heavy XML blobs into an Asset Store.
    Replaces them with plain text placeholders [TBL_X] and [IMG_Y].
    Returns: 
        (list of strings representing the document flow, Dictionary mapping placeholders -> raw XML Element)
    """
    body_element = doc._body._body
    asset_store = {}
    doc_flow = []
    
    tbl_counter = 1
    img_counter = 1
    
    # Iterate through all direct children of the document body
    for child in body_element:
        # If it's a table
        if child.tag == f"{{{NAMESPACES['w']}}}tbl":
            # Deep copy the element so we save exactly how it looked
            stored_element = copy.deepcopy(child)
            placeholder = f"[TBL_{tbl_counter}]"
            asset_store[placeholder] = stored_element
            doc_flow.append(placeholder)
            tbl_counter += 1
            
        # If it's a paragraph
        elif child.tag == f"{{{NAMESPACES['w']}}}p":
            # Does this paragraph contain drawings/objects?
            drawings = child.xpath('.//w:drawing')
            pictures = child.xpath('.//w:pict')
            
            # If it's purely an image block without translatable text
            if (drawings or pictures) and not _has_text(child):
                stored_element = copy.deepcopy(child)
                placeholder = f"[IMG_{img_counter}]"
                asset_store[placeholder] = stored_element
                doc_flow.append(placeholder)
                img_counter += 1
            else:
                # It's a text paragraph (might contain inline images, but mostly text)
                # Extract the text
                texts = child.xpath('.//w:t/text()')
                full_text = ''.join(texts)
                if full_text.strip():
                    doc_flow.append(full_text)
                    
    return doc_flow, asset_store

def recompose_elements(doc, translated_flow: List[str], asset_store: Dict[str, etree._Element]):
    """
    Modifies the document in-place.
    Replaces text nodes with translated flow, preserving w:pPr and w:rPr.
    """
    body_element = doc._body._body
    flow_idx = 0
    
    for child in body_element:
        if flow_idx >= len(translated_flow):
            break
            
        if child.tag == f"{{{NAMESPACES['w']}}}tbl":
            # Flow expects a placeholder here
            if translated_flow[flow_idx].startswith("[TBL_"):
                # We leave the native table intact! The placeholder just skips it.
                flow_idx += 1
                
        elif child.tag == f"{{{NAMESPACES['w']}}}p":
            drawings = child.xpath('.//w:drawing')
            pictures = child.xpath('.//w:pict')
            
            if (drawings or pictures) and not _has_text(child):
                if translated_flow[flow_idx].startswith("[IMG_"):
                    # Leave native image block intact
                    flow_idx += 1
            else:
                texts = child.xpath('.//w:t/text()')
                full_text = ''.join(texts)
                if full_text.strip():
                    # This paragraph had translatable text.
                    translated_text = translated_flow[flow_idx]
                    
                    # Replace the text inside the w:t nodes.
                    # Preserve the run formatting of the very first w:t node that actually had text.
                    t_nodes = child.xpath('.//w:t')
                    first_t = None
                    for t in t_nodes:
                        # Only check if it has text. It might be empty.
                        if t.text and t.text.strip():
                            if first_t is None:
                                first_t = t
                                t.text = translated_text
                                if translated_text.startswith(' ') or translated_text.endswith(' '):
                                    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
                            else:
                                t.text = "" # wipe out the rest
                                
                    # If we somehow didn't find a first_t with a strip(), fallback to the very first t node 
                    if first_t is None and len(t_nodes) > 0:
                        t_nodes[0].text = translated_text
                        
                    flow_idx += 1
