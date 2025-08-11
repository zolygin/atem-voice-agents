import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import AzureOpenAI
from pypdf import PdfReader

# Load environment variables
# The .env file is located in .azure/azd-atem/.env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".azure", "azd-atem", ".env")
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_VERSION = os.environ.get("AZURE_OPENAI_VERSION")
AZURE_OPENAI_EMBEDDING_MODEL = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL")

if not all([SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_VERSION, AZURE_OPENAI_EMBEDDING_MODEL]):
    print("Error: Missing one or more required environment variables for Supabase or OpenAI.")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Initialize OpenAI client
openai_client = AzureOpenAI(
    api_key=OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_VERSION
)

def get_embedding(text: str) -> list[float]:
    """Generates an embedding for the given text using OpenAI."""
    response = openai_client.embeddings.create(
        input=text,
        model=AZURE_OPENAI_EMBEDDING_MODEL
    )
    return response.data[0].embedding

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Chunks text into smaller pieces with optional overlap."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

async def ingest_pdf_to_supabase(file_path: str, table_name: str = "atem_voice_documents"):
    """
    Ingests a PDF file into Supabase, chunking text and generating embeddings.
    """
    print(f"Processing PDF: {file_path}")
    reader = PdfReader(file_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    chunks = chunk_text(full_text)
    file_name = os.path.basename(file_path)

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        metadata = {
            "file_name": file_name,
            "chunk_index": i,
            "total_chunks": len(chunks)
        }
        
        data_to_insert = {
            "content": chunk,
            "metadata": metadata,
            "embedding": embedding
        }

        try:
            response = supabase.table(table_name).insert(data_to_insert).execute()
            if response.data:
                print(f"Inserted chunk {i+1}/{len(chunks)} from {file_name} into Supabase.")
            else:
                print(f"Failed to insert chunk {i+1}/{len(chunks)} from {file_name}: {response.error}")
        except Exception as e:
            print(f"An error occurred during Supabase insertion for {file_name}, chunk {i+1}: {e}")

async def ingest_md_to_supabase(file_path: str, table_name: str = "atem_voice_documents"):
    """
    Ingests a Markdown file into Supabase, chunking text and generating embeddings.
    """
    print(f"Processing Markdown: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        full_text = f.read()

    chunks = chunk_text(full_text)
    file_name = os.path.basename(file_path)

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        metadata = {
            "file_name": file_name,
            "chunk_index": i,
            "total_chunks": len(chunks)
        }
        
        data_to_insert = {
            "content": chunk,
            "metadata": metadata,
            "embedding": embedding
        }

        try:
            response = supabase.table(table_name).insert(data_to_insert).execute()
            if response.data:
                print(f"Inserted chunk {i+1}/{len(chunks)} from {file_name} into Supabase.")
            else:
                print(f"Failed to insert chunk {i+1}/{len(chunks)} from {file_name}: {response.error}")
        except Exception as e:
            print(f"An error occurred during Supabase insertion for {file_name}, chunk {i+1}: {e}")

async def main():
    data_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    if not os.path.exists(data_folder):
        print(f"Data folder not found: {data_folder}")
        sys.exit(1)

    for file_name in os.listdir(data_folder):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(data_folder, file_name)
            await ingest_pdf_to_supabase(file_path)
        elif file_name.lower().endswith(".md"):
            file_path = os.path.join(data_folder, file_name)
            await ingest_md_to_supabase(file_path)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
