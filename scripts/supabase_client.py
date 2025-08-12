#!/usr/bin/env python3
"""
Supabase client utilities for RAG system.
"""

import os
from typing import List, Dict, Any
from supabase import create_client, Client
from openai import OpenAI

def get_supabase_client() -> Client:
    """Initialize and return a Supabase client using environment variables."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL and Service Role Key must be provided.")

    return create_client(url, key)

def get_openai_client() -> OpenAI:
    """Initialize and return an OpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be provided.")
    
    return OpenAI(api_key=api_key)

def generate_embedding(text: str, client: OpenAI) -> List[float]:
    """Generate embedding for text using OpenAI."""
    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def ingest_document_to_supabase(
    document_id: str,
    title: str,
    content: str,
    embedding: List[float],
    supabase: Client
) -> bool:
    """Ingest a document chunk into Supabase."""
    try:
        # Insert document into the 'documents' table
        # Assumes table structure:
        # - id (TEXT, PRIMARY KEY)
        # - title (TEXT)
        # - content (TEXT)
        # - embedding (VECTOR(3072))
        # - metadata (JSONB)
        
        data = {
            "id": document_id,
            "title": title,
            "content": content,
            "embedding": embedding,
            "metadata": {
                "ingested_at": "now()",
                "source": "pdf_ingestion"
            }
        }
        
        response = supabase.table('documents').insert(data).execute()
        return True
        
    except Exception as e:
        print(f"Error ingesting document {document_id}: {e}")
        return False
