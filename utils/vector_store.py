import os
import streamlit as st
from pathlib import Path
from utils.embeddings import get_mistral_embeddings
from utils.documents import DOCUMENTS_DIR, process_document
from langchain_community.vectorstores import FAISS, Pinecone

# Vector store directory
VECTOR_STORE_DIR = Path("./data/vector_store")
VECTOR_STORE_DIR.mkdir(exist_ok=True, parents=True)

def initialize_vector_store():
    """Initialize vector store with processed documents"""
    if "document_metadata" not in st.session_state or not st.session_state.document_metadata:
        st.warning("No documents have been processed yet")
        return None
    
    # Get all processed documents
    all_splits = []
    for filename, metadata in st.session_state.document_metadata.items():
        if metadata["status"] == "processed":
            file_path = DOCUMENTS_DIR / filename
            if file_path.exists():
                splits = process_document(file_path)
                all_splits.extend(splits)
    
    if not all_splits:
        st.warning("No processed documents found")
        return None
    
    # Get embeddings
    embeddings = get_mistral_embeddings()
    if not embeddings:
        return None
    
    # Create vector store
    if st.session_state.get("use_pinecone", False):
        # Check if Pinecone details are available
        if not all(key in st.session_state for key in ["pinecone_api_key", "pinecone_env", "pinecone_index"]):
            st.error("Pinecone settings not found")
            return None
        
        # Initialize Pinecone
        import pinecone
        
        pinecone.init(
            api_key=st.session_state.pinecone_api_key,
            environment=st.session_state.pinecone_env
        )
        
        # Create vector store
        vector_store = Pinecone.from_documents(
            all_splits,
            embeddings,
            index_name=st.session_state.pinecone_index
        )
    else:
        # Use FAISS
        vector_store = FAISS.from_documents(all_splits, embeddings)
        
        # Save vector store locally
        vector_store.save_local(VECTOR_STORE_DIR)
    
    # Create retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    return retriever

def load_vector_store(enabled_docs=None):
    """Load existing vector store, optionally filtering by enabled documents"""
    embeddings = get_mistral_embeddings()
    if not embeddings:
        return None
    
    if st.session_state.get("use_pinecone", False):
        # Check if Pinecone details are available
        if not all(key in st.session_state for key in ["pinecone_api_key", "pinecone_env", "pinecone_index"]):
            st.error("Pinecone settings not found")
            return None
        
        # Initialize Pinecone
        import pinecone
        
        pinecone.init(
            api_key=st.session_state.pinecone_api_key,
            environment=st.session_state.pinecone_env
        )
        
        # Load vector store
        vector_store = Pinecone.from_existing_index(
            st.session_state.pinecone_index,
            embeddings
        )
    else:
        # Check if local vector store exists
        if not os.path.exists(VECTOR_STORE_DIR):
            st.warning("No local vector store found")
            return None
        
        # Load FAISS vector store
        vector_store = FAISS.load_local(
            folder_path=VECTOR_STORE_DIR, 
            embeddings=embeddings,
            allow_dangerous_deserialization=True
            ) 
        
        # Filter by enabled documents if specified
        if enabled_docs is not None:
            # Create a new vector store with only enabled documents
            filtered_docs = []
            for doc in vector_store.docstore._dict.values():
                if doc.metadata.get("source") in enabled_docs:
                    filtered_docs.append(doc)
            
            if filtered_docs:
                vector_store = FAISS.from_documents(filtered_docs, embeddings)
            else:
                st.warning("No documents selected")
                return None
    
    # Create retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    return retriever