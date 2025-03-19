import os
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    Docx2txtLoader,
    UnstructuredFileLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Set up document storage
DOCUMENTS_DIR = Path("./data/documents")
DOCUMENTS_DIR.mkdir(exist_ok=True, parents=True)

def save_uploaded_file(uploaded_file):
    """Save uploaded file to the documents directory"""
    # Generate a unique filename
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(uploaded_file.name)[1]
    filename = f"{file_id}{file_extension}"
    
    # Save file
    file_path = DOCUMENTS_DIR / filename
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Store metadata
    if "document_metadata" not in st.session_state:
        st.session_state.document_metadata = {}
    
    st.session_state.document_metadata[filename] = {
        "original_name": uploaded_file.name,
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "size": uploaded_file.size,
        "status": "uploaded",
        "processing_error": None
    }
    
    return file_path

def get_document_loader(file_path):
    """Get appropriate document loader based on file extension"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == ".pdf":
        return PyPDFLoader(str(file_path))
    elif file_extension == ".txt":
        return TextLoader(str(file_path))
    elif file_extension in [".docx", ".doc"]:
        return Docx2txtLoader(str(file_path))
    else:
        # Fall back to unstructured loader for other file types
        return UnstructuredFileLoader(str(file_path))

def process_document(file_path):
    """Process a document and return its chunks"""
    try:
        # Get appropriate loader
        loader = get_document_loader(file_path)
        
        # Load document
        documents = loader.load()
        
        # Update metadata
        filename = os.path.basename(file_path)
        if filename in st.session_state.document_metadata:
            st.session_state.document_metadata[filename]["status"] = "loaded"
        
        # Split text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Add source metadata
        for doc in documents:
            doc.metadata["source"] = os.path.basename(file_path)
            doc.metadata["original_name"] = st.session_state.document_metadata[filename]["original_name"]
        
        # Split documents
        splits = text_splitter.split_documents(documents)
        
        # Update metadata
        if filename in st.session_state.document_metadata:
            st.session_state.document_metadata[filename]["status"] = "processed"
            st.session_state.document_metadata[filename]["chunks"] = len(splits)
        
        return splits
    except Exception as e:
        # Update metadata with error
        filename = os.path.basename(file_path)
        if filename in st.session_state.document_metadata:
            st.session_state.document_metadata[filename]["status"] = "error"
            st.session_state.document_metadata[filename]["processing_error"] = str(e)
        
        raise e

def process_documents(uploaded_files):
    """Process multiple documents and return combined chunks"""
    all_splits = []
    
    for uploaded_file in uploaded_files:
        try:
            # Save file
            file_path = save_uploaded_file(uploaded_file)
            
            # Process document
            splits = process_document(file_path)
            all_splits.extend(splits)
            st.success(f"Successfully processed {uploaded_file.name} in {len(splits)} chunks")
            
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    # Mark documents as processed
    st.session_state.documents_processed = True
    
    return all_splits

def get_document_status():
    """Get status of all documents as a DataFrame"""
    if "document_metadata" not in st.session_state or not st.session_state.document_metadata:
        return None
    
    # Convert metadata to DataFrame
    data = []
    for filename, metadata in st.session_state.document_metadata.items():
        row = {
            "Original Name": metadata["original_name"],
            "Upload Date": metadata["upload_date"],
            "Size (KB)": round(metadata["size"] / 1024, 2),
            "Status": metadata["status"],
            "Chunks": metadata.get("chunks", 0),
            "Error": metadata.get("processing_error", "")
        }
        data.append(row)
    
    return pd.DataFrame(data)

def delete_document(filename):
    """Delete a document and its metadata"""
    if filename in st.session_state.document_metadata:
        # Delete file
        file_path = DOCUMENTS_DIR / filename
        if file_path.exists():
            file_path.unlink()
        
        # Delete metadata
        del st.session_state.document_metadata[filename]