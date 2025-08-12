#!/usr/bin/env python3
"""
Script to check available RPC functions in Supabase.
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

def check_rpc_functions():
    """Check what RPC functions are available."""
    load_dotenv()
    
    try:
        print("Checking available RPC functions in Supabase...")
        supabase = get_supabase_client()
        
        # Test common vector search function names
        common_functions = [
            'match_documents',
            'search_documents', 
            'vector_search',
            'find_similar_documents',
            'match_vectors',
            'search_vectors'
        ]
        
        available_functions = []
        
        print("\nTesting common RPC function names:")
        for func_name in common_functions:
            try:
                # Try calling the function with minimal parameters to see if it exists
                response = supabase.rpc(func_name, {}).execute()
                available_functions.append(func_name)
                print(f"  ✓ {func_name}: Available")
            except Exception as e:
                error_msg = str(e).lower()
                if 'function' in error_msg and 'does not exist' in error_msg:
                    print(f"  ✗ {func_name}: Not found")
                else:
                    # Function exists but expects parameters
                    available_functions.append(func_name)
                    print(f"  ✓ {func_name}: Available (requires parameters)")
        
        print(f"\nAvailable RPC functions: {available_functions}")
        
        # If we found vector search functions, test one with parameters
        if available_functions:
            print(f"\nTesting {available_functions[0]} with sample parameters...")
            try:
                response = supabase.rpc(
                    available_functions[0],
                    {
                        'query_embedding': [0.1] * 100,  # Dummy embedding
                        'match_threshold': 0.1,
                        'match_count': 1
                    }
                ).execute()
                print(f"  ✓ Function call successful")
                print(f"  Response data: {len(response.data) if response.data else 0} items")
            except Exception as e:
                print(f"  Function call failed (expected): {str(e)[:100]}...")
        
        return available_functions
        
    except Exception as e:
        print(f"Error checking RPC functions: {e}")
        return []

if __name__ == "__main__":
    check_rpc_functions()
