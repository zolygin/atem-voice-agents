#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))

# Test various possible function names for atem_voice_documents table
possible_functions = [
    'match_atem_voice_documents',
    'match_atem_voice',
    'match_voice_documents', 
    'match_voice',
    'match_documents',
    'search_atem_voice_documents',
    'search_atem_voice',
    'search_voice_documents',
    'atem_voice_documents_search',
    'voice_documents_match'
]

dummy_vector = [0.1] * 1536

print("Testing possible RPC function names for atem_voice_documents table...")
print("=" * 60)

for func_name in possible_functions:
    try:
        response = supabase.rpc(func_name, {
            'query_embedding': dummy_vector,
            'match_count': 1,
            'filter': {}
        }).execute()
        print(f"✓ {func_name}: SUCCESS - {len(response.data) if response.data else 0} results")
        if response.data:
            print(f"  First result ID: {response.data[0].get('id', 'N/A')}")
    except Exception as e:
        error_msg = str(e)
        if "Could not find the function" in error_msg:
            print(f"✗ {func_name}: Function not found")
        else:
            print(f"? {func_name}: Function exists but error: {error_msg[:50]}...")
