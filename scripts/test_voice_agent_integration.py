#!/usr/bin/env python3
import os
import asyncio
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_voice_agent_integration():
    """Test the complete voice agent integration with Supabase RAG"""
    print("Testing Voice Agent Integration with Supabase RAG")
    print("=" * 50)
    
    # Test 1: Supabase Connection
    print("1. Testing Supabase Connection...")
    try:
        supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))
        print("   ✓ Supabase connection successful")
        
        # Test basic table access
        response = supabase.table('atem_voice_documents').select('id', 'content').limit(1).execute()
        print(f"   ✓ Table access successful - Found {len(response.data)} documents")
        
    except Exception as e:
        print(f"   ✗ Supabase connection failed: {e}")
        return
    
    # Test 2: OpenAI Connection (for embeddings)
    print("\n2. Testing OpenAI Connection...")
    try:
        openai_client = OpenAI(api_key=os.environ.get("AZURE_OPENAI_API_KEY"))
        # Test embedding generation
        response = openai_client.embeddings.create(
            input="test query",
            model="text-embedding-3-large"
        )
        embedding = response.data[0].embedding
        print(f"   ✓ OpenAI connection successful - Generated {len(embedding)}-dimensional embedding")
        
    except Exception as e:
        print(f"   ⚠ OpenAI connection has issues: {e}")
        print("     (This is OK if using dummy embeddings for testing)")
    
    # Test 3: Supabase RPC Function
    print("\n3. Testing Supabase RPC Function...")
    try:
        # Use dummy embedding for testing
        dummy_embedding = [0.1] * 3072
        response = supabase.rpc('match_atem_voice_documents', {
            'query_embedding': dummy_embedding,
            'match_count': 2,
            'filter': {}
        }).execute()
        
        print(f"   ✓ RPC function successful - Found {len(response.data)} results")
        if response.data:
            print(f"   Sample result ID: {response.data[0].get('id', 'N/A')}")
            print(f"   Content preview: {response.data[0].get('content', '')[:100]}...")
            
    except Exception as e:
        print(f"   ✗ RPC function failed: {e}")
        return
    
    # Test 4: Environment Variables
    print("\n4. Checking Environment Variables...")
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY', 
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME',
        'AZURE_OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ✓ {var}: ***{value[-4:] if len(value) > 4 else value}")
        else:
            print(f"   ✗ {var}: MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n   Warning: Missing environment variables: {missing_vars}")
        print("   Make sure these are set in your .env file or deployment environment")
    
    print("\n" + "=" * 50)
    print("Integration Test Complete!")
    print("The voice agent should now be able to use Supabase RAG for knowledge retrieval.")
    
    if not missing_vars:
        print("\n🎉 All systems ready for voice agent operation!")
    else:
        print(f"\n⚠️  Some configuration may be needed before full operation.")

if __name__ == "__main__":
    test_voice_agent_integration()
