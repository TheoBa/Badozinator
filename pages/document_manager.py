import streamlit as st
import pandas as pd
from utils.documents import process_documents, get_document_status, delete_document
from utils.vector_store import initialize_vector_store
from utils.query_confluence import fetch_confluence_pages, process_directory

def show_document_manager():
    st.title("Document Manager")
    
    st.subheader("Fetch Confluence Pages")
    if st.button("Fetch Confluence Pages"):
        fetch_confluence_pages()
    if st.button("Process Confluence Pages"):
        process_directory(
            directory_path="./confluence_pages", 
            output_file="./data/confluence/pratt_confluence.json"
            )

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
        with st.form("Delete Documents"):
            st.write("Select documents to delete and click the button below")
            # Get selected documents
            selected_docs = st.multiselect(
                "Select documents to delete",
                doc_status["Original Name"].tolist()
            )
            btn = st.form_submit_button("Delete Selected Documents")
        if btn:
            # Find filename for each selected document
            file_names_to_delete = [filename for filename, metadata in st.session_state.document_metadata.items() if metadata["original_name"] in selected_docs]
            for filename in file_names_to_delete:
                delete_document(filename)
            
            # Reinitialize vector store
            with st.spinner("Reinitializing vector store..."):
                st.session_state.retriever = initialize_vector_store()
                st.success("Vector store reinitialized successfully")
    else:
        st.info("No documents have been processed yet")