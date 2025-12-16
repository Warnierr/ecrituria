"""
Module de reranking utilisant des Cross-Encoders.
Phase 1.2 du plan d'évolution Ecrituria v2.0

Les Cross-Encoders évaluent la pertinence réelle d'un document
par rapport à une requête, contrairement aux embeddings qui 
comparent des représentations pré-calculées.
"""
from typing import List, Tuple, Optional
from langchain_core.documents import Document
import os

# Lazy import pour éviter le chargement si non utilisé
_cross_encoder = None
_model_name = None


def get_cross_encoder(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
    """
    Charge le modèle Cross-Encoder (lazy loading).
    
    Modèles recommandés:
    - cross-encoder/ms-marco-MiniLM-L-6-v2: Rapide, bon pour le français
    - cross-encoder/ms-marco-MiniLM-L-12-v2: Plus précis, plus lent
    - cross-encoder/mmarco-mMiniLMv2-L12-H384-v1: Multilingue optimisé
    
    Args:
        model_name: Nom du modèle Hugging Face
        
    Returns:
        Instance CrossEncoder
    """
    global _cross_encoder, _model_name
    
    if _cross_encoder is None or _model_name != model_name:
        try:
            from sentence_transformers import CrossEncoder
            print(f"📦 Chargement du modèle de reranking: {model_name}")
            _cross_encoder = CrossEncoder(model_name)
            _model_name = model_name
        except ImportError:
            raise ImportError(
                "sentence-transformers n'est pas installé.\n"
                "Installez-le avec: pip install sentence-transformers"
            )
    
    return _cross_encoder


class Reranker:
    """
    Reranker utilisant un Cross-Encoder pour réordonner
    les documents par pertinence réelle.
    """
    
    # Modèles disponibles avec leurs caractéristiques
    MODELS = {
        "fast": {
            "name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "description": "Rapide (~40ms/doc), bonne qualité"
        },
        "accurate": {
            "name": "cross-encoder/ms-marco-MiniLM-L-12-v2",
            "description": "Plus précis (~80ms/doc)"
        },
        "multilingual": {
            "name": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
            "description": "Optimisé multilingue (français inclus)"
        }
    }
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        batch_size: int = 32
    ):
        """
        Initialise le reranker.
        
        Args:
            model_name: Nom du modèle ou alias ("fast", "accurate", "multilingual")
            batch_size: Taille des batches pour le scoring
        """
        # Résoudre les alias
        if model_name in self.MODELS:
            model_name = self.MODELS[model_name]["name"]
        
        self.model_name = model_name
        self.batch_size = batch_size
        self._encoder = None
    
    @property
    def encoder(self):
        """Lazy loading du modèle."""
        if self._encoder is None:
            self._encoder = get_cross_encoder(self.model_name)
        return self._encoder
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None,
        return_scores: bool = False
    ) -> List[Document] | List[Tuple[Document, float]]:
        """
        Réordonne les documents par pertinence.
        
        Args:
            query: Requête de recherche
            documents: Liste de documents à réordonner
            top_k: Nombre de documents à retourner (None = tous)
            return_scores: Retourner les scores avec les documents
            
        Returns:
            Documents réordonnés (avec scores optionnellement)
        """
        if not documents:
            return []
        
        # Préparer les paires query-document
        pairs = [(query, doc.page_content) for doc in documents]
        
        # Calculer les scores
        scores = self.encoder.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False
        )
        
        # Associer documents et scores
        doc_scores = list(zip(documents, scores))
        
        # Trier par score décroissant
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Limiter si demandé
        if top_k is not None:
            doc_scores = doc_scores[:top_k]
        
        if return_scores:
            return doc_scores
        else:
            return [doc for doc, _ in doc_scores]
    
    def score_document(self, query: str, document: Document) -> float:
        """
        Calcule le score de pertinence d'un document.
        
        Args:
            query: Requête
            document: Document à scorer
            
        Returns:
            Score de pertinence (plus élevé = plus pertinent)
        """
        return self.encoder.predict([(query, document.page_content)])[0]
    
    def score_documents(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Tuple[Document, float]]:
        """
        Calcule les scores pour plusieurs documents.
        
        Args:
            query: Requête
            documents: Liste de documents
            
        Returns:
            Liste de tuples (document, score)
        """
        return self.rerank(query, documents, return_scores=True)


def rerank_documents(
    query: str,
    documents: List[Document],
    top_k: Optional[int] = None,
    model: str = "fast"
) -> List[Document]:
    """
    Fonction utilitaire pour reranker des documents rapidement.
    
    Args:
        query: Requête de recherche
        documents: Documents à réordonner
        top_k: Nombre de résultats (None = tous)
        model: "fast", "accurate", ou "multilingual"
        
    Returns:
        Documents réordonnés
    """
    reranker = Reranker(model_name=model)
    return reranker.rerank(query, documents, top_k=top_k)


def rerank_with_scores(
    query: str,
    documents: List[Document],
    top_k: Optional[int] = None,
    model: str = "fast"
) -> List[Tuple[Document, float]]:
    """
    Rerank avec les scores de pertinence.
    
    Args:
        query: Requête de recherche
        documents: Documents à réordonner
        top_k: Nombre de résultats
        model: Type de modèle
        
    Returns:
        Liste de (document, score)
    """
    reranker = Reranker(model_name=model)
    return reranker.rerank(query, documents, top_k=top_k, return_scores=True)


# Test du module
if __name__ == "__main__":
    from langchain_core.documents import Document
    
    print("\n🔄 Test du module de reranking")
    print("=" * 50)
    
    # Documents de test
    test_docs = [
        Document(page_content="Alex Chen est un technicien de maintenance du Nexus.", metadata={"source": "alex.md"}),
        Document(page_content="Maya est une programmeuse talentueuse qui travaille dans la Zone Alpha.", metadata={"source": "maya.md"}),
        Document(page_content="Le Nexus est le cœur du réseau de données du Consortium.", metadata={"source": "monde.md"}),
        Document(page_content="Les Anomalies sont des individus aux capacités exceptionnelles.", metadata={"source": "monde.md"}),
        Document(page_content="Alex a découvert qu'il était une Anomalie capable de percevoir les flux de données.", metadata={"source": "alex.md"}),
    ]
    
    query = "Qui est Alex et quels sont ses pouvoirs?"
    
    print(f"\n📝 Requête: {query}")
    print(f"\n📚 Documents avant reranking:")
    for i, doc in enumerate(test_docs, 1):
        print(f"  {i}. {doc.page_content[:60]}...")
    
    try:
        reranker = Reranker(model_name="fast")
        results = reranker.rerank(query, test_docs, return_scores=True)
        
        print(f"\n✨ Documents après reranking:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. [Score: {score:.4f}] {doc.page_content[:60]}...")
        
        print("\n✅ Test réussi!")
        
    except ImportError as e:
        print(f"\n⚠️  {e}")
        print("   Le reranking nécessite sentence-transformers")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

