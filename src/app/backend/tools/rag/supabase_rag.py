import os
from typing import Any
from supabase import create_client, Client
from backend.tools.tools import Tool, ToolResult, ToolResultDirection

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Supabase URL and Service Role Key must be set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

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

async def _search_tool(
    table_name: str,
    embedding_field: str,
    content_field: str,
    identifier_field: str,
    args: Any) -> ToolResult:

    query_text = args['query']
    print(f"Searching for '{query_text}' in Supabase table '{table_name}'.")

    # TODO: Generate embedding for query_text using OpenAI embedding model
    # For now, this is a placeholder. You'll need to integrate OpenAI's embedding API here.
    # Example:
    # from openai import AsyncOpenAI
    # openai_client = AsyncOpenAI(api_key=os.environ.get("AZURE_OPENAI_API_KEY"), azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"), api_version=os.environ.get("AZURE_OPENAI_VERSION"))
    # embedding_response = await openai_client.embeddings.create(input=query_text, model=os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL"))
    # query_embedding = embedding_response.data[0].embedding

    # Placeholder for query_embedding (replace with actual embedding generation)
    query_embedding = [0.0] * 1536 # Assuming 1536 dimensions for text-embedding-3-large

    # Perform vector similarity search in Supabase
    # This assumes you have a 'vector' column in your table and pgvector extension enabled
    response = supabase.rpc(
        'match_documents',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.7, # Adjust as needed
            'match_count': 5 # Number of top results to retrieve
        }
    ).execute()

    if response.data:
        result = ""
        for r in response.data:
            result += f"[{r[identifier_field]}]: {r[content_field]}\n-----\n"
        return ToolResult(result, ToolResultDirection.TO_SERVER)
    else:
        return ToolResult("No relevant documents found.", ToolResultDirection.TO_SERVER)

# TODO: Implement _report_grounding_tool for Supabase if needed
async def _report_grounding_tool(args: Any) -> ToolResult:
    print(f"Grounding sources: {args['sources']}")
    # This would involve fetching the full content of cited documents from Supabase
    # based on their identifiers.
    return ToolResult({"sources": []}, ToolResultDirection.TO_CLIENT)


def search_tool(table_name: str, embedding_field: str, content_field: str, identifier_field: str) -> Tool:
    return Tool(schema=_search_tool_schema, target=lambda args: _search_tool(table_name, embedding_field, content_field, identifier_field, args))

def report_grounding_tool() -> Tool:
    return Tool(schema=_search_tool_schema, target=lambda args: _report_grounding_tool(args))
