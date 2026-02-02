"""
Test script to demonstrate all 5 technologies working together.
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_health():
    """Test API and MCP servers health."""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE}/health")
        data = response.json()
        print(f"   ✅ API Status: {data.get('status')}")
        print(f"   ✅ RAG System: {'Ready' if data.get('rag_system_ready') else 'Not Ready'}")
        
        # Check MCP servers
        mcp_servers = data.get('mcp_servers', {})
        print(f"\n   MCP Servers:")
        for name, url in mcp_servers.items():
            print(f"   - {name}: {url}")
        
        return data
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def create_sample_invoice():
    """Create sample invoice as Word document."""
    content = """INVOICE

Vendor: Acme Corporation
Address: 123 Business Street, Tech City, CA 94000
Phone: (555) 123-4567

Invoice Number: INV-2024-001
Invoice Date: 2024-01-15
Due Date: 2024-02-15

BILL TO:
Customer Name: Tech Solutions Inc
Address: 456 Client Avenue

DESCRIPTION                          QTY    UNIT PRICE    AMOUNT
Widget A - Premium Model             10     50.00         500.00
Widget B - Standard Edition          5      100.00        500.00
Service Package - Annual             1      200.00        200.00

                                     SUBTOTAL:            1200.00
                                     TAX (8%):            96.00
                                     TOTAL:               1296.00

Payment Terms: Net 30 days
Thank you for your business!"""
    
    try:
        from docx import Document
        
        # Create Word document
        doc = Document()
        for line in content.strip().split('\n'):
            doc.add_paragraph(line)
        
        filename = "sample_invoice.docx"
        doc.save(filename)
        print(f"📝 Created sample invoice file: {filename}")
        return filename
    except ImportError:
        print("   ❌ Error: python-docx not installed")
        print("   Please install: pip install python-docx")
        print("   Or manually create a Word document and update the path below")
        return None

def test_upload(file_path):
    """Test document upload."""
    print(f"\n📤 Uploading document: {file_path}")
    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f, "application/pdf")}
            response = requests.post(f"{API_BASE}/documents/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Upload successful!")
            print(f"   Document ID: {data.get('document_id')}")
            return data
        else:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_process(doc_id):
    """Test document processing through LangGraph + MCP."""
    print(f"\n⚙️  Processing document: {doc_id}")
    print("   (This may take 10-30 seconds...)")
    try:
        response = requests.post(f"{API_BASE}/documents/process/{doc_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Processing complete!")
            print(f"   Status: {data.get('status')}")
            
            # Show structured data if available
            structured_data = data.get('structured_data')
            if structured_data:
                print(f"   Vendor: {structured_data.get('vendor', 'N/A')}")
                print(f"   Total: {structured_data.get('total', 'N/A')}")
            
            # Show validation
            validation = data.get('validation_result', {})
            print(f"   Validation: {validation.get('overall_status', 'N/A')}")
            
            # Show current stage
            print(f"   Stage: {data.get('current_stage', 'N/A')}")
            
            return data
        else:
            print(f"   ❌ Processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_query(query_text, metadata_filter=None):
    """Test RAG query with LangChain."""
    print(f"\n🔍 Querying: '{query_text}'")
    try:
        payload = {"query": query_text}
        if metadata_filter:
            payload["metadata_filter"] = metadata_filter
        
        response = requests.post(
            f"{API_BASE}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Query successful!")
            print(f"   Answer: {data.get('answer')}")
            print(f"   Confidence: {data.get('confidence', 0):.2%}")
            return data
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("🧾 Invoice Intelligence System - Test Script")
    print("=" * 60)
    print()
    
    # Test health
    health = test_health()
    if not health:
        print("\n❌ API is not running. Please start it first:")
        print("   python api.py")
        return
    
    print()
    
    # Create sample
    sample_file = create_sample_invoice()
    if not sample_file:
        print("\n❌ Could not create sample file. Exiting.")
        return
    
    # Upload
    upload_result = test_upload(sample_file)
    if not upload_result or "document_id" not in upload_result:
        print("\n❌ Upload failed. Cannot continue.")
        return
    
    doc_id = upload_result["document_id"]
    
    # Process (LangGraph + MCP)
    process_result = test_process(doc_id)
    if not process_result:
        print("\n❌ Processing failed.")
        return
    
    # Wait for indexing
    print("\n⏳ Waiting for RAG indexing...")
    time.sleep(3)
    
    # Query (RAG with LangChain)
    queries = [
        "What is the total amount?",
        "Who is the vendor?",
        "What items were purchased?"
    ]
    
    for query in queries:
        test_query(query)
        time.sleep(1)
    
    # Cleanup
    import os
    os.remove(sample_file)
    
    print()
    print("=" * 60)
    print("✅ Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("   Please start the server first:")
        print("   python api.py")
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted")
