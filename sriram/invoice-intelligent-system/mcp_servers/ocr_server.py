"""
MCP Server: OCR Agent
Azure Computer Vision OCR processing using FastMCP.
"""

from fastmcp import FastMCP
import json
import time

mcp = FastMCP("OCR Agent")

@mcp.tool()
def perform_ocr(file_path: str) -> str:
    """
    Perform OCR on image/scanned PDF using Azure Computer Vision.
    Returns JSON with extracted text and confidence.
    """
    try:
        # Import only when tool is called
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        AZURE_CV_ENDPOINT = os.getenv("AZURE_CV_ENDPOINT")
        AZURE_CV_KEY = os.getenv("AZURE_CV_KEY")
        
        if not AZURE_CV_KEY or not AZURE_CV_ENDPOINT:
            return json.dumps({
                "success": False,
                "text": "",
                "confidence": 0.0,
                "message": "Azure credentials not configured"
            })
        
        from azure.cognitiveservices.vision.computervision import ComputerVisionClient
        from msrest.authentication import CognitiveServicesCredentials
        
        credentials = CognitiveServicesCredentials(AZURE_CV_KEY)
        client = ComputerVisionClient(AZURE_CV_ENDPOINT, credentials)
        
        with open(file_path, "rb") as image_stream:
            ocr_result = client.read_in_stream(image_stream, raw=True)
        
        operation_location = ocr_result.headers["Operation-Location"]
        operation_id = operation_location.split("/")[-1]
        
        # Wait for result
        while True:
            result = client.get_read_result(operation_id)
            if result.status.lower() not in ['notstarted', 'running']:
                break
            time.sleep(1)
        
        extracted_text = []
        confidence_scores = []
        
        if result.status.lower() == 'succeeded':
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    extracted_text.append(line.text)
                    if hasattr(line, 'confidence'):
                        confidence_scores.append(line.confidence)
        
        text_content = "\n".join(extracted_text)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return json.dumps({
            "success": True,
            "text": text_content,
            "confidence": avg_confidence,
            "char_count": len(text_content)
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "text": "",
            "confidence": 0.0,
            "error": str(e)
        })


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    MCP_OCR_PORT = int(os.getenv("MCP_OCR_PORT", 8002))
    
    mcp.run(transport="http", host="127.0.0.1", port=MCP_OCR_PORT)
