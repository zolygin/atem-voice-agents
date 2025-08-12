import os
import re
from typing import Any
from supabase import create_client, Client
from backend.tools.tools import Tool, ToolResult, ToolResultDirection

KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_=\-]+$')

_search_tool_schema = {
    "type": "function",
    "name": "search",
    "description": "Search the knowledge base. The knowledge base is in English, translate to and from English if " + \
                   "needed. Results are formatted as a source name first in square brackets, followed by the text " + \
                   "content, and a line with '-----' at the end of each result.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

_grounding_tool_schema = {
    "type": "function",
    "name": "report_grounding",
    "description": "Report use of a source from the knowledge base as part of an answer (effectively, cite the source). Sources " + \
                   "appear in square brackets before each knowledge base passage. Always use this tool to cite sources when responding " + \
                   "with information from the knowledge base.",
    "parameters": {
        "type": "object",
        "properties": {
            "sources": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of source names from last statement actually used, do not include the ones not used to formulate a response"
            }
        },
        "required": ["sources"],
        "additionalProperties": False
    }
}

def get_supabase_client() -> Client:
    """Initialize and return a Supabase client using environment variables."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL and Service Role Key must be provided.")

    return create_client(url, key)

async def _search_tool(
    args: Any) -> ToolResult:
    """Search the knowledge base using Supabase vector search."""
    print(f"Searching for '{args['query']}' in the knowledge base.")
    
    try:
        supabase = get_supabase_client()
        
        # Perform vector search using pgvector
        # This assumes you have a table called 'documents' with columns:
        # - id (primary key)
        # - content (text)
        # - embedding (vector)
        # - metadata (jsonb, optional)
        
        response = supabase.rpc(
            'match_documents',
            {
                'query_embedding': args['query'],  # This will be converted to embedding by the RPC function
                'match_threshold': 0.7,  # Adjust similarity threshold as needed
                'match_count': 5  # Number of results to return
            }
        ).execute()
        
        result = ""
        if response.data:
            for item in response.data:
                # Assuming the table has 'id' and 'content' columns
                result += f"[{item.get('id', 'unknown')}]: {item.get('content', '')}\n-----\n"
        
        return ToolResult(result, ToolResultDirection.TO_SERVER)
        
    except Exception as e:
        print(f"Error during Supabase search: {e}")
        return ToolResult(f"Error searching knowledge base: {str(e)}", ToolResultDirection.TO_SERVER)

async def _report_grounding_tool(args: Any) -> ToolResult:
    """Report use of sources from the knowledge base."""
    sources = [s for s in args["sources"] if KEY_PATTERN.match(s)]
    list_str = " OR ".join(sources)
    print(f"Grounding source: {list_str}")
    
    try:
        supabase = get_supabase_client()
        
        # Fetch the actual document content for grounding
        response = supabase.table('documents').select('*').in_('id', sources).execute()
        
        docs = []
        if response.data:
            for item in response.data:
                docs.append({
                    "chunk_id": item.get('id', ''),
                    "title": item.get('metadata', {}).get('title', 'Untitled'),
                    "chunk": item.get('content', '')
                })
        
        return ToolResult({"sources": docs}, ToolResultDirection.TO_CLIENT)
        
    except Exception as e:
        print(f"Error during grounding: {e}")
        return ToolResult(f"Error reporting grounding: {str(e)}", ToolResultDirection.TO_CLIENT)

def search_tool() -> Tool:
    """Create and return the search tool for Supabase RAG."""
    return Tool(schema=_search_tool_schema, target=_search_tool)

def report_grounding_tool() -> Tool:
    """Create and return the grounding tool for Supabase RAG."""
    return Tool(schema=_grounding_tool_schema, target=_report_grounding_tool)
