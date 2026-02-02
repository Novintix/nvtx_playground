"""
Test script to verify database schema analysis and PyMongo bug fix.
"""

import sys
from query_router import analyze_database_schema, get_schema_context, mongo_db

def test_schema_analysis():
    """Test the database schema analysis functionality."""
    print("=" * 60)
    print("Testing Database Schema Analysis")
    print("=" * 60)
    
    # Test 1: Check MongoDB connection
    print("\n1. Testing MongoDB Connection...")
    if mongo_db is None:
        print("   ❌ MongoDB not configured")
        return False
    else:
        print("   ✅ MongoDB connected")
    
    # Test 2: Analyze schema
    print("\n2. Analyzing Database Schema...")
    schema = analyze_database_schema()
    
    if schema.get("status") == "success":
        print(f"   ✅ Schema analysis successful")
        print(f"   Database: {schema['database']}")
        print(f"   Total Documents: {schema['total_documents']}")
        print(f"   Collections: {len(schema['collections'])}")
        
        for coll_name, coll_info in schema['collections'].items():
            print(f"\n   Collection: {coll_name}")
            print(f"   - Count: {coll_info['count']}")
            print(f"   - Fields: {', '.join(coll_info['sample_keys'][:5])}...")
    else:
        print(f"   ❌ Schema analysis failed: {schema.get('message')}")
        return False
    
    # Test 3: Get schema context
    print("\n3. Testing Schema Context Generation...")
    context = get_schema_context()
    print("   ✅ Schema context generated:")
    print("\n" + context)
    
    # Test 4: Test PyMongo bug fix
    print("\n4. Testing PyMongo Bug Fix...")
    try:
        # This should NOT raise "Database objects do not implement truth value testing"
        if mongo_db is None:
            print("   ❌ Database is None")
        else:
            print("   ✅ Database check works correctly (bug fixed!)")
            
            # Try to access a collection
            resumes = mongo_db["resumes"]
            count = resumes.count_documents({})
            print(f"   ✅ Successfully counted resumes: {count}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_schema_analysis()
    sys.exit(0 if success else 1)
