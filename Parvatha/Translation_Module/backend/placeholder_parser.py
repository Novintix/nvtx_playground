import re
from typing import Dict, Tuple, List
from lxml import etree
import copy

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
}

def _get_all_parts(doc) -> List:
    """Get all XML parts that might contain translatable text"""
    parts = [doc._body._body]
    for rel in doc.part.rels.values():
        if 'header' in rel.reltype or 'footer' in rel.reltype:
            parts.append(rel.target_part._element)
    return parts

def extract_translatable_elements(doc) -> List[str]:
    """
    Extracts purely translatable text chunks, splitting at non-text elements
    and also splitting whenever the run formatting (rPr) changes to preserve exact layout.
    """
    doc_flow = []
    
    for part in _get_all_parts(doc):
        for p in part.xpath('.//w:p'):
            descendants = p.xpath('.//w:t | .//w:br | .//w:drawing | .//w:pict | .//w:sym | .//w:tab')
            
            current_text = ""
            last_rpr_str = None
            
            for node in descendants:
                if node.tag.endswith('}t'): # It's a text node
                    parent_r = node.getparent()
                    rpr = parent_r.find('./w:rPr', namespaces=NAMESPACES)
                    rpr_str = etree.tostring(rpr) if rpr is not None else b""
                    
                    if last_rpr_str is not None and rpr_str != last_rpr_str:
                        # Formatting changed! Break the flow to preserve exact styles!
                        if current_text.strip():
                            doc_flow.append(current_text)
                        current_text = ""
                        
                    last_rpr_str = rpr_str
                    
                    if node.text:
                        current_text += node.text
                else:
                    # It's a flow-breaking element
                    if current_text.strip():
                        doc_flow.append(current_text)
                    current_text = ""
                    last_rpr_str = None
            
            # Emit remaining text at end of paragraph
            if current_text.strip():
                doc_flow.append(current_text)
                
    return doc_flow

def recompose_elements(doc, translated_flow: List[str]):
    """
    Modifies the document in-place.
    Replaces text chunks exactly where they were initially extracted,
    preserving all non-text elements, and exact inline run formatting.
    """
    flow_idx = 0
    
    for part in _get_all_parts(doc):
        for p in part.xpath('.//w:p'):
            descendants = p.xpath('.//w:t | .//w:br | .//w:drawing | .//w:pict | .//w:sym | .//w:tab')
            
            current_t_nodes = []
            has_text = False
            last_rpr_str = None
            
            for node in descendants:
                if node.tag.endswith('}t'):
                    parent_r = node.getparent()
                    rpr = parent_r.find('./w:rPr', namespaces=NAMESPACES)
                    rpr_str = etree.tostring(rpr) if rpr is not None else b""
                    
                    if last_rpr_str is not None and rpr_str != last_rpr_str:
                        # Formatting changed! Flush chunk
                        if has_text:
                            if flow_idx < len(translated_flow):
                                _replace_text_in_nodes(current_t_nodes, translated_flow[flow_idx])
                                flow_idx += 1
                        current_t_nodes = []
                        has_text = False
                        
                    last_rpr_str = rpr_str
                    
                    current_t_nodes.append(node)
                    if node.text and node.text.strip():
                        has_text = True
                else:
                    # Flush the current chunk
                    if has_text:
                        if flow_idx < len(translated_flow):
                            _replace_text_in_nodes(current_t_nodes, translated_flow[flow_idx])
                            flow_idx += 1
                    current_t_nodes = []
                    has_text = False
                    last_rpr_str = None
                    
            # Flush remaining chunk
            if has_text:
                if flow_idx < len(translated_flow):
                    _replace_text_in_nodes(current_t_nodes, translated_flow[flow_idx])
                    flow_idx += 1

def _replace_text_in_nodes(t_nodes: List, translated_text: str):
    """
    Places the translated text into the first available text node
    and clears the rest within the exact same continuous text chunk.
    """
    first_t = None
    for t in t_nodes:
        if t.text and t.text.strip():
            if first_t is None:
                first_t = t
                t.text = translated_text
                # Maintain spacing if needed
                if translated_text.startswith(' ') or translated_text.endswith(' '):
                    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            else:
                t.text = ""
                
    if first_t is None and t_nodes:
        t_nodes[0].text = translated_text
