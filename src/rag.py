"""
Logique RAG (Retrieval-Augmented Generation) pour l'assistant fiction.
Version 2.0 avec recherche hybride et reranking.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


# Template de prompt personnalisé pour l'écriture de fiction
FICTION_PROMPT_TEMPLATE = """Tu es un assistant créatif spécialisé dans l'écriture de fiction.
Tu as accès à l'univers narratif de l'auteur via les passages suivants :

{context}

Question de l'auteur : {question}

Instructions :
- Réponds de manière créative et cohérente avec l'univers établi
- Utilise les informations des passages fournis pour maintenir la cohérence
- Si tu proposes du contenu créatif (scènes, dialogues), reste fidèle au ton et au style
- Si les passages ne contiennent pas assez d'information, dis-le clairement

Réponse :"""


# Prompt alternatif pour les questions factuelles
FACTUAL_PROMPT_TEMPLATE = """Tu es un assistant d'écriture qui connaît parfaitement cet univers de fiction.
Voici les informations pertinentes de la base de connaissances :

{context}

Question : {question}

Réponds de façon précise et concise en te basant uniquement sur les informations fournies.
Si l'information n'est pas disponible, indique-le clairement.

Réponse :"""


class RAGEngine:
    """
    Moteur RAG avancé avec:
    - Recherche hybride (BM25 + vecteurs)
    - Reranking par cross-encoder
    - Support multi-provider (OpenRouter, OpenAI, Ollama)
    """
    
    def __init__(
        self,
        project_name: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        use_openrouter: bool = True,
        use_hybrid_search: bool = True,
        use_reranking: bool = True,
        rerank_model: str = "fast"
    ):
        """
        Initialise le moteur RAG.
        
        Args:
            project_name: Nom du projet
            model: Modèle LLM à utiliser
            temperature: Température de génération
            use_openrouter: Utiliser OpenRouter comme provider
            use_hybrid_search: Activer la recherche hybride BM25+vecteurs
            use_reranking: Activer le reranking par cross-encoder
            rerank_model: Modèle de reranking ("fast", "accurate", "multilingual")
        """
        self.project_name = project_name
        self.model = model
        self.temperature = temperature
        self.use_openrouter = use_openrouter
        self.use_hybrid_search = use_hybrid_search
        self.use_reranking = use_reranking
        self.rerank_model = rerank_model
        
        self.db_path = Path("db") / project_name
        
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"L'index pour le projet '{project_name}' n'existe pas.\n"
                f"Lancez d'abord: python -m src.indexer {project_name}"
            )
        
        # Configuration des embeddings
        self.embeddings = self._create_embeddings()
        
        # Charger la base vectorielle
        self.vectordb = Chroma(
            embedding_function=self.embeddings,
            persist_directory=str(self.db_path),
            collection_name=project_name
        )
        
        # Créer le LLM
        self.llm = self._create_llm()
        
        # Composants optionnels (lazy loading)
        self._hybrid_searcher = None
        self._reranker = None
    
    def _create_embeddings(self):
        """Crée le client d'embeddings selon la configuration."""
        if self.use_openrouter:
            return OpenAIEmbeddings(
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant RAG"
                }
            )
        else:
            return OpenAIEmbeddings()
    
    def _create_llm(self):
        """Crée le client LLM selon la configuration."""
        if self.use_openrouter:
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant RAG"
                }
            )
        else:
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature
            )
    
    @property
    def hybrid_searcher(self):
        """Lazy loading du rechercheur hybride."""
        if self._hybrid_searcher is None and self.use_hybrid_search:
            try:
                from src.hybrid_search import HybridSearcher
                self._hybrid_searcher = HybridSearcher(
                    self.project_name,
                    use_openrouter=self.use_openrouter
                )
            except ImportError as e:
                print(f"⚠️ Recherche hybride non disponible: {e}")
                self.use_hybrid_search = False
        return self._hybrid_searcher
    
    @property
    def reranker(self):
        """Lazy loading du reranker."""
        if self._reranker is None and self.use_reranking:
            try:
                from src.reranker import Reranker
                self._reranker = Reranker(model_name=self.rerank_model)
            except ImportError as e:
                print(f"⚠️ Reranking non disponible: {e}")
                self.use_reranking = False
        return self._reranker
    
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """
        Récupère les documents pertinents.
        
        Utilise la recherche hybride et le reranking si configurés.
        
        Args:
            query: Requête de recherche
            k: Nombre de documents à retourner
            
        Returns:
            Liste de documents triés par pertinence
        """
        # Récupérer plus de documents si on fait du reranking
        retrieve_k = k * 3 if self.use_reranking else k
        
        # Recherche hybride ou vectorielle simple
        if self.use_hybrid_search and self.hybrid_searcher:
            docs = self.hybrid_searcher.search(query, k=retrieve_k)
        else:
            docs = self.vectordb.similarity_search(query, k=retrieve_k)
        
        # Reranking
        if self.use_reranking and self.reranker and docs:
            docs = self.reranker.rerank(query, docs, top_k=k)
        else:
            docs = docs[:k]
        
        return docs
    
    def ask(
        self,
        question: str,
        k: int = 5,
        prompt_template: str = None,
        show_sources: bool = False
    ) -> Dict[str, Any] | str:
        """
        Pose une question et génère une réponse.
        
        Args:
            question: Question à poser
            k: Nombre de documents de contexte
            prompt_template: Template personnalisé (défaut: FICTION_PROMPT_TEMPLATE)
            show_sources: Retourner les sources avec la réponse
            
        Returns:
            Réponse (str) ou dict avec answer et sources
        """
        # Récupérer le contexte
        docs = self.retrieve(question, k=k)
        
        # Construire le contexte
        context = "\n\n---\n\n".join([
            f"[Source: {doc.metadata.get('relative_path', 'inconnu')}]\n{doc.page_content}"
            for doc in docs
        ])
        
        # Sélectionner le template
        if prompt_template is None:
            prompt_template = FICTION_PROMPT_TEMPLATE
        
        # Construire le prompt
        full_prompt = prompt_template.format(context=context, question=question)
        
        # Générer la réponse
        response = self.llm.invoke(full_prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        if show_sources:
            return {
                "answer": answer,
                "sources": docs
            }
        
        return answer
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Recherche simple sans génération.
        
        Args:
            query: Requête de recherche
            k: Nombre de résultats
            
        Returns:
            Documents pertinents
        """
        return self.retrieve(query, k=k)


# ============================================
# Fonctions de compatibilité avec l'API existante
# ============================================

def get_rag_chain(
    project_name: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    k: int = 5
):
    """
    Crée une chaîne RAG pour un projet donné.
    (Fonction de compatibilité avec l'ancienne API)
    """
    engine = RAGEngine(project_name, model=model, temperature=temperature)
    return engine.llm, engine.vectordb.as_retriever(search_kwargs={"k": k})


def ask(
    project_name: str,
    question: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    k: int = 5,
    show_sources: bool = False,
    use_hybrid: bool = True,
    use_reranking: bool = True
) -> Dict[str, Any] | str:
    """
    Pose une question sur un projet de fiction.
    
    Args:
        project_name: Nom du projet
        question: Question à poser
        model: Modèle à utiliser
        temperature: Température de génération
        k: Nombre de passages à récupérer
        show_sources: Afficher les sources utilisées
        use_hybrid: Utiliser la recherche hybride
        use_reranking: Utiliser le reranking
        
    Returns:
        Réponse du LLM (et sources si demandé)
    """
    engine = RAGEngine(
        project_name,
        model=model,
        temperature=temperature,
        use_hybrid_search=use_hybrid,
        use_reranking=use_reranking
    )
    
    return engine.ask(question, k=k, show_sources=show_sources)


def get_relevant_passages(
    project_name: str,
    query: str,
    k: int = 5,
    use_hybrid: bool = True,
    use_reranking: bool = True
) -> List[Document]:
    """
    Récupère les passages les plus pertinents sans générer de réponse.
    
    Args:
        project_name: Nom du projet
        query: Requête de recherche
        k: Nombre de passages à récupérer
        use_hybrid: Utiliser la recherche hybride
        use_reranking: Utiliser le reranking
        
    Returns:
        Liste de documents pertinents
    """
    engine = RAGEngine(
        project_name,
        use_hybrid_search=use_hybrid,
        use_reranking=use_reranking
    )
    
    return engine.search(query, k=k)


# ============================================
# Fonctions utilitaires avancées
# ============================================

def compare_search_methods(
    project_name: str,
    query: str,
    k: int = 5
) -> Dict[str, List[Document]]:
    """
    Compare les différentes méthodes de recherche.
    
    Returns:
        Dict avec les résultats de chaque méthode
    """
    results = {}
    
    # Recherche vectorielle simple
    engine_vector = RAGEngine(
        project_name,
        use_hybrid_search=False,
        use_reranking=False
    )
    results["vector_only"] = engine_vector.search(query, k=k)
    
    # Recherche hybride sans reranking
    try:
        engine_hybrid = RAGEngine(
            project_name,
            use_hybrid_search=True,
            use_reranking=False
        )
        results["hybrid_no_rerank"] = engine_hybrid.search(query, k=k)
    except Exception:
        results["hybrid_no_rerank"] = []
    
    # Recherche complète (hybride + reranking)
    try:
        engine_full = RAGEngine(
            project_name,
            use_hybrid_search=True,
            use_reranking=True
        )
        results["full"] = engine_full.search(query, k=k)
    except Exception:
        results["full"] = []
    
    return results


# Test du module
if __name__ == "__main__":
    import sys
    
    project = sys.argv[1] if len(sys.argv) > 1 else "anomalie2084"
    question = sys.argv[2] if len(sys.argv) > 2 else "Qui est Alex Chen?"
    
    print(f"\n🔍 Test RAG v2.0 pour '{project}'")
    print(f"   Question: {question}")
    print("=" * 60)
    
    try:
        # Test avec toutes les fonctionnalités
        print("\n🚀 Test avec recherche hybride + reranking...")
        result = ask(project, question, show_sources=True)
        
        print(f"\n✨ Réponse:")
        print(result["answer"])
        
        print(f"\n📚 Sources utilisées:")
        for i, doc in enumerate(result["sources"], 1):
            source = doc.metadata.get('relative_path', 'inconnu')
            print(f"   {i}. {source}")
        
        print("\n✅ Test réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
