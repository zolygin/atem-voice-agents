# Supabase Integration Guide for Realtime Call Center Solution Accelerator

This guide details the steps to correctly integrate Supabase as a replacement for Azure AI Search in the "Realtime Call Center Solution Accelerator". This will ensure proper environment variable handling and successful deployment.

## 1. Update `azure.yaml`

The `azure.yaml` file needs to be updated to define the Supabase URL and Service Role Key as environment variables that `azd` can manage.

**Action:** Add the following environment variables under the `services.app.env` section in `azure.yaml`.

```yaml
# azure.yaml
services:
  app:
    project: ./src/app
    language: py
    host: containerapp
    env:
      # ... existing environment variables ...
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}
```

**Explanation:**
- `SUPABASE_URL`: The URL of your Supabase project.
- `SUPABASE_SERVICE_ROLE_KEY`: The service role key from your Supabase project. This key has elevated privileges, so treat it as a secret.

## 2. Modify Bicep Templates

We need to ensure that the Supabase environment variables are correctly passed from `azd` to the Azure Container App. This involves modifications in `infra/main.bicep` and `infra/core/app/web.bicep`.

### 2.1. `infra/main.bicep`

**Action:** Pass the Supabase URL and Service Role Key as parameters to the `web.bicep` module.

```bicep
// infra/main.bicep
module web 'core/app/web.bicep' = {
  name: 'web'
  params: {
    // ... existing parameters ...
    supabaseUrl: supabaseUrl
    supabaseServiceRoleKey: supabaseServiceRoleKey
  }
}
```

**Explanation:** This makes the Supabase variables available to the `web.bicep` module.

### 2.2. `infra/core/app/web.bicep`

**Action:**
1.  Add `supabaseUrl` and `supabaseServiceRoleKey` as parameters to the module.
2.  Pass these parameters as environment variables to the Container App.

```bicep
// infra/core/app/web.bicep
param supabaseUrl string
param supabaseServiceRoleKey string

resource web 'Microsoft.App/containerApps@2023-05-01' = {
  // ... existing properties ...
  properties: {
    // ... existing properties ...
    template: {
      // ... existing properties ...
      containers: [
        {
          // ... existing properties ...
          env: [
            // ... existing environment variables ...
            {
              name: 'SUPABASE_URL'
              value: supabaseUrl
            }
            {
              name: 'SUPABASE_SERVICE_ROLE_KEY'
              secretRef: 'supabase-service-role-key' // Reference a secret
            }
          ]
        }
      ]
      secrets: [
        {
          name: 'supabase-service-role-key'
          value: supabaseServiceRoleKey
        }
      ]
    }
  }
}
```

**Explanation:**
- We define `supabaseUrl` and `supabaseServiceRoleKey` as parameters for this Bicep module.
- `SUPABASE_URL` is passed directly as an environment variable.
- `SUPABASE_SERVICE_ROLE_KEY` is passed as a secret reference (`secretRef`) to enhance security, as it contains sensitive information. The actual value is stored in the `secrets` array.

## 3. Modify `azd-hooks/deploy.sh`

The `deploy.sh` script can be used to set environment variables before deployment. While the Bicep changes handle passing the variables, it's good practice to ensure `azd` is aware of them.

**Action:** Add the following lines to `azd-hooks/deploy.sh` to export the Supabase variables. You will need to set these values in your local environment or `azd` environment.

```bash
# azd-hooks/deploy.sh
#!/bin/bash

# ... existing script content ...

# Export Supabase environment variables
export SUPABASE_URL=${SUPABASE_URL:-""}
export SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY:-""}

# Ensure they are not empty
if [ -z "$SUPABASE_URL" ]; then
  echo "SUPABASE_URL is not set. Please set it in your environment or .env file."
  exit 1
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
  echo "SUPABASE_SERVICE_ROLE_KEY is not set. Please set it in your environment or .env file."
  exit 1
fi

# ... rest of the script ...
```

**Explanation:** This script ensures that `azd` picks up these environment variables from your local shell or `.env` file (if you use `azd env set` or similar) and passes them to the Bicep templates. The `:-""` provides a default empty string if the variable is not set, and the `if` conditions ensure that deployment fails if these critical variables are missing.

