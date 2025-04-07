import streamlit as st
import os
from utils.document_store import DocumentStore
from utils.document_processor import process_pdf, process_docx, process_html, get_document_embeddings
from utils.rag_chat import RAGChat
from utils.query_confluence import fetch_confluence_pages, preprocess_confluence_html
from utils.embeddings import get_mistral_embeddings

# Set up page config
st.set_page_config(
    page_title="Knowledge Management System",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'document_store' not in st.session_state:
    st.session_state.document_store = DocumentStore()
if 'rag_chat' not in st.session_state:
    st.session_state.rag_chat = RAGChat(st.session_state.document_store)
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("Badozinator")

# Sidebar for document management
with st.sidebar:
    st.header("Document Management")
    
    # Manual file upload
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=['pdf', 'docx'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        with st.spinner("Processing uploaded files..."):
            for file in uploaded_files:
                # Save uploaded file temporarily
                temp_path = f"temp_{file.name}"
                with open(temp_path, "wb") as f:
                    f.write(file.getvalue())
                
                try:
                    # Process based on file type
                    if file.name.endswith('.pdf'):
                        doc, chunks = process_pdf(temp_path)
                        st.write(f"Processed PDF: {len(chunks)} chunks")
                    elif file.name.endswith('.docx'):
                        doc, chunks = process_docx(temp_path)
                        st.write(f"Processed DOCX: {len(chunks)} chunks")
                    
                    # Get embeddings for all chunks at once
                    embeddings = get_document_embeddings(chunks)
                    if embeddings:
                        st.write(f"Generated {len(embeddings)} embeddings")
                        st.session_state.document_store.save_document(doc, embeddings)
                        st.write(f"Saved document: {doc['title']}")
                    else:
                        st.error("Failed to generate embeddings")
                    
                    st.success(f"Processed {file.name}")
                except Exception as e:
                    st.error(f"Error processing {file.name}: {str(e)}")
                finally:
                    # Clean up temporary file
                    os.remove(temp_path)
    
    # Confluence integration
    if st.button("Load from Confluence"):
        with st.spinner("Fetching Confluence pages..."):
            fetch_confluence_pages()
            confluence_dir = "./confluence_pages"
            if os.path.exists(confluence_dir):
                for filename in os.listdir(confluence_dir):
                    if filename.endswith('.html'):
                        with open(os.path.join(confluence_dir, filename), 'r', encoding='utf-8') as f:
                            html_content = f.read()
                            title = filename.split('_')[-1].replace('.html', '')
                            file_id = filename.split('_')[0]
                            parent_id = filename.split('_')[1]
                            
                            # Process HTML content
                            doc, chunks = process_html(html_content, title, "confluence")
                            
                            # Get embeddings for all chunks at once
                            embeddings = get_document_embeddings(chunks)
                            if embeddings:
                                st.session_state.document_store.save_document(doc, embeddings)
    
    # Display stored documents
    st.header("Stored Documents")
    documents = st.session_state.document_store.get_all_documents()
    st.write(f"Total documents: {len(documents)}")
    for doc in documents:
        with st.expander(doc['title']):
            st.write(f"Source: {doc['source']}")
            st.write(f"Chunks: {len(doc['chunks'])}")
            st.write(f"Embeddings: {doc.get('embedding_count', 0)}")
            if st.button("Delete", key=f"delete_{doc['id']}"):
                st.session_state.document_store.delete_document(doc['id'])
                st.rerun()

# Main chat interface
st.header("Chat with your Knowledge Base")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "sources" in message:
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.write(f"- {source['title']}")

# Chat input
if prompt := st.chat_input("Ask a question about your documents"):
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        response = st.session_state.rag_chat.chat(prompt)
        
        if "error" in response:
            st.error(response["error"])
        else:
            st.write(response["response"])
            
            # Display sources
            if response["sources"]:
                with st.expander("Sources"):
                    for source in response["sources"]:
                        st.write(f"- {source['title']}")
            
            # Add assistant message to chat history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["response"],
                "sources": response["sources"]
            })
