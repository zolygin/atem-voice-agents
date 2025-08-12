#!/usr/bin/env python3
"""
Quick test script to verify Supabase RAG integration is working
"""
import os
import sys
from dotenv import load_dotenv

# Add src to path so we can import the modules
sys.path.insert(0, 'src/app')

load_dotenv()

def test_supabase_rag():
    """Test the Supabase RAG implementation"""
    print("🔍 Testing Supabase RAG Integration...")
    
    try:
        # Test 1: Import the Supabase RAG module
        print("1. Importing Supabase RAG module...")
        from backend.tools.rag.supabase_rag import search_tool, report_grounding_tool
        print("   ✅ Import successful")
        
        # Test 2: Create the tools
        print("2. Creating RAG tools...")
        search_tool_instance = search_tool()
        grounding_tool_instance = report_grounding_tool()
        print("   ✅ Tools created successfully")
        
        # Test 3: Check if required environment variables are present
        print("3. Checking environment variables...")
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"   ⚠️  Missing environment variables: {missing_vars}")
            return False
        else:
            print("   ✅ All required environment variables present")
        
        # Test 4: Quick connectivity test
        print("4. Testing basic connectivity...")
        from supabase import create_client
        supabase = create_client(
            os.environ.get('SUPABASE_URL'), 
            os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Test simple query
        response = supabase.table('atem_voice_documents').select('id').limit(1).execute()
        print(f"   ✅ Supabase connection successful - Found {len(response.data)} documents")
        
        print("\n🎉 All tests passed! Supabase RAG integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_rag()
    sys.exit(0 if success else 1)
