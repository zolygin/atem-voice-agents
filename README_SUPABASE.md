# ATEM Voice Agents with Supabase RAG Integration

This document explains how the Supabase RAG (Retrieval Augmented Generation) integration works in the ATEM Voice Agents project, replacing the original Azure AI Search implementation.

## Architecture Overview

The voice agent uses Supabase as its knowledge base for RAG operations instead of Azure AI Search. The integration includes:

1. **Supabase Database**: Stores document chunks with vector embeddings
2. **RPC Functions**: Custom PostgreSQL functions for vector similarity search
3. **Python Backend**: Uses Supabase client and OpenAI for embedding generation
4. **Voice Agent Tools**: `search` and `report_grounding` tools integrated with Supabase

## Key Components

### 1. Supabase Database Structure

**Table: `atem_voice_documents`**
- `id` (bigint): Primary key
- `content` (text): Document content/chunk
- `metadata` (jsonb): Additional metadata (title, source, etc.)
- `embedding` (vector): 3072-dimensional vector embedding

**RPC Function: `match_atem_voice_documents`**
```sql
CREATE OR REPLACE FUNCTION public.match_atem_voice_documents(
    query_embedding vector,
    match_count integer DEFAULT NULL::integer,
    filter jsonb DEFAULT '{}'::jsonb
)
RETURNS TABLE(
    id bigint,
    content text,
    metadata jsonb,
    similarity double precision
)
LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        id,
        content,
        metadata,
        1 - (atem_voice_documents.embedding <=> query_embedding) as similarity
    FROM atem_voice_documents
    WHERE metadata @> filter
    ORDER BY atem_voice_documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$function$;
```

### 2. Python Implementation

**File: `src/app/backend/tools/rag/supabase_rag.py`**

Key features:
- **Embedding Generation**: Uses OpenAI `text-embedding-3-large` model (3072 dimensions)
- **Vector Search**: Calls `match_atem_voice_documents` RPC function
- **Fallback Handling**: Uses dummy embeddings if OpenAI fails
- **Tool Integration**: Provides `search` and `report_grounding` tools

### 3. Environment Variables

Required environment variables:
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
AZURE_OPENAI_ENDPOINT=your_openai_endpoint
AZURE_OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME=your_deployment_name
```

## How It Works

### 1. Query Processing Flow

1. **Voice Input**: User asks a question
2. **Embedding Generation**: Query converted to 3072-dim vector using OpenAI
3. **Vector Search**: `match_atem_voice_documents` RPC function finds similar documents
4. **Result Formatting**: Results formatted for LLM context
5. **LLM Response**: OpenAI generates response using retrieved context

### 2. Search Tool (`search`)

```python
# Called by LLM when it needs to search knowledge base
result = supabase.rpc('match_atem_voice_documents', {
    'query_embedding': generated_embedding,
    'match_count': 5,
    'filter': {}
}).execute()
```

### 3. Grounding Tool (`report_grounding`)

```python
# Called by LLM to cite sources
response = supabase.table('atem_voice_documents').select('*').in_('id', sources).execute()
```

## Testing

### Integration Tests

Run the integration test to verify all components work together:
```bash
python scripts/test_voice_agent_integration.py
```

### Manual Testing

1. **Test Supabase Connection**:
   ```bash
   python scripts/test_supabase_connection.py
   ```

2. **Test Search Functionality**:
   ```bash
   python scripts/test_atem_voice_search.py
   ```

3. **Test Voice Agent**:
   ```bash
   cd src/app
   python app.py
   ```

## Deployment

The application is configured to use Supabase RAG automatically when the required environment variables are present. The Azure AI Search code remains as legacy but is not used when Supabase is configured.

### Azure Deployment Configuration

The `azd` deployment automatically sets the required environment variables:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

These are configured in:
- `azure.yaml` (environment variables)
- `infra/main.bicep` (parameter passing)
- `infra/core/app/web.bicep` (container environment)

## Troubleshooting

### Common Issues

1. **OpenAI API Key Invalid**:
   - Update `AZURE_OPENAI_API_KEY` in environment
   - Fallback to dummy embeddings works for testing

2. **Supabase Connection Failed**:
   - Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
   - Check Supabase project status and network access

3. **No Search Results**:
   - Verify documents exist in `atem_voice_documents` table
   - Check that embeddings are properly generated and stored

### Debugging Commands

```bash
# Check Supabase table contents
python -c "from supabase import create_client; import os; s=create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY']); print(s.table('atem_voice_documents').select('id', 'content').limit(3).execute())"

# Test RPC function directly
python -c "from supabase import create_client; import os; s=create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY']); print(s.rpc('match_atem_voice_documents', {'query_embedding': [0.1]*3072, 'match_count': 2}).execute())"
```

## Data Management

### Ingesting New Documents

Use the ingestion script to add new documents:
```bash
python scripts/ingest_data_to_supabase.py
```

The script:
1. Reads documents from `data/` directory
2. Chunks content appropriately
3. Generates embeddings using OpenAI
4. Stores in `atem_voice_documents` table

### Updating Existing Data

To refresh embeddings or update content:
1. Clear existing data: `DELETE FROM atem_voice_documents;`
2. Re-run ingestion script
3. Or update individual records as needed

## Performance Considerations

### Vector Search Optimization

- **Indexing**: Ensure `pgvector` indexes are created on embedding column
- **Dimensions**: Using 3072-dim embeddings (text-embedding-3-large)
- **Similarity**: Cosine similarity via `<=>` operator

### Caching

Consider implementing caching for:
- Frequently accessed documents
- Common query embeddings
- Search results for repeated queries

## Security

### API Keys

- **Supabase Service Role Key**: Used for backend operations (has elevated privileges)
- **OpenAI API Key**: Used for embedding generation
- Store securely in environment variables or Azure Key Vault

### Data Access

- RPC functions limit data exposure
- Row-level security can be added if needed
- Metadata filtering available through JSONB queries

## Future Enhancements

### Planned Improvements

1. **Better Error Handling**: More robust fallback mechanisms
2. **Caching Layer**: Redis or in-memory caching for frequent queries
3. **Advanced Filtering**: More sophisticated metadata filtering
4. **Batch Operations**: Bulk ingestion and updates
5. **Monitoring**: Better logging and performance metrics

### Alternative Embedding Models

Support for different embedding models:
- `text-embedding-3-small` (1536 dimensions)
- `text-embedding-ada-002` (1536 dimensions)
- Custom embedding services

Update the dimension in the RPC function and embedding generation code accordingly.
