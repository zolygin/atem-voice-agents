#!/usr/bin/env python3
import os
from supabase import create_client
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_embedding(text: str) -> list:
    """Generate embedding for the given text using Azure OpenAI."""
    try:
        # Use Azure OpenAI client with proper Azure configuration
        openai_client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version=os.environ.get("AZURE_OPENAI_VERSION", "2024-10-01-preview"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        
        # Use the deployment name for Azure OpenAI
        deployment_name = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        
        response = openai_client.embeddings.create(
            input=text,
            model=deployment_name
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding with Azure OpenAI: {e}")
        # Return a dummy embedding for testing
        return [0.1] * 3072

def test_atem_voice_search():
    """Test the match_atem_voice_documents function"""
    try:
        supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))
        print("Connected to Supabase successfully")
        
        # Test embedding generation
        print("Testing embedding generation...")
        test_query = "What are your music marketing prices?"
        query_embedding = generate_embedding(test_query)
        print(f"Generated embedding with {len(query_embedding)} dimensions")
        
        # Test the RPC function with proper vector
        print("Testing match_atem_voice_documents RPC function...")
        try:
            response = supabase.rpc('match_atem_voice_documents', {
                'query_embedding': query_embedding,
                'match_count': 3,
                'filter': {}
            }).execute()
            
            print(f"RPC call successful!")
            print(f"Number of results: {len(response.data) if response.data else 0}")
            
            if response.data:
                print("Sample results:")
                for i, item in enumerate(response.data[:2]):
                    print(f"  Result {i+1}: ID={item.get('id')}")
                    content = item.get('content', '')
                    print(f"    Content preview: {content[:150]}...")
                    print(f"    Similarity: {item.get('similarity', 'N/A')}")
                    print()
            else:
                print("No results found")
                
        except Exception as rpc_error:
            print(f"RPC function error: {rpc_error}")
            
            # Try simple table query as fallback
            print("Trying simple table query...")
            try:
                response = supabase.table('atem_voice_documents').select('id', 'content').limit(3).execute()
                print(f"Simple query successful! Found {len(response.data)} rows")
                for item in response.data:
                    print(f"  ID: {item.get('id')}, Content: {item.get('content', '')[:50]}...")
            except Exception as table_error:
                print(f"Simple table query also failed: {table_error}")
                
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_atem_voice_search()
