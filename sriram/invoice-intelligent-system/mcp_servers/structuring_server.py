"""
MCP Server: Structuring Agent
Uses Gemini to extract structured invoice data using FastMCP.
"""

from fastmcp import FastMCP
import json

mcp = FastMCP("Structuring Agent")

@mcp.tool()
def structure_invoice(content: str) -> str:
    """
    Extract structured invoice data from text using Gemini.
    Returns JSON with vendor, invoice_number, date, line_items, totals.
    """
    try:
        # Import only when tool is called
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0
        )
        
        prompt = f"""
You are an invoice data extraction expert. Extract structured information from the following invoice content.

Return ONLY a valid JSON object with this exact structure:
{{
    "vendor": "vendor name or null",
    "invoice_number": "invoice number or null",
    "invoice_date": "YYYY-MM-DD or null",
    "line_items": [
        {{
            "description": "item description",
            "quantity": number,
            "unit_price": number,
            "amount": number
        }}
    ],
    "subtotal": number or null,
    "tax": number or null,
    "total": number or null,
    "currency": "USD/EUR/etc or null"
}}

Invoice Content:
{content}

Return ONLY the JSON object, no other text.
"""
        
        response = llm.invoke(prompt)
        response_text = response.content.strip()
        
        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        structured_data = json.loads(response_text)
        
        return json.dumps({
            "success": True,
            "data": structured_data
        })
        
    except json.JSONDecodeError as e:
        return json.dumps({
            "success": False,
            "data": None,
            "error": f"JSON parsing error: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "data": None,
            "error": str(e)
        })


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    MCP_STRUCTURING_PORT = int(os.getenv("MCP_STRUCTURING_PORT", 8003))
    
    mcp.run(transport="http", host="127.0.0.1", port=MCP_STRUCTURING_PORT)