## 4. Modify Python Code (`src/app/backend/tools/rag/supabase_rag.py`)

You mentioned `src/app/backend/tools/rag/supabase_rag.py` as the implementation for RAG with Supabase. You will need to ensure this file correctly reads the `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from environment variables.

**Action:** Ensure your `supabase_rag.py` (or the relevant RAG implementation file) initializes the Supabase client using `os.environ`.

```python
# src/app/backend/tools/rag/supabase_rag.py (Example)
import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL and Service Role Key must be provided.")

    return create_client(url, key)

# Example usage in your RAG logic:
# supabase_client = get_supabase_client()
# # Use supabase_client for your RAG operations
```

**Explanation:** This code snippet demonstrates how to retrieve the environment variables within your Python application. The `ValueError` you previously encountered indicates that these variables were not correctly propagated to the Container App, which these Bicep and `azd-hooks` changes aim to fix.

## 5. Create Data Ingestion Script (`scripts/ingest_data_to_supabase.py`)

You mentioned `scripts/ingest_data_to_supabase.py` for data ingestion. This script will replace the `upload_data.sh` and `infra/definitions` files used for Azure AI Search.

**Action:** Create this Python script to handle data loading from your `data/` directory into Supabase, including embedding generation and `pgvector` insertion.

```python
# scripts/ingest_data_to_supabase.py (Example structure)
import os
from supabase import create_client, Client
from dotenv import load_dotenv
# Assuming you have a way to generate embeddings, e.g., with OpenAI
# from openai import OpenAI

load_dotenv() # Load environment variables from .env file for local execution

def get_supabase_client() -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL and Service Role Key must be provided.")

    return create_client(url, key)

def ingest_data_to_supabase(data_path: str):
    supabase_client = get_supabase_client()
    # openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) # Example for embeddings

    # 1. Read data from data_path (e.g., PDF documents)
    # 2. Process and chunk the data
    # 3. Generate embeddings for each chunk using OpenAI or similar
    # 4. Insert data and embeddings into your Supabase table (e.g., 'documents' table with 'content' and 'embedding' columns)

    print(f"Ingesting data from {data_path} to Supabase...")
    # Example:
    # for doc in processed_documents:
    #     embedding = openai_client.embeddings.create(input=doc.content, model="text-embedding-ada-002").data[0].embedding
    #     supabase_client.table('documents').insert({'content': doc.content, 'embedding': embedding}).execute()
    print("Data ingestion complete.")

if __name__ == "__main__":
    # Ensure your .env file has SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and OPENAI_API_KEY
    # Example usage:
    ingest_data_to_supabase("data/")
```

**Explanation:** This script will be responsible for:
-   Loading environment variables (for local testing).
-   Initializing the Supabase client.
-   Reading your data (e.g., PDFs).
-   Processing and chunking the data.
-   Generating embeddings for the text chunks (e.g., using OpenAI's embedding models).
-   Inserting the text and their corresponding embeddings into a Supabase table configured with `pgvector`.

## Next Steps for You

1.  **Set Supabase Environment Variables**: Before running `azd up`, ensure you set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in your `azd` environment. You can do this using:
    ```bash
    azd env set SUPABASE_URL "YOUR_SUPABASE_URL"
    azd env set SUPABASE_SERVICE_ROLE_KEY "YOUR_SUPABASE_SERVICE_ROLE_KEY"
    ```
    Replace `"YOUR_SUPABASE_URL"` and `"YOUR_SUPABASE_SERVICE_ROLE_KEY"` with your actual Supabase project details.

2.  **Run `azd up`**: Execute `azd up` to deploy the updated infrastructure and application. This should now correctly pass the Supabase environment variables.

3.  **Run Data Ingestion**: After successful deployment, run your `scripts/ingest_data_to_supabase.py` script locally to populate your Supabase database with data.

4.  **Test the Agent**: Verify that the voice agent correctly uses Supabase for RAG operations.

I have provided the detailed steps for integrating Supabase. Please review these changes and let me know if you'd like to proceed with implementing them.
