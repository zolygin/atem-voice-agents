import os
from typing import Any
from supabase import create_client, Client
from openai import AzureOpenAI
from pypdf import PdfReader
from backend.tools.tools import Tool, ToolResult, ToolResultDirection

def initialize_supabase_client(supabase_url: str, supabase_service_role_key: str) -> Client:
    """Initializes and returns a Supabase client."""
    if not supabase_url or not supabase_service_role_key:
        raise ValueError("Supabase URL and Service Role Key must be provided.")
    return create_client(supabase_url, supabase_service_role_key)

def initialize_openai_client(api_key: str, azure_endpoint: str, api_version: str) -> AzureOpenAI:
    """Initializes and returns an Azure OpenAI client."""
    if not all([api_key, azure_endpoint, api_version]):
        raise ValueError("OpenAI API Key, Azure Endpoint, and API Version must be provided.")
    return AzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version
    )

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
    supabase_client: Client,
    openai_client: AzureOpenAI,
    table_name: str,
    embedding_field: str,
    content_field: str,
    identifier_field: str,
    embedding_model: str,
    args: Any) -> ToolResult:

    query_text = args['query']
    print(f"Searching for '{query_text}' in Supabase table '{table_name}'.")

    embedding_response = await openai_client.embeddings.create(input=query_text, model=embedding_model)
    query_embedding = embedding_response.data[0].embedding

    response = supabase_client.rpc(
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


def search_tool(supabase_client: Client, openai_client: AzureOpenAI, table_name: str, embedding_field: str, content_field: str, identifier_field: str, embedding_model: str) -> Tool:
    return Tool(schema=_search_tool_schema, target=lambda args: _search_tool(supabase_client, openai_client, table_name, embedding_field, content_field, identifier_field, embedding_model, args))

def report_grounding_tool() -> Tool:
    return Tool(schema=_search_tool_schema, target=lambda args: _report_grounding_tool(args))
