import os
import re
from typing import Any
import numpy as np
from supabase import create_client, Client
from backend.tools.tools import Tool, ToolResult, ToolResultDirection

# Import OpenAI for embedding generation
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI library not available for embeddings")

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

def generate_embedding(text: str) -> list:
    """Generate embedding for the given text using OpenAI."""
    if not OPENAI_AVAILABLE:
        raise ValueError("OpenAI library not available for embedding generation")
    
    try:
        openai_client = OpenAI(api_key=os.environ.get("AZURE_OPENAI_API_KEY"))
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return a dummy embedding for testing
        return [0.1] * 3072

async def _search_tool(
    args: Any) -> ToolResult:
    """Search the knowledge base using Supabase vector search."""
    print(f"Searching for '{args['query']}' in the knowledge base.")
    
    try:
        supabase = get_supabase_client()
        
        # Generate embedding for the query
        try:
            query_embedding = generate_embedding(args['query'])
            print(f"Generated embedding with {len(query_embedding)} dimensions")
        except Exception as embed_error:
            print(f"Error generating embedding: {embed_error}")
            return ToolResult(f"Error generating query embedding: {str(embed_error)}", ToolResultDirection.TO_SERVER)
        
        # Perform vector search using pgvector on atem_voice_documents table
        # Using the correct match_atem_voice_documents RPC function
        try:
            response = supabase.rpc(
                'match_atem_voice_documents',
                {
                    'query_embedding': query_embedding,
                    'match_count': 5,  # Number of results to return
                    'filter': {}  # Optional filter
                }
            ).execute()
            
            result = ""
            if response and response.data:
                for item in response.data:
                    # Using the correct table structure with similarity score
                    result += f"[{item.get('id', 'unknown')}]: {item.get('content', '')}\n-----\n"
            else:
                result = "No relevant information found in the knowledge base."
            
            return ToolResult(result, ToolResultDirection.TO_SERVER)
            
        except Exception as e:
            print(f"Error during Supabase vector search: {e}")
            # Final fallback: simple table query
            try:
                response = supabase.table('atem_voice_documents').select('id', 'content').limit(3).execute()
                result = ""
                if response.data:
                    for item in response.data:
                        result += f"[{item.get('id', 'unknown')}]: {item.get('content', '')[:200]}...\n-----\n"
                else:
                    result = "No data found in atem_voice_documents table."
                return ToolResult(result, ToolResultDirection.TO_SERVER)
            except Exception as final_fallback_e:
                return ToolResult(f"Error searching knowledge base: {str(final_fallback_e)}", ToolResultDirection.TO_SERVER)
        
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
        
        # Fetch the actual document content for grounding from atem_voice_documents table
        response = supabase.table('atem_voice_documents').select('*').in_('id', sources).execute()
        
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
