import streamlit as st
import pandas as pd
from utils.documents import process_documents, get_document_status, delete_document, process_confluence_data
from utils.vector_store import initialize_vector_store
from utils.query_confluence import fetch_confluence_pages, process_directory
import os

def show_document_manager():
    st.title("Document Manager")
    
    # Add tabs for different document sources
    tab1, tab2 = st.tabs(["File Upload", "Confluence"])
    
    with tab1:
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
    
    with tab2:
        st.subheader("Fetch Confluence Pages")
        if st.button("Fetch Confluence Pages"):
            fetch_confluence_pages()
        if st.button("Process Pages and save to json"):
            process_directory(
                directory_path="./confluence_pages", 
                output_file="./data/confluence/pratt_confluence.json"
                )
        
        st.subheader("Process Confluence Data")
        if st.button("Process Confluence Data"):
            confluence_file = "./data/confluence/pratt_confluence.json"
            if os.path.exists(confluence_file):
                with st.spinner("Processing Confluence data..."):
                    all_splits = process_confluence_data(confluence_file)
                    if all_splits:
                        # Initialize vector store
                        st.session_state.retriever = initialize_vector_store()
                        st.success("Confluence data processed successfully!")
            else:
                st.error("Confluence data file not found")
    
    # Initialize document metadata if not exists
    if "document_metadata" not in st.session_state:
        st.session_state.document_metadata = {}
    
    # Document status section
    st.subheader("Document Status")
    doc_status = get_document_status()
    
    if doc_status is not None and not doc_status.empty:
        st.dataframe(doc_status)
            
        with st.expander("Document Management"):
            with st.form("Enable/Disable Documents"):
                use_all_docs = st.toggle("Use All Documents", value=False)
                enabled_docs = {}
                # Iterate over document metadata and create checkboxes for each on
                for doc_id, metadata in st.session_state.document_metadata.items():
                    enabled_docs[doc_id] = st.checkbox(
                        metadata["original_name"],
                        value=metadata.get("enabled", False),
                        key=f"doc_enable_{doc_id}"
                    )
                btn = st.form_submit_button("Save Changes")
            if btn:
                for doc_id, bool_to_embbed in enabled_docs.items():
                    if use_all_docs:
                        st.session_state.document_metadata[doc_id]["enabled"] = True
                    else:
                        st.session_state.document_metadata[doc_id]["enabled"] = bool_to_embbed

            
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