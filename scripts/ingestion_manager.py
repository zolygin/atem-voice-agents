#!/usr/bin/env python3
"""
Main ingestion manager for Supabase RAG system.
"""

import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Add the src directory to Python path to import backend modules
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from pdf_processor import extract_text_from_pdf, chunk_text
from supabase_client import get_supabase_client, get_openai_client, generate_embedding, ingest_document_to_supabase

def process_pdf_document(
    pdf_path: Path,
    supabase,
    openai_client
) -> int:
    """Process a PDF document and ingest its content into Supabase."""
    print(f"Processing PDF: {pdf_path}")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print(f"No text extracted from {pdf_path}")
        return 0
    
    # Chunk text
    chunks = chunk_text(text)
    print(f"Split into {len(chunks)} chunks")
    
    # Process each chunk
    successful_ingestions = 0
    base_name = pdf_path.stem
    
    for i, chunk in enumerate(chunks):
        # Generate unique ID for this chunk
        chunk_id = f"{base_name}_{i}"
        
        # Generate embedding
        embedding = generate_embedding(chunk, openai_client)
        if not embedding:
            print(f"Failed to generate embedding for chunk {i}")
            continue
        
        # Ingest into Supabase
        success = ingest_document_to_supabase(
            document_id=chunk_id,
            title=f"{pdf_path.name} - Chunk {i}",
            content=chunk,
            embedding=embedding,
            supabase=supabase
        )
        
        if success:
            successful_ingestions += 1
            print(f"Ingested chunk {i} successfully")
        else:
            print(f"Failed to ingest chunk {i}")
    
    return successful_ingestions

def main():
    """Main function to ingest all PDF documents from the data directory."""
    # Load environment variables
    load_dotenv()
    
    # Get data directory
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    # Initialize clients
    try:
        supabase = get_supabase_client()
        openai_client = get_openai_client()
    except ValueError as e:
        print(f"Error initializing clients: {e}")
        return
    
    # Find all PDF files
    pdf_files = list(data_dir.glob('*.pdf'))
    if not pdf_files:
        print("No PDF files found in data directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    total_chunks = 0
    successful_chunks = 0
    
    # Process each PDF file
    for pdf_file in pdf_files:
        chunks_processed = process_pdf_document(pdf_file, supabase, openai_client)
        successful_chunks += chunks_processed
        total_chunks += chunks_processed  # This counts successful ingestions
    
    print(f"\nIngestion complete!")
    print(f"Successfully ingested {successful_chunks} chunks")
    print(f"Total chunks processed: {total_chunks}")

if __name__ == "__main__":
    main()
