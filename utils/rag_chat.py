from typing import List, Dict, Any
import numpy as np
from .embeddings import get_mistral_llm, get_mistral_embeddings
from .document_store import DocumentStore

class RAGChat:
    def __init__(self, document_store: DocumentStore):
        self.document_store = document_store
        self.llm = get_mistral_llm()
        self.embeddings = get_mistral_embeddings()

    def _get_relevant_chunks(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Get relevant document chunks for a query"""
        query_embedding = self.embeddings.embed_query(query)
        relevant_docs = self.document_store.search_similar(query_embedding, k)
        
        # Get chunks from relevant documents
        chunks = []
        for doc in relevant_docs:
            for chunk in doc['chunks']:
                chunks.append({
                    'content': chunk,
                    'source': doc['title'],
                    'doc_id': doc['id']
                })
        return chunks

    def _create_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Create a prompt for the LLM"""
        context = "\n\n".join([f"From {chunk['source']}:\n{chunk['content']}" for chunk in chunks])
        
        prompt = f"""You are a helpful AI assistant. Use the following context to answer the question. 
If the context is insufficient to provide a complete answer, say so and provide the best answer you can based on the available information.

Context:
{context}

Question: {query}

Answer:"""
        return prompt

    def chat(self, query: str) -> Dict[str, Any]:
        """Process a chat query and return response with sources"""
        if not self.llm or not self.embeddings:
            return {
                "error": "LLM or embeddings not initialized",
                "response": None,
                "sources": []
            }

        # Get relevant chunks
        chunks = self._get_relevant_chunks(query)
        
        # Create and send prompt
        prompt = self._create_prompt(query, chunks)
        response = self.llm.invoke(prompt)
        
        # Format sources
        sources = [{
            "title": chunk['source'],
            "doc_id": chunk['doc_id']
        } for chunk in chunks]
        
        return {
            "response": response.content,
            "sources": sources
        } 