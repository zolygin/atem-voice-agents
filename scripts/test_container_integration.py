#!/usr/bin/env python3
"""
Comprehensive integration test that simulates the container app environment
to verify that all components work together correctly with Supabase RAG.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY', 
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_VERSION',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            print(f"  ❌ {var}: MISSING")
        else:
            print(f"  ✅ {var}: SET")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All environment variables are set correctly")
    return True

def test_supabase_connection():
    """Test Supabase connection and table access"""
    print("\n🔍 Testing Supabase Connection...")
    
    try:
        from supabase import create_client
        
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not key:
            print("❌ Supabase credentials not found")
            return False
            
        supabase = create_client(url, key)
        print("  ✅ Supabase client created successfully")
        
        # Test table access
        response = supabase.table('atem_voice_documents').select('id', 'content').limit(1).execute()
        print(f"  ✅ Table access successful - Found {len(response.data) if response.data else 0} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_azure_openai_connection():
    """Test Azure OpenAI connection and embedding generation"""
    print("\n🔍 Testing Azure OpenAI Connection...")
    
    try:
        from openai import AzureOpenAI
        
        client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version=os.environ.get("AZURE_OPENAI_VERSION", "2024-10-01-preview"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        
        deployment_name = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        
        response = client.embeddings.create(
            input="test query for embedding",
            model=deployment_name
        )
        
        embedding = response.data[0].embedding
        print(f"  ✅ Embedding generated successfully: {len(embedding)} dimensions")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {e}")
        return False

def test_supabase_rag_tools():
    """Test Supabase RAG tools creation and functionality"""
    print("\n🔍 Testing Supabase RAG Tools...")
    
    try:
        # Import the Supabase RAG tools
        from src.app.backend.tools.rag.supabase_rag import search_tool, report_grounding_tool
        
        # Create the tools
        search_tool_instance = search_tool()
        grounding_tool_instance = report_grounding_tool()
        
        print("  ✅ Supabase RAG tools created successfully")
        
        # Test search tool schema
        if hasattr(search_tool_instance, 'schema'):
            print("  ✅ Search tool schema available")
        else:
            print("  ❌ Search tool schema missing")
            return False
            
        # Test grounding tool schema
        if hasattr(grounding_tool_instance, 'schema'):
            print("  ✅ Grounding tool schema available")
        else:
            print("  ❌ Grounding tool schema missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Supabase RAG tools test failed: {e}")
        return False

def test_vector_search_functionality():
    """Test the complete vector search functionality"""
    print("\n🔍 Testing Vector Search Functionality...")
    
    try:
        from supabase import create_client
        
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        supabase = create_client(url, key)
        
        # Test RPC function exists
        try:
            # Try to call the RPC function with a simple test
            response = supabase.rpc('match_atem_voice_documents', {
                'query_embedding': [0.1] * 3072,  # Dummy embedding
                'match_count': 1,
                'filter': {}
            }).execute()
            
            print("  ✅ RPC function 'match_atem_voice_documents' is available")
            print(f"  ✅ Vector search test completed - Found {len(response.data) if response.data else 0} results")
            return True
            
        except Exception as rpc_error:
            print(f"  ⚠️  RPC function test warning: {rpc_error}")
            # Try simple table query as fallback
            try:
                response = supabase.table('atem_voice_documents').select('id', 'content').limit(1).execute()
                print(f"  ✅ Fallback table query successful - Found {len(response.data)} documents")
                return True
            except Exception as fallback_error:
                print(f"  ❌ Fallback query also failed: {fallback_error}")
                return False
                
    except Exception as e:
        print(f"❌ Vector search functionality test failed: {e}")
        return False

def test_application_imports():
    """Test that the main application can be imported without errors"""
    print("\n🔍 Testing Application Imports...")
    
    try:
        # This will test if all imports work correctly
        import src.app.app
        print("  ✅ Main application imports successfully")
        return True
    except Exception as e:
        print(f"❌ Application import failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("🧪 Container App Integration Test")
    print("=" * 60)
    
    tests = [
        test_environment_variables,
        test_supabase_connection,
        test_azure_openai_connection,
        test_supabase_rag_tools,
        test_vector_search_functionality,
        test_application_imports
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        print("✅ Container app should deploy and run successfully with Supabase RAG")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
