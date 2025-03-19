import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from utils.embeddings import get_mistral_llm
from utils.vector_store import load_vector_store

def show_qa_interface():
    st.title("Knowledge Base Q&A")
    
    # Check if documents have been processed
    if "documents_processed" not in st.session_state or not st.session_state.documents_processed:
        st.info("Please process documents in the Document Manager first")
        return
    
    # Get retriever
    retriever = st.session_state.get("retriever")
    if not retriever:
        retriever = load_vector_store()
        if not retriever:
            st.error("Failed to load vector store")
            return
        st.session_state.retriever = retriever
    
    # Get LLM
    llm = get_mistral_llm()
    if not llm:
        st.error("Failed to initialize Mistral LLM")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        st.chat_message(message["role"]).write(message["content"])
    
    # User input
    if query := st.chat_input("Ask a question about your documents"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        st.chat_message("user").write(query)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_template("""
        Answer the following question based only on the provided context:
        
        <context>
        {context}
        </context>
        
        Question: {input}
        
        If the answer is not in the context, say "I don't have enough information to answer this question."
        """)
        
        # Create chain
        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        # Get response
        with st.spinner("Thinking..."):
            result = retrieval_chain.invoke({"input": query})
            response = result["answer"]
            
            # Get source documents
            source_docs = []
            if "context" in result and hasattr(result["context"], "get_content"):
                source_docs = result["context"].get_content()
            
            # Add assistant message to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Display response
            with st.chat_message("assistant"):
                st.write(response)
                
                # Display sources if available
                if source_docs:
                    with st.expander("Sources"):
                        sources = set()
                        for doc in source_docs:
                            if hasattr(doc, "metadata") and "original_name" in doc.metadata:
                                sources.add(doc.metadata["original_name"])
                        
                        if sources:
                            st.write(", ".join(sources))