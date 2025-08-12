#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

def test_azure_openai_config():
    """Test Azure OpenAI configuration from environment variables"""
    print("Testing Azure OpenAI Configuration...")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT', 
        'AZURE_OPENAI_VERSION',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value[:10]}...{value[-4:] if len(value) > 14 else value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print("\nTesting Azure OpenAI Client...")
    
    try:
        from openai import AzureOpenAI
        print("✅ AzureOpenAI imported successfully")
        
        # Test client creation
        client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version=os.environ.get("AZURE_OPENAI_VERSION", "2024-10-01-preview"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        print("✅ AzureOpenAI client created successfully")
        
        # Test embedding generation
        deployment_name = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        print(f"Testing embedding with deployment: {deployment_name}")
        
        response = client.embeddings.create(
            input="test query for embedding",
            model=deployment_name
        )
        embedding = response.data[0].embedding
        print(f"✅ Embedding generated successfully: {len(embedding)} dimensions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_azure_openai_config()
