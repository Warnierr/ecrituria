"""
Module de recherche hybride combinant BM25 (lexical) et recherche vectorielle.
Phase 1.1 du plan d'évolution Ecrituria v2.0
"""
from typing import List, Optional, Tuple
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
try:
    from langchain.retrievers import EnsembleRetriever
except ImportError:
    try:
        from langchain.retrievers.ensemble import EnsembleRetriever
    except ImportError:
        from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from rank_bm25 import BM25Okapi
import os
from dotenv import load_dotenv

load_dotenv()


class HybridSearcher:
    """
    Recherche hybride combinant:
    - BM25: recherche lexicale (mots-clés exacts)
    - Vecteurs: recherche sémantique (sens similaire)
    
    Les deux approches se complètent:
    - BM25 trouve les correspondances exactes de termes
    - Les vecteurs trouvent les concepts similaires même avec des mots différents
    """
    
    def __init__(
        self,
        project_name: str,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        use_openrouter: bool = True
    ):
        """
        Initialise le rechercheur hybride.
        
        Args:
            project_name: Nom du projet (dossier dans data/)
            vector_weight: Poids de la recherche vectorielle (0-1)
            bm25_weight: Poids de la recherche BM25 (0-1)
            use_openrouter: Utiliser OpenRouter pour les embeddings
        """
        self.project_name = project_name
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.db_path = Path("db") / project_name
        
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"L'index pour le projet '{project_name}' n'existe pas.\n"
                f"Lancez d'abord: python -m src.indexer {project_name}"
            )
        
        # Configuration des embeddings
        if use_openrouter:
            self.embeddings = OpenAIEmbeddings(
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant RAG"
                }
            )
        else:
            self.embeddings = OpenAIEmbeddings()
        
        # Charger la base vectorielle
        self.vectordb = Chroma(
            embedding_function=self.embeddings,
            persist_directory=str(self.db_path),
            collection_name=project_name
        )
        
        # Récupérer tous les documents pour BM25
        self._documents: Optional[List[Document]] = None
        self._bm25_retriever: Optional[BM25Retriever] = None
        self._ensemble_retriever: Optional[EnsembleRetriever] = None
    
    def _load_documents_for_bm25(self) -> List[Document]:
        """Charge tous les documents de la base vectorielle pour BM25."""
        if self._documents is None:
            # Récupérer tous les documents de ChromaDB
            collection = self.vectordb._collection
            results = collection.get(include=["documents", "metadatas"])
            
            self._documents = []
            for i, (doc_text, metadata) in enumerate(zip(
                results.get("documents", []),
                results.get("metadatas", [])
            )):
                if doc_text:
                    self._documents.append(Document(
                        page_content=doc_text,
                        metadata=metadata or {}
                    ))
        
        return self._documents
    
    def _get_bm25_retriever(self, k: int = 5) -> BM25Retriever:
        """Crée ou récupère le retriever BM25."""
        docs = self._load_documents_for_bm25()
        
        if not docs:
            raise ValueError("Aucun document trouvé dans la base vectorielle")
        
        # Créer le retriever BM25
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = k
        
        return bm25_retriever
    
    def _get_vector_retriever(self, k: int = 5):
        """Crée le retriever vectoriel."""
        return self.vectordb.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
    
    def get_ensemble_retriever(self, k: int = 5) -> EnsembleRetriever:
        """
        Crée un retriever ensemble combinant BM25 et vecteurs.
        
        Args:
            k: Nombre de documents à récupérer par retriever
            
        Returns:
            EnsembleRetriever configuré
        """
        bm25_retriever = self._get_bm25_retriever(k)
        vector_retriever = self._get_vector_retriever(k)
        
        # Créer l'ensemble avec les poids configurés
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[self.bm25_weight, self.vector_weight]
        )
        
        return ensemble_retriever
    
    def search(
        self,
        query: str,
        k: int = 5,
        return_scores: bool = False
    ) -> List[Document]:
        """
        Effectue une recherche hybride.
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats à retourner
            return_scores: Retourner les scores (non supporté avec ensemble)
            
        Returns:
            Liste de documents triés par pertinence combinée
        """
        ensemble = self.get_ensemble_retriever(k)
        results = ensemble.invoke(query)
        
        # Limiter au nombre demandé (l'ensemble peut retourner plus)
        return results[:k]
    
    def search_vector_only(self, query: str, k: int = 5) -> List[Document]:
        """Recherche vectorielle pure (pour comparaison)."""
        return self.vectordb.similarity_search(query, k=k)
    
    def search_bm25_only(self, query: str, k: int = 5) -> List[Document]:
        """Recherche BM25 pure (pour comparaison)."""
        retriever = self._get_bm25_retriever(k)
        return retriever.invoke(query)
    
    def compare_methods(
        self,
        query: str,
        k: int = 5
    ) -> dict:
        """
        Compare les trois méthodes de recherche.
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats par méthode
            
        Returns:
            Dict avec les résultats de chaque méthode
        """
        return {
            "hybrid": self.search(query, k),
            "vector": self.search_vector_only(query, k),
            "bm25": self.search_bm25_only(query, k)
        }


def get_hybrid_retriever(
    project_name: str,
    k: int = 5,
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4
) -> EnsembleRetriever:
    """
    Fonction utilitaire pour obtenir rapidement un retriever hybride.
    
    Args:
        project_name: Nom du projet
        k: Nombre de résultats
        vector_weight: Poids recherche vectorielle
        bm25_weight: Poids recherche BM25
        
    Returns:
        EnsembleRetriever configuré
    """
    searcher = HybridSearcher(
        project_name,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight
    )
    return searcher.get_ensemble_retriever(k)


def hybrid_search(
    project_name: str,
    query: str,
    k: int = 5,
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4
) -> List[Document]:
    """
    Fonction utilitaire pour effectuer une recherche hybride rapidement.
    
    Args:
        project_name: Nom du projet
        query: Requête de recherche
        k: Nombre de résultats
        vector_weight: Poids recherche vectorielle
        bm25_weight: Poids recherche BM25
        
    Returns:
        Liste de documents pertinents
    """
    searcher = HybridSearcher(
        project_name,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight
    )
    return searcher.search(query, k)


# Test du module
if __name__ == "__main__":
    import sys
    
    project = sys.argv[1] if len(sys.argv) > 1 else "anomalie2084"
    query = sys.argv[2] if len(sys.argv) > 2 else "Qui est Alex Chen?"
    
    print(f"\n🔍 Test recherche hybride pour '{project}'")
    print(f"   Requête: {query}\n")
    
    try:
        searcher = HybridSearcher(project)
        
        print("=" * 60)
        print("📊 Comparaison des méthodes de recherche")
        print("=" * 60)
        
        results = searcher.compare_methods(query, k=3)
        
        for method, docs in results.items():
            print(f"\n{'🎯' if method == 'hybrid' else '📌'} {method.upper()}")
            print("-" * 40)
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get('relative_path', 'inconnu')
                preview = doc.page_content[:100].replace('\n', ' ')
                print(f"  {i}. [{source}]")
                print(f"     {preview}...")
        
        print("\n✅ Test réussi!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

