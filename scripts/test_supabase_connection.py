#!/usr/bin/env python3
"""
Test script to verify Supabase connection and check database structure.
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

def test_connection():
    """Test the Supabase connection and list tables."""
    load_dotenv()
    
    try:
        print("Testing Supabase connection...")
        supabase = get_supabase_client()
        print(f"✓ Connected to Supabase at: {os.environ.get('SUPABASE_URL')}")
        
        # Try to list tables (this might not work depending on permissions)
        print("\nChecking database structure...")
        
        # Try to get table names by querying information schema
        try:
            tables_response = supabase.table('pg_tables').select('tablename').eq('schemaname', 'public').execute()
            print("Tables in public schema:")
            for table in tables_response.data:
                print(f"  - {table['tablename']}")
        except Exception as e:
            print(f"Could not list tables directly: {e}")
        
        # Check if your specific table exists
        table_name = 'atem_voice_documents'
        try:
            # Try to get a count of rows in the table
            count_response = supabase.table(table_name).select('*', count='exact').limit(1).execute()
            print(f"\n✓ Table '{table_name}' exists!")
            print(f"  Found {count_response.count} rows in the table")
            
            # Show first row structure
            if count_response.data and len(count_response.data) > 0:
                first_row = count_response.data[0]
                print(f"  Columns in table: {list(first_row.keys())}")
                
        except Exception as e:
            print(f"✗ Table '{table_name}' not found or not accessible: {e}")
        
        # Check if 'documents' table exists
        table_name = 'documents'
        try:
            count_response = supabase.table(table_name).select('*', count='exact').limit(1).execute()
            print(f"\n✓ Table '{table_name}' exists!")
            print(f"  Found {count_response.count} rows in the table")
        except Exception as e:
            print(f"✗ Table '{table_name}' not found or not accessible: {e}")
            
        # Check for RPC functions
        print("\nChecking for RPC functions...")
        try:
            # This is a common way to check available functions, but might not work
            # You'll need to check your Supabase dashboard for actual function names
            print("Please check your Supabase dashboard for available RPC functions")
            print("Look for functions like 'match_documents' or similar vector search functions")
        except Exception as e:
            print(f"Could not list RPC functions: {e}")
            
    except Exception as e:
        print(f"✗ Failed to connect to Supabase: {e}")
        print("Please check your SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables")

if __name__ == "__main__":
    test_connection()
