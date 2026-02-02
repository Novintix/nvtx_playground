"""
LangGraph Orchestrator: State-based agent workflow.
Uses MCP servers as tools with conditional transitions.
"""

import asyncio
import json
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from fastmcp import Client
from logger import setup_logger
from config import MCP_PORT

logger = setup_logger("ORCHESTRATOR")


class InvoiceState(TypedDict):
    """State for invoice processing workflow."""
    document_id: str
    file_path: str
    file_type: str
    raw_data: dict
    needs_ocr: bool
    structured_data: dict
    validation_result: dict
    current_stage: str
    error: str


async def ingestion_node(state: InvoiceState) -> InvoiceState:
    """
    Ingestion Agent: Process uploaded file using MCP server.
    """
    logger.info(f"doc={state['document_id']} action=ingestion_start file_type={state['file_type']}")
    
    try:
        async with Client(f"http://127.0.0.1:{MCP_PORT}/mcp") as client:
            # Select appropriate tool based on file type
            tool_map = {
                "pdf": "process_pdf",
                "image": "process_image",
                "excel": "process_excel",
                "word": "process_word"
            }
            
            tool_name = tool_map.get(state["file_type"])
            if not tool_name:
                raise ValueError(f"Unsupported file type: {state['file_type']}")
            
            result = await client.call_tool(tool_name, {"file_path": state["file_path"]})
            raw_data = json.loads(result.data)
            
            # Check if OCR is needed
            needs_ocr = any(page.get("needs_ocr", False) for page in raw_data.get("pages", []))
            
            logger.info(f"doc={state['document_id']} action=ingestion_complete needs_ocr={needs_ocr}")
            
            return {
                **state,
                "raw_data": raw_data,
                "needs_ocr": needs_ocr,
                "current_stage": "ingestion_complete"
            }
            
    except Exception as e:
        logger.error(f"doc={state['document_id']} action=ingestion_failed error={str(e)}")
        return {**state, "error": str(e), "current_stage": "failed"}


async def ocr_node(state: InvoiceState) -> InvoiceState:
    """
    OCR Agent: Perform OCR using Azure CV via MCP server.
    """
    logger.info(f"doc={state['document_id']} action=ocr_start")
    
    try:
        async with Client(f"http://127.0.0.1:{MCP_PORT}/mcp") as client:
            result = await client.call_tool("perform_ocr", {"file_path": state["file_path"]})
            ocr_result = json.loads(result.data)
            
            if ocr_result.get("success"):
                # Update raw_data with OCR text
                for page in state["raw_data"].get("pages", []):
                    if page.get("needs_ocr"):
                        page["text"] = ocr_result.get("text", "")
                        page["needs_ocr"] = False
                
                logger.info(f"doc={state['document_id']} action=ocr_complete confidence={ocr_result.get('confidence', 0):.2f}")
            else:
                logger.warning(f"doc={state['document_id']} action=ocr_skipped reason={ocr_result.get('message', 'unknown')}")
            
            return {**state, "current_stage": "ocr_complete"}
            
    except Exception as e:
        logger.error(f"doc={state['document_id']} action=ocr_failed error={str(e)}")
        # Continue without OCR
        return {**state, "current_stage": "ocr_complete"}


async def structuring_node(state: InvoiceState) -> InvoiceState:
    """
    Structuring Agent: Extract structured data using Gemini via MCP server.
    """
    logger.info(f"doc={state['document_id']} action=structuring_start")
    
    try:
        # Combine all page text
        combined_text = "\n\n".join([
            f"[Page {page['page_number']}]\n{page['text']}"
            for page in state["raw_data"].get("pages", [])
        ])
        
        async with Client(f"http://127.0.0.1:{MCP_PORT}/mcp") as client:
            result = await client.call_tool("structure_invoice", {"content": combined_text})
            structuring_result = json.loads(result.data)
            
            if structuring_result.get("success"):
                structured_data = structuring_result.get("data", {})
                logger.info(f"doc={state['document_id']} action=structuring_complete vendor={structured_data.get('vendor', 'N/A')}")
                
                return {
                    **state,
                    "structured_data": structured_data,
                    "current_stage": "structuring_complete"
                }
            else:
                raise ValueError(structuring_result.get("error", "Structuring failed"))
            
    except Exception as e:
        logger.error(f"doc={state['document_id']} action=structuring_failed error={str(e)}")
        return {**state, "error": str(e), "current_stage": "failed"}


async def validation_node(state: InvoiceState) -> InvoiceState:
    """
    Validation Agent: Apply neuro-symbolic rules via MCP server.
    """
    logger.info(f"doc={state['document_id']} action=validation_start")
    
    try:
        async with Client(f"http://127.0.0.1:{MCP_PORT}/mcp") as client:
            invoice_json = json.dumps(state["structured_data"])
            result = await client.call_tool("validate_invoice", {"invoice_data_json": invoice_json})
            validation_result = json.loads(result.data)
            
            overall_status = validation_result.get("overall_status", "UNKNOWN")
            logger.info(f"doc={state['document_id']} action=validation_complete status={overall_status}")
            
            return {
                **state,
                "validation_result": validation_result,
                "current_stage": "validation_complete"
            }
            
    except Exception as e:
        logger.error(f"doc={state['document_id']} action=validation_failed error={str(e)}")
        return {**state, "error": str(e), "current_stage": "failed"}


def should_perform_ocr(state: InvoiceState) -> Literal["ocr", "structuring"]:
    """
    Conditional edge: Decide if OCR is needed.
    """
    if state.get("needs_ocr", False):
        logger.info(f"doc={state['document_id']} action=routing decision=ocr_needed")
        return "ocr"
    else:
        logger.info(f"doc={state['document_id']} action=routing decision=skip_ocr")
        return "structuring"


# Build LangGraph workflow
workflow = StateGraph(InvoiceState)

# Add nodes
workflow.add_node("ingestion", ingestion_node)
workflow.add_node("ocr", ocr_node)
workflow.add_node("structuring", structuring_node)
workflow.add_node("validation", validation_node)

# Set entry point
workflow.set_entry_point("ingestion")

# Add conditional edge after ingestion
workflow.add_conditional_edges(
    "ingestion",
    should_perform_ocr,
    {
        "ocr": "ocr",
        "structuring": "structuring"
    }
)

# Add edges
workflow.add_edge("ocr", "structuring")
workflow.add_edge("structuring", "validation")
workflow.add_edge("validation", END)

# Compile graph
app = workflow.compile()


async def process_document(document_id: str, file_path: str, file_type: str) -> dict:
    """
    Process document through LangGraph workflow.
    
    Args:
        document_id: Unique document identifier
        file_path: Path to uploaded file
        file_type: Type of file (pdf, image, excel, word)
        
    Returns:
        Final state with structured data and validation
    """
    logger.info(f"doc={document_id} action=workflow_start file_type={file_type}")
    
    initial_state = {
        "document_id": document_id,
        "file_path": file_path,
        "file_type": file_type,
        "raw_data": {},
        "needs_ocr": False,
        "structured_data": {},
        "validation_result": {},
        "current_stage": "initialized",
        "error": ""
    }
    
    try:
        final_state = await app.ainvoke(initial_state)
        logger.info(f"doc={document_id} action=workflow_complete stage={final_state.get('current_stage')}")
        return final_state
        
    except Exception as e:
        logger.error(f"doc={document_id} action=workflow_failed error={str(e)}")
        return {**initial_state, "error": str(e), "current_stage": "failed"}
