import streamlit as st
import os
from utils.vector_store import initialize_vector_store

# Set up page config
st.set_page_config(
    page_title="Knowledge Management System",
    page_icon="📚",
    layout="wide"
)

# Initialize directories
os.makedirs("./data/documents", exist_ok=True)
os.makedirs("./data/vector_store", exist_ok=True)

# Sidebar for navigation
st.sidebar.title("Knowledge Management System")
page = st.sidebar.radio("Navigation", ["Q&A Interface", "Document Manager"])

# Check for API key
if "mistral_api_key" not in st.secrets:
    st.sidebar.warning("Mistral API key not found in secrets")
    api_key = st.sidebar.text_input("Mistral API Key", type="password")
    if api_key:
        st.session_state.mistral_api_key = api_key
else:
    st.session_state.mistral_api_key = st.secrets.mistral_api_key

# Vector store settings
use_pinecone = st.sidebar.toggle("Use Pinecone Vector DB", False)
st.session_state.use_pinecone = use_pinecone

if use_pinecone:
    if "pinecone_api_key" not in st.secrets or "pinecone_env" not in st.secrets or "pinecone_index" not in st.secrets:
        st.sidebar.warning("Pinecone settings not found in secrets")
        pinecone_api_key = st.sidebar.text_input("Pinecone API Key", type="password")
        pinecone_env = st.sidebar.text_input("Pinecone Environment")
        pinecone_index = st.sidebar.text_input("Pinecone Index Name")
        
        if pinecone_api_key and pinecone_env and pinecone_index:
            st.session_state.pinecone_api_key = pinecone_api_key
            st.session_state.pinecone_env = pinecone_env
            st.session_state.pinecone_index = pinecone_index
    else:
        st.session_state.pinecone_api_key = st.secrets.pinecone_api_key
        st.session_state.pinecone_env = st.secrets.pinecone_env
        st.session_state.pinecone_index = st.secrets.pinecone_index

# Initialize vector store if needed
# if "retriever" not in st.session_state and "documents_processed" in st.session_state and st.session_state.documents_processed:
#     with st.spinner("Initializing vector store..."):
#         st.session_state.retriever = initialize_vector_store()

# Load the appropriate page
if page == "Q&A Interface":
    from pages.qa_interface import show_qa_interface
    show_qa_interface()
else:
    from pages.document_manager import show_document_manager
    show_document_manager()