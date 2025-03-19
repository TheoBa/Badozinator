import streamlit as st
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_mistralai.chat_models import ChatMistralAI

def get_mistral_embeddings():
    """Get Mistral AI embeddings object with API key"""
    api_key = st.session_state.get("mistral_api_key", st.secrets.get("mistral_api_key", ""))
    
    if not api_key:
        st.error("Mistral API key not found")
        return None
    
    return MistralAIEmbeddings(
        model="mistral-embed",
        mistral_api_key=api_key
    )

def get_mistral_llm():
    """Get Mistral AI LLM object with API key"""
    api_key = st.session_state.get("mistral_api_key", st.secrets.get("mistral_api_key", ""))
    
    if not api_key:
        st.error("Mistral API key not found")
        return None
    
    return ChatMistralAI(
        model="mistral-large-2411",  # Use appropriate model name
        mistral_api_key=api_key
    )