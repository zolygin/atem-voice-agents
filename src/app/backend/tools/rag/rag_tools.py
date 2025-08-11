import os
from typing import Any
from backend.tools.tools import Tool, ToolResult, ToolResultDirection
from backend.tools.rag.supabase_rag import search_tool as supabase_search_tool, report_grounding_tool as supabase_report_grounding_tool, initialize_supabase_client, initialize_openai_client

# Configuration for Supabase RAG
SUPABASE_RAG_TABLE_NAME = "atem_voice_documents"
SUPABASE_RAG_EMBEDDING_FIELD = "embedding"
SUPABASE_RAG_CONTENT_FIELD = "content"
SUPABASE_RAG_IDENTIFIER_FIELD = "id" # Assuming 'id' is the unique identifier for documents

# These will be initialized in app.py and passed here
_supabase_client = None
_openai_client = None
_embedding_model = None

def initialize_rag_tools(supabase_url: str, supabase_service_role_key: str, openai_api_key: str, azure_openai_endpoint: str, azure_openai_version: str, azure_openai_embedding_model: str):
    global _supabase_client, _openai_client, _embedding_model
    _supabase_client = initialize_supabase_client(supabase_url, supabase_service_role_key)
    _openai_client = initialize_openai_client(openai_api_key, azure_openai_endpoint, azure_openai_version)
    _embedding_model = azure_openai_embedding_model

def search_tool() -> Tool:
    """
    Returns the search tool configured for Supabase RAG.
    """
    if _supabase_client is None or _openai_client is None or _embedding_model is None:
        raise ValueError("RAG tools not initialized. Call initialize_rag_tools first.")
    return supabase_search_tool(
        supabase_client=_supabase_client,
        openai_client=_openai_client,
        table_name=SUPABASE_RAG_TABLE_NAME,
        embedding_field=SUPABASE_RAG_EMBEDDING_FIELD,
        content_field=SUPABASE_RAG_CONTENT_FIELD,
        identifier_field=SUPABASE_RAG_IDENTIFIER_FIELD,
        embedding_model=_embedding_model
    )

def report_grounding_tool() -> Tool:
    """
    Returns the report grounding tool configured for Supabase RAG.
    """
    return supabase_report_grounding_tool()
