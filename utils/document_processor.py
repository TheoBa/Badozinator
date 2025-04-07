from typing import Dict, Any, List, Tuple
import docx2txt
from pypdf import PdfReader
from bs4 import BeautifulSoup
import re
from .embeddings import get_mistral_embeddings
import numpy as np
import streamlit as st

def process_text_document(text: str, title: str, source: str) -> Tuple[Dict[str, Any], List[str]]:
    """Process a text document and split it into chunks"""
    # Clean the text
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split into chunks (roughly 1000 words each)
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_chunk.append(word)
        current_length += 1
        if current_length >= 1000:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    st.write(f"Created {len(chunks)} chunks for {title}")
    return {
        "title": title,
        "source": source,
        "chunks": chunks,
        "type": "text"
    }, chunks

def process_pdf(file_path: str) -> Tuple[Dict[str, Any], List[str]]:
    """Process a PDF file"""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        if not text.strip():
            st.error(f"No text extracted from PDF: {file_path}")
            return None, []
            
        st.write(f"Extracted {len(text.split())} words from PDF")
        return process_text_document(text, file_path.split('/')[-1], "pdf")
    except Exception as e:
        st.error(f"Error processing PDF {file_path}: {str(e)}")
        return None, []

def process_docx(file_path: str) -> Tuple[Dict[str, Any], List[str]]:
    """Process a DOCX file"""
    try:
        text = docx2txt.process(file_path)
        if not text.strip():
            st.error(f"No text extracted from DOCX: {file_path}")
            return None, []
            
        st.write(f"Extracted {len(text.split())} words from DOCX")
        return process_text_document(text, file_path.split('/')[-1], "docx")
    except Exception as e:
        st.error(f"Error processing DOCX {file_path}: {str(e)}")
        return None, []

def process_html(html_content: str, title: str, source: str) -> Tuple[Dict[str, Any], List[str]]:
    """Process HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        if not text.strip():
            st.error(f"No text extracted from HTML: {title}")
            return None, []
            
        st.write(f"Extracted {len(text.split())} words from HTML")
        return process_text_document(text, title, source)
    except Exception as e:
        st.error(f"Error processing HTML {title}: {str(e)}")
        return None, []

def get_document_embeddings(chunks: List[str]) -> List[np.ndarray]:
    """Get embeddings for all chunks in a document"""
    embeddings = get_mistral_embeddings()
    if not embeddings:
        st.error("Failed to initialize embeddings")
        return []
    
    try:
        chunk_embeddings = [embeddings.embed_query(chunk) for chunk in chunks]
        st.write(f"Generated {len(chunk_embeddings)} embeddings")
        return chunk_embeddings
    except Exception as e:
        st.error(f"Error generating embeddings: {str(e)}")
        return [] 