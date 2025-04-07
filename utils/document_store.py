import os
import json
from datetime import datetime
import faiss
import numpy as np
from typing import List, Dict, Any
import pickle

class DocumentStore:
    def __init__(self, store_dir: str = "document_store"):
        self.store_dir = store_dir
        self.documents_file = os.path.join(store_dir, "documents.json")
        self.embeddings_file = os.path.join(store_dir, "embeddings.pkl")
        self._ensure_store_exists()
        self.documents = self._load_documents()
        self.embeddings_index = self._load_embeddings()

    def _ensure_store_exists(self):
        """Create store directory if it doesn't exist"""
        os.makedirs(self.store_dir, exist_ok=True)

    def _load_documents(self) -> List[Dict[str, Any]]:
        """Load documents from JSON file"""
        if os.path.exists(self.documents_file):
            with open(self.documents_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _load_embeddings(self) -> faiss.Index:
        """Load FAISS index from pickle file"""
        if os.path.exists(self.embeddings_file):
            with open(self.embeddings_file, 'rb') as f:
                return pickle.load(f)
        return faiss.IndexFlatL2(1024)  # Assuming 1024-dimensional embeddings

    def save_document(self, document: Dict[str, Any], embeddings: List[np.ndarray]):
        """Save a document and its chunk embeddings"""
        # Add metadata
        document['added_at'] = datetime.now().isoformat()
        document['id'] = len(self.documents)
        document['embedding_count'] = len(embeddings)  # Store number of embeddings
        
        # Save document
        self.documents.append(document)
        with open(self.documents_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        # Save embeddings for all chunks at once
        if embeddings:
            self.embeddings_index.add(np.array(embeddings, dtype=np.float32))
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings_index, f)

    def get_document(self, doc_id: int) -> Dict[str, Any]:
        """Retrieve a document by ID"""
        return self.documents[doc_id]

    def _get_document_index_range(self, doc_id: int) -> tuple[int, int]:
        """Get the start and end indices in the FAISS index for a document"""
        start_idx = 0
        for doc in self.documents:
            if doc['id'] == doc_id:
                return start_idx, start_idx + doc['embedding_count']
            start_idx += doc['embedding_count']
        return 0, 0

    def search_similar(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks and return their parent documents"""
        distances, indices = self.embeddings_index.search(
            np.array([query_embedding], dtype=np.float32), k
        )
        
        # Get unique document IDs from the chunks
        doc_ids = set()
        for idx in indices[0]:
            # Find which document this embedding belongs to
            current_idx = 0
            for doc in self.documents:
                if current_idx <= idx < current_idx + doc['embedding_count']:
                    doc_ids.add(doc['id'])
                    break
                current_idx += doc['embedding_count']
        
        # Return unique documents
        return [self.documents[doc_id] for doc_id in doc_ids]

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents"""
        return self.documents

    def delete_document(self, doc_id: int):
        """Delete a document and its embeddings"""
        if 0 <= doc_id < len(self.documents):
            # Get the document's embedding range
            start_idx, end_idx = self._get_document_index_range(doc_id)
            
            # Remove document
            self.documents.pop(doc_id)
            
            # Create new FAISS index
            self.embeddings_index = faiss.IndexFlatL2(1024)
            
            # Re-add embeddings for remaining documents
            for doc in self.documents:
                if 'embedding_count' in doc:
                    # Get embeddings for this document
                    doc_start, doc_end = self._get_document_index_range(doc['id'])
                    if doc_end > doc_start:
                        embeddings = self.embeddings_index.reconstruct_n(doc_start, doc_end - doc_start)
                        self.embeddings_index.add(embeddings)
            
            # Save updated state
            with open(self.documents_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(self.embeddings_index, f) 