"""
Agent Rechercheur: Trouve l'information dans les documents et le graphe.
Phase 3 du plan d'évolution Ecrituria v2.0
"""
from typing import Dict, Any, List
from langchain_core.documents import Document

from .base_agent import BaseAgent, AgentState, AgentType


RECHERCHEUR_PROMPT = """Tu es un assistant de recherche spécialisé dans l'univers de fiction de l'auteur.
Ta mission est de trouver et synthétiser les informations pertinentes.

CONTEXTE DU GRAPHE DE CONNAISSANCES:
{graph_context}

PASSAGES TEXTUELS PERTINENTS:
{text_context}

QUESTION: {question}

Instructions:
- Réponds de manière factuelle et précise
- Cite les sources quand c'est pertinent
- Si l'information n'est pas disponible, dis-le clairement
- Mets en évidence les connexions entre entités si pertinentes

Réponse:"""


class RechercheurAgent(BaseAgent):
    """
    Agent spécialisé dans la recherche d'informations.
    
    Combine recherche vectorielle et traversée du graphe pour
    trouver les informations les plus pertinentes.
    """
    
    agent_type = AgentType.RECHERCHEUR
    description = "Trouve l'information dans les documents et le graphe"
    
    def should_run(self, state: AgentState) -> bool:
        """
        S'exécute pour les questions factuelles ou comme première étape.
        """
        question_type = state.get("question_type", "factual")
        return question_type in ["factual", "analysis"] or not state.get("documents")
    
    def process(self, state: AgentState) -> AgentState:
        """
        Recherche et synthétise les informations.
        """
        question = state.get("question", "")
        
        # Récupérer le contexte si pas déjà fait
        if not state.get("documents"):
            context = self.retrieve_context(question, k=5, use_graph=True)
            state["documents"] = context["documents"]
            state["graph_context"] = context.get("graph_context", {})
        
        # Formater les contextes
        text_context = self.format_documents_context(state.get("documents", []))
        
        graph_ctx = state.get("graph_context", {})
        if hasattr(graph_ctx, 'text_context'):
            graph_context = graph_ctx.text_context
        elif isinstance(graph_ctx, dict) and "text_context" in graph_ctx:
            graph_context = graph_ctx["text_context"]
        else:
            graph_context = "Pas de contexte graphe disponible."
        
        # Générer la réponse
        prompt = RECHERCHEUR_PROMPT.format(
            graph_context=graph_context,
            text_context=text_context,
            question=question
        )
        
        answer = self.invoke_llm(prompt)
        
        # Mettre à jour l'état
        state["search_results"] = {
            "answer": answer,
            "num_documents": len(state.get("documents", [])),
            "has_graph_context": bool(graph_context != "Pas de contexte graphe disponible.")
        }
        
        # Si pas de réponse finale, utiliser celle-ci
        if not state.get("answer"):
            state["answer"] = answer
            state["sources"] = [
                doc.metadata.get("relative_path", "source inconnue")
                for doc in state.get("documents", [])
            ]
        
        # Enregistrer le passage de l'agent
        state["agent_chain"] = state.get("agent_chain", []) + [self.agent_type.value]
        
        return state
    
    def search_entity(self, entity_name: str) -> Dict[str, Any]:
        """
        Recherche spécifiquement une entité.
        
        Args:
            entity_name: Nom de l'entité à rechercher
            
        Returns:
            Informations sur l'entité
        """
        # Recherche vectorielle
        docs = self.rag_engine.retrieve(f"Qui est {entity_name}?", k=3)
        
        # Recherche dans le graphe
        from src.graph.entity_extractor import normalize_entity_id
        entity_id = normalize_entity_id(entity_name)
        
        node = self.graph_engine.graph_client.get_node(entity_id)
        relationships = self.graph_engine.graph_client.get_relationships(entity_id)
        
        return {
            "name": entity_name,
            "graph_node": node,
            "relationships": relationships,
            "documents": docs
        }
    
    def find_connections(
        self,
        entity1: str,
        entity2: str
    ) -> Dict[str, Any]:
        """
        Trouve les connexions entre deux entités.
        
        Args:
            entity1: Première entité
            entity2: Deuxième entité
            
        Returns:
            Informations sur les connexions
        """
        from src.graph.entity_extractor import normalize_entity_id
        
        id1 = normalize_entity_id(entity1)
        id2 = normalize_entity_id(entity2)
        
        # Chercher le chemin dans le graphe
        path = self.graph_engine.graph_client.find_path(id1, id2)
        
        # Recherche textuelle
        query = f"Quelle est la relation entre {entity1} et {entity2}?"
        docs = self.rag_engine.retrieve(query, k=3)
        
        return {
            "entity1": entity1,
            "entity2": entity2,
            "path": path,
            "documents": docs
        }


# Test du module
if __name__ == "__main__":
    print("\n🔍 Test de l'Agent Rechercheur")
    print("=" * 50)
    
    agent = RechercheurAgent("anomalie2084")
    
    # Créer un état de test
    state: AgentState = {
        "question": "Qui est Alex Chen et quels sont ses pouvoirs?",
        "project_name": "anomalie2084",
        "question_type": "factual"
    }
    
    print(f"\n📝 Question: {state['question']}")
    print(f"   Type: {state['question_type']}")
    print(f"   Should run: {agent.should_run(state)}")
    
    print("\n⏳ Traitement en cours...")
    
    try:
        result = agent.process(state)
        
        print(f"\n✨ Réponse:")
        print(result.get("answer", "Pas de réponse")[:500])
        
        print(f"\n📚 Sources: {len(result.get('sources', []))}")
        for source in result.get("sources", [])[:3]:
            print(f"   - {source}")
        
        print(f"\n🔗 Chain: {result.get('agent_chain', [])}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test terminé!")

