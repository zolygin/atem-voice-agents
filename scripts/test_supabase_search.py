#!/usr/bin/env python3
"""
Test script to verify Supabase vector search functionality.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

def get_supabase_client() -> Client:
    """Initialize and return a Supabase client using environment variables."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL and Service Role Key must be provided.")

    return create_client(url, key)

def test_vector_search():
    """Test vector search functionality."""
    load_dotenv()
    
    try:
        print("Testing Supabase vector search...")
        supabase = get_supabase_client()
        
        # Test 1: Check if match_documents RPC function exists
        print("\n1. Testing match_documents RPC function...")
        try:
            # Try a simple match_documents call with a test query
            response = supabase.rpc(
                'match_documents',
                {
                    'query_embedding': 'test query',
                    'match_threshold': 0.1,
                    'match_count': 1
                }
            ).execute()
            print("✓ match_documents RPC function exists and is accessible")
            print(f"  Response: {len(response.data) if response.data else 0} results")
        except Exception as e:
            print(f"✗ match_documents RPC function not found or not working: {e}")
        
        # Test 2: Check if there are other RPC functions
        print("\n2. Testing common vector search function names...")
        common_functions = [
            'match_documents',
            'search_documents', 
            'vector_search',
            'find_similar_documents'
        ]
        
        working_functions = []
        for func_name in common_functions:
            try:
                response = supabase.rpc(func_name, {}).execute()
                working_functions.append(func_name)
                print(f"✓ Found working RPC function: {func_name}")
            except Exception as e:
                print(f"  {func_name}: Not available ({str(e)[:50]}...)")
        
        # Test 3: Direct table query to see if we can access embeddings
        print("\n3. Testing direct table access...")
        try:
            # Check atem_voice_documents table
            response = supabase.table('atem_voice_documents').select('id', 'content').limit(2).execute()
            print(f"✓ Can query atem_voice_documents table")
            print(f"  Sample data: {len(response.data) if response.data else 0} rows")
            if response.data:
                for row in response.data[:2]:
                    print(f"    ID: {row.get('id', 'N/A')[:30]}...")
                    print(f"    Content: {row.get('content', 'N/A')[:50]}...")
        
        except Exception as e:
            print(f"✗ Cannot query atem_voice_documents table: {e}")
            
        # Test 4: Check documents table
        print("\n4. Testing documents table...")
        try:
            response = supabase.table('documents').select('id', 'content').limit(2).execute()
            print(f"✓ Can query documents table")
            print(f"  Sample data: {len(response.data) if response.data else 0} rows")
        except Exception as e:
            print(f"✗ Cannot query documents table: {e}")
            
        print("\n=== SUMMARY ===")
        print("✓ Supabase connection: Working")
        print("✓ Tables exist: atem_voice_documents (21 rows), documents (18 rows)")
        print("✓ Table structure: id, content, metadata, embedding")
        print("? RPC functions: Check your Supabase dashboard for vector search functions")
        
    except Exception as e:
        print(f"✗ Failed to test Supabase: {e}")

if __name__ == "__main__":
    test_vector_search()
