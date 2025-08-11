import os
from typing import Any
from backend.tools.tools import Tool, ToolResult, ToolResultDirection
from backend.tools.rag.supabase_rag import search_tool as supabase_search_tool, report_grounding_tool as supabase_report_grounding_tool

# Configuration for Supabase RAG
SUPABASE_RAG_TABLE_NAME = "documents" # As confirmed by the user
SUPABASE_RAG_EMBEDDING_FIELD = "embedding"
SUPABASE_RAG_CONTENT_FIELD = "content"
SUPABASE_RAG_IDENTIFIER_FIELD = "id" # Assuming 'id' is the unique identifier for documents

# Initialize Supabase RAG tools
_supabase_search_tool_instance = supabase_search_tool(
    table_name=SUPABASE_RAG_TABLE_NAME,
    embedding_field=SUPABASE_RAG_EMBEDDING_FIELD,
    content_field=SUPABASE_RAG_CONTENT_FIELD,
    identifier_field=SUPABASE_RAG_IDENTIFIER_FIELD
)

_supabase_report_grounding_tool_instance = supabase_report_grounding_tool()

def search_tool() -> Tool:
    """
    Returns the search tool configured for Supabase RAG.
    """
    return _supabase_search_tool_instance

def report_grounding_tool() -> Tool:
    """
    Returns the report grounding tool configured for Supabase RAG.
    """
    return _supabase_report_grounding_tool_instance
