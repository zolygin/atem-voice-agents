#!/usr/bin/env python3
"""
PDF processing utilities for Supabase RAG system.
"""

import PyPDF2
from pathlib import Path
from typing import List

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""
    
    return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    words = text.split()
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
    
    return chunks
