# Supabase Integration Guide

This guide explains how to integrate Supabase as a replacement for Azure AI Search in the Realtime Call Center Solution Accelerator.

## Prerequisites

1. A Supabase project with `pgvector` extension enabled
2. Supabase URL and Service Role Key
3. OpenAI API key for embedding generation

## Setup Instructions

### 1. Environment Variables

Set the following environment variables:

```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_ROLE_KEY="your-supabase-service-role-key"
export OPENAI_API_KEY="your-openai-api-key"
```

Or use `azd` to set them:

```bash
azd env set SUPABASE_URL "your-supabase-url"
azd env set SUPABASE_SERVICE_ROLE_KEY "your-supabase-service-role-key"
```

### 2. Supabase Database Setup

Create the required table structure in your Supabase database:

```sql
-- Enable pgvector extension
create extension if not exists vector;

-- Create documents table
create table documents (
    id text primary key,
    title text,
    content text,
    embedding vector(3072),
    metadata jsonb,
    created_at timestamp with time zone default now()
);

-- Create index for vector similarity search
create index on documents using ivfflat (embedding vector_cosine_ops);

-- Create RPC function for similarity search
create or replace function match_documents (
    query_embedding vector(3072),
    match_threshold float,
    match_count int
)
returns table (
    id text,
    title text,
    content text,
    metadata jsonb,
    similarity float
)
language sql
as $$
    select
        documents.id,
        documents.title,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) as similarity
    from documents
    where 1 - (documents.embedding <=> query_embedding) > match_threshold
    order by documents.embedding <=> query_embedding
    limit match_count;
$$;
```

### 3. Data Ingestion

Run the data ingestion script to process PDF documents and store them in Supabase:

```bash
python scripts/ingest_data_to_supabase.py
```

### 4. Deployment

Deploy the application using `azd`:

```bash
azd up
```

## Key Changes Made

### Infrastructure (Bicep)
- Added `supabaseUrl` and `supabaseServiceRoleKey` parameters to `infra/main.bicep`
- Updated `infra/core/app/web.bicep` to pass Supabase environment variables to the container

### Configuration
- Updated `azure.yaml` to include Supabase environment variables
- Modified `azd-hooks/deploy.sh` to handle Supabase parameters and validation

### Application Code
- Created `src/app/backend/tools/rag/supabase_rag.py` with Supabase-based RAG implementation
- Updated `src/app/app.py` to use Supabase RAG tools instead of Azure AI Search
- Added Supabase dependencies to `src/app/requirements.txt`

### Data Processing
- Created `scripts/ingest_data_to_supabase.py` for PDF processing and vector embedding

## Testing

After deployment, verify that the Supabase integration is working:

1. Check that environment variables are properly set in the container
2. Test the search functionality through the voice agent
3. Verify that document grounding works correctly

## Troubleshooting

### Common Issues

1. **"Supabase URL and Service Role Key must be provided"**
   - Ensure environment variables are set correctly
   - Check that `azd` environment variables are configured

2. **Vector search not returning results**
   - Verify that the `match_documents` RPC function exists
   - Check that documents have been properly ingested with embeddings

3. **Connection errors**
   - Verify Supabase URL and credentials
   - Check network connectivity from the container to Supabase

### Debugging Steps

1. Check container logs:
   ```bash
   az containerapp logs show --name <container-app-name> --resource-group <resource-group>
   ```

2. Test Supabase connection locally:
   ```bash
   python -c "from supabase import create_client; client = create_client('url', 'key'); print(client.table('documents').select('*').execute())"
   ```

3. Verify environment variables in the container:
   ```bash
   az containerapp exec --name <container-app-name> --resource-group <resource-group> --command "printenv"
