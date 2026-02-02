"""
MCP Server: Validation Agent
Neuro-symbolic rule-based validation using FastMCP.
"""

from fastmcp import FastMCP
import json
from datetime import datetime

mcp = FastMCP("Validation Agent")

@mcp.tool()
def validate_invoice(invoice_data_json: str) -> str:
    """
    Apply neuro-symbolic validation rules to structured invoice data.
    Returns JSON with validation status and rule results.
    """
    try:
        invoice_data = json.loads(invoice_data_json)
        
        validation_results = []
        
        # Rule 1: Total Calculation
        subtotal = invoice_data.get("subtotal")
        tax = invoice_data.get("tax")
        total = invoice_data.get("total")
        
        if subtotal is not None and tax is not None and total is not None:
            calculated_total = subtotal + tax
            tolerance = 0.02
            
            if abs(calculated_total - total) <= tolerance:
                validation_results.append({
                    "rule": "total_calculation",
                    "status": "PASS",
                    "message": f"Total calculation correct: {subtotal} + {tax} = {total}"
                })
            else:
                validation_results.append({
                    "rule": "total_calculation",
                    "status": "FAIL",
                    "message": f"Total mismatch: {subtotal} + {tax} = {calculated_total}, expected {total}"
                })
        else:
            validation_results.append({
                "rule": "total_calculation",
                "status": "NEEDS_REVIEW",
                "message": "Missing financial values"
            })
        
        # Rule 2: Positive Amounts
        if total is not None:
            if total > 0:
                validation_results.append({
                    "rule": "positive_amounts",
                    "status": "PASS",
                    "message": f"Total is positive: {total}"
                })
            else:
                validation_results.append({
                    "rule": "positive_amounts",
                    "status": "FAIL",
                    "message": f"Total must be positive, got: {total}"
                })
        else:
            validation_results.append({
                "rule": "positive_amounts",
                "status": "NEEDS_REVIEW",
                "message": "Total amount missing"
            })
        
        # Rule 3: Required Fields
        vendor = invoice_data.get("vendor")
        invoice_date = invoice_data.get("invoice_date")
        
        missing = []
        if not vendor:
            missing.append("vendor")
        if not invoice_date:
            missing.append("invoice_date")
        
        if not missing:
            validation_results.append({
                "rule": "required_fields",
                "status": "PASS",
                "message": "All required fields present"
            })
        else:
            validation_results.append({
                "rule": "required_fields",
                "status": "FAIL",
                "message": f"Missing required fields: {', '.join(missing)}"
            })
        
        # Rule 4: Date Validity
        if invoice_date:
            try:
                date_obj = datetime.strptime(invoice_date, "%Y-%m-%d")
                
                if date_obj > datetime.now():
                    validation_results.append({
                        "rule": "date_validity",
                        "status": "FAIL",
                        "message": f"Invoice date is in future: {invoice_date}"
                    })
                else:
                    validation_results.append({
                        "rule": "date_validity",
                        "status": "PASS",
                        "message": f"Valid invoice date: {invoice_date}"
                    })
            except ValueError:
                validation_results.append({
                    "rule": "date_validity",
                    "status": "FAIL",
                    "message": f"Invalid date format: {invoice_date}"
                })
        else:
            validation_results.append({
                "rule": "date_validity",
                "status": "NEEDS_REVIEW",
                "message": "Invoice date missing"
            })
        
        # Rule 5: Line Items Consistency
        line_items = invoice_data.get("line_items", [])
        
        if line_items and subtotal is not None:
            line_items_sum = sum(item.get("amount", 0) for item in line_items)
            tolerance = 0.02 * len(line_items)
            
            if abs(line_items_sum - subtotal) <= tolerance:
                validation_results.append({
                    "rule": "line_items_consistency",
                    "status": "PASS",
                    "message": f"Line items sum matches subtotal: {line_items_sum} ≈ {subtotal}"
                })
            else:
                validation_results.append({
                    "rule": "line_items_consistency",
                    "status": "FAIL",
                    "message": f"Line items sum mismatch: {line_items_sum} vs subtotal {subtotal}"
                })
        else:
            validation_results.append({
                "rule": "line_items_consistency",
                "status": "NEEDS_REVIEW",
                "message": "No line items or subtotal missing"
            })
        
        # Determine overall status
        statuses = [r['status'] for r in validation_results]
        if all(s == 'PASS' for s in statuses):
            overall_status = 'PASS'
        elif any(s == 'FAIL' for s in statuses):
            overall_status = 'FAIL'
        else:
            overall_status = 'NEEDS_REVIEW'
        
        return json.dumps({
            "overall_status": overall_status,
            "validation_results": validation_results,
            "rules_passed": sum(1 for r in validation_results if r['status'] == 'PASS'),
            "rules_failed": sum(1 for r in validation_results if r['status'] == 'FAIL'),
            "rules_review": sum(1 for r in validation_results if r['status'] == 'NEEDS_REVIEW')
        })
        
    except Exception as e:
        return json.dumps({
            "overall_status": "ERROR",
            "validation_results": [],
            "error": str(e)
        })


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    MCP_VALIDATION_PORT = int(os.getenv("MCP_VALIDATION_PORT", 8004))
    
    mcp.run(transport="http", host="127.0.0.1", port=MCP_VALIDATION_PORT)
