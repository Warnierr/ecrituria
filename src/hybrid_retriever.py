"""
Hybrid Retrieval: BM25 + Vector Similarity
Combine lexical (exact match) and semantic (meaning) search for better retrieval
"""
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from chromadb import Collection
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Result from hybrid retrieval"""
    content: str
    source: str
    score: float
    method: str  # 'bm25', 'vector', or 'hybrid'
    metadata: Dict[str, Any]


class HybridRetriever:
    """
    Combines BM25 (keyword) and vector similarity for optimal retrieval
    
    BM25 captures exact term matches ("Alex Chen" will match exactly)
    Vector captures semantic similarity ("protagonist" might match "main character")
    """
    
    def __init__(
        self, 
        chroma_collection: Collection,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5
    ):
        """
        Args:
            chroma_collection: ChromaDB collection with embedded documents
            bm25_weight: Weight for BM25 scores (0-1)
            vector_weight: Weight for vector scores (0-1)
        """
        self.collection = chroma_collection
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        
        # Build BM25 index from collection
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 index from ChromaDB documents"""
        print("🔧 Building BM25 index...")
        
        # Get all documents from ChromaDB
        results = self.collection.get(include=['documents', 'metadatas'])
        
        if not results['documents']:
            print("⚠️  No documents found in collection")
            self.bm25 = None
            self.doc_ids = []
            self.documents = []
            self.metadatas = []
            return
        
        self.documents = results['documents']
        self.metadatas = results['metadatas']
        self.doc_ids = results['ids']
        
        # Tokenize documents for BM25
        tokenized_corpus = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        print(f"✅ BM25 index built with {len(self.documents)} documents")
    
    def retrieve(
        self, 
        query: str, 
        k: int = 5,
        min_score: float = 0.0
    ) -> List[RetrievalResult]:
        """
        Retrieve top-k most relevant documents using hybrid search
        
        Args:
            query: Search query
            k: Number of results to return
            min_score: Minimum score threshold
            
        Returns:
            List of RetrievalResult sorted by score
        """
        if not self.bm25:
            # Fallback to vector-only if BM25 not available
            return self._vector_only_retrieve(query, k, min_score)
        
        # 1. BM25 retrieval
        bm25_scores = self._bm25_retrieve(query, k * 2)  # Get more candidates
        
        # 2. Vector retrieval
        vector_scores = self._vector_retrieve(query, k * 2)
        
        # 3. Combine scores
        hybrid_scores = self._combine_scores(bm25_scores, vector_scores)
        
        # 4. Filter and sort
        results = []
        for doc_id, score in hybrid_scores.items():
            if score >= min_score:
                idx = self.doc_ids.index(doc_id)
                results.append(RetrievalResult(
                    content=self.documents[idx],
                    source=self.metadatas[idx].get('source', 'unknown'),
                    score=score,
                    method='hybrid',
                    metadata=self.metadatas[idx]
                ))
        
        # Sort by score and return top-k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
    
    def _bm25_retrieve(self, query: str, k: int) -> Dict[str, float]:
        """Retrieve using BM25"""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:k]
        
        # Normalize scores to 0-1
        max_score = scores[top_indices[0]] if len(top_indices) > 0 and scores[top_indices[0]] > 0 else 1.0
        
        return {
            self.doc_ids[idx]: scores[idx] / max_score
            for idx in top_indices
            if scores[idx] > 0
        }
    
    def _vector_retrieve(self, query: str, k: int) -> Dict[str, float]:
        """Retrieve using vector similarity"""
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=['distances']
        )
        
        if not results['ids'] or not results['ids'][0]:
            return {}
        
        # ChromaDB returns distances (lower is better), convert to similarity scores
        # Using cosine distance: similarity = 1 - distance
        return {
            doc_id: 1 - distance
            for doc_id, distance in zip(results['ids'][0], results['distances'][0])
        }
    
    def _combine_scores(
        self, 
        bm25_scores: Dict[str, float], 
        vector_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Combine BM25 and vector scores with weights"""
        all_doc_ids = set(bm25_scores.keys()) | set(vector_scores.keys())
        
        combined = {}
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0.0)
            vector_score = vector_scores.get(doc_id, 0.0)
            
            # Weighted combination
            combined[doc_id] = (
                self.bm25_weight * bm25_score + 
                self.vector_weight * vector_score
            )
        
        return combined
    
    def _vector_only_retrieve(
        self, 
        query: str, 
        k: int,
        min_score: float
    ) -> List[RetrievalResult]:
        """Fallback to vector-only retrieval"""
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )
        
        if not results['ids'] or not results['ids'][0]:
            return []
        
        return [
            RetrievalResult(
                content=doc,
                source=meta.get('source', 'unknown'),
                score=1 - distance,  # Convert distance to similarity
                method='vector',
                metadata=meta
            )
            for doc, meta, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
            if (1 - distance) >= min_score
        ]
    
    def reindex(self):
        """Rebuild BM25 index (call after adding documents)"""
        self._build_bm25_index()


# Example usage
if __name__ == "__main__":
    import chromadb
    
    # Example with ChromaDB
    client = chromadb.PersistentClient(path="./test_db")
    collection = client.get_or_create_collection("test")
    
    # Add sample documents
    collection.add(
        documents=[
            "Alex Chen est le protagoniste de l'histoire",
            "Le Baron des Cendres règne sur les ruines",
            "Maya travaille dans la résistance clandestine"
        ],
        ids=["doc1", "doc2", "doc3"],
        metadatas=[
            {"source": "personnages/alex.md"},
            {"source": "personnages/baron.md"},
            {"source": "personnages/maya.md"}
        ]
    )
    
    # Create hybrid retriever
    retriever = HybridRetriever(collection)
    
    # Search
    results = retriever.retrieve("qui est le personnage principal?", k=2)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.3f} ({result.method})")
        print(f"   Source: {result.source}")
        print(f"   Content: {result.content[:100]}...")
