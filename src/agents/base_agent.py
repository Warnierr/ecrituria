"""
Classe de base pour les agents spécialisés.
Phase 3 du plan d'évolution Ecrituria v2.0
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()


class AgentType(Enum):
    """Types d'agents disponibles."""
    RECHERCHEUR = "rechercheur"
    COHERENCE = "coherence"
    CREATIF = "creatif"
    EDITEUR = "editeur"
    ANALYSTE = "analyste"


class AgentState(TypedDict, total=False):
    """État partagé entre les agents dans un workflow."""
    # Entrée
    question: str
    project_name: str
    
    # Contexte récupéré
    documents: List[Document]
    graph_context: Dict[str, Any]
    
    # Analyse
    detected_entities: List[str]
    question_type: str  # factual, creative, analysis, coherence
    
    # Résultats intermédiaires
    search_results: Dict[str, Any]
    coherence_issues: List[Dict[str, Any]]
    creative_suggestions: List[str]
    
    # Sortie finale
    answer: str
    sources: List[str]
    confidence: float
    agent_chain: List[str]  # Agents qui ont participé


@dataclass
class AgentResponse:
    """Réponse d'un agent."""
    content: str
    agent_type: AgentType
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "agent": self.agent_type.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "sources": self.sources
        }


class BaseAgent(ABC):
    """
    Classe de base pour tous les agents.
    
    Chaque agent spécialisé hérite de cette classe et implémente
    sa logique spécifique dans la méthode process().
    """
    
    agent_type: AgentType = None
    description: str = "Agent de base"
    
    def __init__(
        self,
        project_name: str,
        model: str = "gpt-4o-mini",
        use_openrouter: bool = True,
        temperature: float = 0.7
    ):
        """
        Initialise l'agent.
        
        Args:
            project_name: Nom du projet
            model: Modèle LLM à utiliser
            use_openrouter: Utiliser OpenRouter
            temperature: Température de génération
        """
        self.project_name = project_name
        self.model = model
        self.temperature = temperature
        
        # Créer le LLM
        if use_openrouter:
            self.llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant RAG"
                }
            )
        else:
            self.llm = ChatOpenAI(model=model, temperature=temperature)
        
        # Composants optionnels (lazy loading)
        self._rag_engine = None
        self._graph_engine = None
    
    @property
    def rag_engine(self):
        """Lazy loading du moteur RAG."""
        if self._rag_engine is None:
            from src.rag import RAGEngine
            self._rag_engine = RAGEngine(
                self.project_name,
                model=self.model,
                use_hybrid_search=True,
                use_reranking=True
            )
        return self._rag_engine
    
    @property
    def graph_engine(self):
        """Lazy loading du moteur GraphRAG."""
        if self._graph_engine is None:
            from src.graph.graph_rag import GraphRAGEngine
            self._graph_engine = GraphRAGEngine(
                self.project_name,
                model=self.model
            )
        return self._graph_engine
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """
        Traite l'état et retourne l'état mis à jour.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        pass
    
    def should_run(self, state: AgentState) -> bool:
        """
        Détermine si cet agent doit s'exécuter.
        
        Args:
            state: État actuel
            
        Returns:
            True si l'agent doit s'exécuter
        """
        return True
    
    def invoke_llm(self, prompt: str) -> str:
        """
        Invoque le LLM avec un prompt.
        
        Args:
            prompt: Prompt à envoyer
            
        Returns:
            Réponse du LLM
        """
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    def retrieve_context(
        self,
        query: str,
        k: int = 5,
        use_graph: bool = True
    ) -> Dict[str, Any]:
        """
        Récupère le contexte pertinent pour une requête.
        
        Args:
            query: Requête de recherche
            k: Nombre de documents
            use_graph: Utiliser aussi le graphe
            
        Returns:
            Dict avec documents et contexte graphe
        """
        context = {
            "documents": [],
            "graph_context": {}
        }
        
        # Recherche vectorielle
        try:
            context["documents"] = self.rag_engine.retrieve(query, k=k)
        except Exception as e:
            print(f"⚠️ Erreur recherche vectorielle: {e}")
        
        # Contexte du graphe
        if use_graph:
            try:
                entity_ids = self.graph_engine.extract_question_entities(query)
                context["graph_context"] = self.graph_engine.get_graph_context(entity_ids)
            except Exception as e:
                print(f"⚠️ Erreur contexte graphe: {e}")
        
        return context
    
    def format_documents_context(self, documents: List[Document]) -> str:
        """Formate les documents en contexte textuel."""
        if not documents:
            return "Aucun document pertinent trouvé."
        
        parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('relative_path', f'doc_{i}')
            parts.append(f"[{i}. {source}]\n{doc.page_content}")
        
        return "\n\n---\n\n".join(parts)
    
    def classify_question(self, question: str) -> str:
        """
        Classifie le type de question.
        
        Args:
            question: Question à classifier
            
        Returns:
            Type: "factual", "creative", "analysis", "coherence"
        """
        prompt = f"""Classifie cette question dans une des catégories suivantes:
- factual: Question sur des faits de l'univers (qui, quoi, où, quand)
- creative: Demande de génération de contenu (scène, dialogue, idée)
- analysis: Demande d'analyse (structure, thèmes, arcs narratifs)
- coherence: Vérification de cohérence ou recherche d'incohérences

Question: {question}

Réponds avec UN SEUL mot (factual, creative, analysis, ou coherence):"""
        
        response = self.invoke_llm(prompt).lower().strip()
        
        # Valider la réponse
        valid_types = ["factual", "creative", "analysis", "coherence"]
        for t in valid_types:
            if t in response:
                return t
        
        return "factual"  # Défaut
    
    def __repr__(self):
        return f"<{self.__class__.__name__} project='{self.project_name}'>"


class DummyAgent(BaseAgent):
    """Agent de test qui ne fait rien."""
    
    agent_type = AgentType.RECHERCHEUR
    description = "Agent de test"
    
    def process(self, state: AgentState) -> AgentState:
        state["agent_chain"] = state.get("agent_chain", []) + [self.agent_type.value]
        return state


# Test du module
if __name__ == "__main__":
    print("\n🤖 Test de la classe BaseAgent")
    print("=" * 50)
    
    # Créer un agent de test
    agent = DummyAgent("anomalie2084")
    print(f"Agent créé: {agent}")
    
    # Tester la classification
    questions = [
        "Qui est Alex Chen?",
        "Écris une scène de combat entre Alex et Voss",
        "Analyse la structure narrative de la saison 1",
        "Y a-t-il des incohérences dans le worldbuilding?"
    ]
    
    print("\n📝 Classification des questions:")
    for q in questions:
        try:
            q_type = agent.classify_question(q)
            print(f"   [{q_type:10}] {q[:50]}...")
        except Exception as e:
            print(f"   [error] {q[:50]}... ({e})")
    
    print("\n✅ Test réussi!")

