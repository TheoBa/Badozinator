import streamlit as st
import pandas as pd
from utils.documents import process_documents, get_document_status, delete_document
from utils.vector_store import initialize_vector_store

def show_document_manager():
    st.title("Document Manager")
    
    # Initialize document metadata if not exists
    if "document_metadata" not in st.session_state:
        st.session_state.document_metadata = {}
    
    # Upload section
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=["pdf", "txt", "docx", "doc"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("Process Documents"):
            with st.spinner("Processing documents..."):
                try:
                    # Process documents
                    all_splits = process_documents(uploaded_files)
                    st.success(f"Successfully processed {len(uploaded_files)} documents with {len(all_splits)} chunks")
                    
                    # Initialize vector store
                    with st.spinner("Initializing vector store..."):
                        st.session_state.retriever = initialize_vector_store()
                        st.success("Vector store initialized successfully")
                except Exception as e:
                    st.error(f"Error processing documents: {str(e)}")
    
    # Document status section
    st.subheader("Document Status")
    doc_status = get_document_status()
    
    if doc_status is not None and not doc_status.empty:
        st.dataframe(doc_status)
        
        # Delete document button
        if st.button("Delete Selected Documents"):
            # Get selected documents
            selected_docs = st.multiselect(
                "Select documents to delete",
                doc_status["Original Name"].tolist()
            )
            
            if selected_docs:
                # Find filename for each selected document
                for original_name in selected_docs:
                    for filename, metadata in st.session_state.document_metadata.items():
                        if metadata["original_name"] == original_name:
                            delete_document(filename)
                
                # Reinitialize vector store
                with st.spinner("Reinitializing vector store..."):
                    st.session_state.retriever = initialize_vector_store()
                    st.success("Vector store reinitialized successfully")
    else:
        st.info("No documents have been processed yet")