"""
Orchestrateur d'agents utilisant LangGraph.
Phase 3 du plan d'évolution Ecrituria v2.0

Coordonne les différents agents spécialisés pour répondre
aux requêtes de façon optimale.
"""
from typing import Dict, Any, List, Optional, Literal
from enum import Enum

from .base_agent import AgentState, AgentType
from .rechercheur import RechercheurAgent
from .coherence import CoherenceAgent
from .creatif import CreatifAgent


class WorkflowType(Enum):
    """Types de workflows prédéfinis."""
    SIMPLE = "simple"  # Un seul agent
    RESEARCH_THEN_CREATE = "research_then_create"  # Recherche puis création
    FULL_ANALYSIS = "full_analysis"  # Tous les agents pertinents
    COHERENCE_CHECK = "coherence_check"  # Vérification de cohérence


class AgentOrchestrator:
    """
    Orchestrateur qui coordonne les agents spécialisés.
    
    Détermine automatiquement:
    - Quels agents doivent s'exécuter
    - Dans quel ordre
    - Comment combiner leurs résultats
    """
    
    def __init__(
        self,
        project_name: str,
        model: str = "gpt-4o-mini",
        use_openrouter: bool = True
    ):
        """
        Initialise l'orchestrateur.
        
        Args:
            project_name: Nom du projet
            model: Modèle LLM à utiliser
            use_openrouter: Utiliser OpenRouter
        """
        self.project_name = project_name
        self.model = model
        self.use_openrouter = use_openrouter
        
        # Initialiser les agents
        self.agents = {
            AgentType.RECHERCHEUR: RechercheurAgent(
                project_name, model=model, use_openrouter=use_openrouter
            ),
            AgentType.COHERENCE: CoherenceAgent(
                project_name, model=model, use_openrouter=use_openrouter
            ),
            AgentType.CREATIF: CreatifAgent(
                project_name, model=model, use_openrouter=use_openrouter
            ),
        }
    
    def classify_request(self, question: str) -> Dict[str, Any]:
        """
        Classifie une requête pour déterminer le workflow optimal.
        
        Args:
            question: Question de l'utilisateur
            
        Returns:
            Dict avec le type de question et le workflow recommandé
        """
        question_lower = question.lower()
        
        # Mots-clés par type
        creative_keywords = [
            "écris", "crée", "génère", "imagine", "propose",
            "scène", "dialogue", "description", "continue"
        ]
        coherence_keywords = [
            "cohérent", "incohérence", "erreur", "contradiction",
            "vérifier", "possible", "logique"
        ]
        analysis_keywords = [
            "analyse", "structure", "thème", "arc",
            "résume", "synthèse", "compare"
        ]
        
        # Déterminer le type
        if any(kw in question_lower for kw in coherence_keywords):
            question_type = "coherence"
            workflow = WorkflowType.COHERENCE_CHECK
        elif any(kw in question_lower for kw in creative_keywords):
            question_type = "creative"
            workflow = WorkflowType.RESEARCH_THEN_CREATE
        elif any(kw in question_lower for kw in analysis_keywords):
            question_type = "analysis"
            workflow = WorkflowType.FULL_ANALYSIS
        else:
            question_type = "factual"
            workflow = WorkflowType.SIMPLE
        
        return {
            "question_type": question_type,
            "workflow": workflow,
            "question": question
        }
    
    def get_workflow_agents(self, workflow: WorkflowType) -> List[AgentType]:
        """
        Retourne la liste ordonnée des agents pour un workflow.
        
        Args:
            workflow: Type de workflow
            
        Returns:
            Liste des types d'agents à exécuter
        """
        workflows = {
            WorkflowType.SIMPLE: [AgentType.RECHERCHEUR],
            WorkflowType.RESEARCH_THEN_CREATE: [
                AgentType.RECHERCHEUR,
                AgentType.CREATIF
            ],
            WorkflowType.FULL_ANALYSIS: [
                AgentType.RECHERCHEUR,
                AgentType.COHERENCE
            ],
            WorkflowType.COHERENCE_CHECK: [
                AgentType.RECHERCHEUR,
                AgentType.COHERENCE
            ]
        }
        
        return workflows.get(workflow, [AgentType.RECHERCHEUR])
    
    def run(
        self,
        question: str,
        workflow: WorkflowType = None,
        show_chain: bool = False
    ) -> Dict[str, Any]:
        """
        Exécute le workflow complet pour répondre à une question.
        
        Args:
            question: Question de l'utilisateur
            workflow: Type de workflow (auto-détecté si None)
            show_chain: Afficher les agents exécutés
            
        Returns:
            Dict avec la réponse et métadonnées
        """
        # Classifier la requête
        classification = self.classify_request(question)
        
        if workflow is None:
            workflow = classification["workflow"]
        
        # Initialiser l'état
        state: AgentState = {
            "question": question,
            "project_name": self.project_name,
            "question_type": classification["question_type"],
            "documents": [],
            "graph_context": {},
            "agent_chain": []
        }
        
        # Obtenir la liste des agents
        agent_types = self.get_workflow_agents(workflow)
        
        if show_chain:
            print(f"\n🔄 Workflow: {workflow.value}")
            print(f"   Agents: {[a.value for a in agent_types]}")
        
        # Exécuter les agents en séquence
        for agent_type in agent_types:
            agent = self.agents.get(agent_type)
            
            if agent and agent.should_run(state):
                if show_chain:
                    print(f"   ▶ Exécution: {agent_type.value}...")
                
                try:
                    state = agent.process(state)
                except Exception as e:
                    print(f"   ⚠️ Erreur {agent_type.value}: {e}")
        
        # Construire la réponse finale
        result = {
            "answer": state.get("answer", "Pas de réponse générée."),
            "sources": state.get("sources", []),
            "question_type": classification["question_type"],
            "workflow": workflow.value,
            "agent_chain": state.get("agent_chain", [])
        }
        
        # Ajouter les infos spécifiques selon le workflow
        if workflow == WorkflowType.COHERENCE_CHECK:
            result["coherence_issues"] = state.get("coherence_issues", [])
        elif workflow == WorkflowType.RESEARCH_THEN_CREATE:
            result["creative_suggestions"] = state.get("creative_suggestions", [])
        
        return result
    
    def ask(self, question: str) -> str:
        """
        Interface simple pour poser une question.
        
        Args:
            question: Question de l'utilisateur
            
        Returns:
            Réponse textuelle
        """
        result = self.run(question)
        return result["answer"]
    
    def run_specific_agent(
        self,
        question: str,
        agent_type: AgentType
    ) -> Dict[str, Any]:
        """
        Exécute un agent spécifique directement.
        
        Args:
            question: Question
            agent_type: Type d'agent à exécuter
            
        Returns:
            Résultat de l'agent
        """
        agent = self.agents.get(agent_type)
        
        if not agent:
            return {"error": f"Agent {agent_type.value} non disponible"}
        
        state: AgentState = {
            "question": question,
            "project_name": self.project_name,
            "question_type": agent_type.value,
            "documents": [],
            "agent_chain": []
        }
        
        state = agent.process(state)
        
        return {
            "answer": state.get("answer", ""),
            "sources": state.get("sources", []),
            "agent": agent_type.value
        }


def run_agent_workflow(
    project_name: str,
    question: str,
    workflow: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Fonction utilitaire pour exécuter un workflow d'agents.
    
    Args:
        project_name: Nom du projet
        question: Question de l'utilisateur
        workflow: Type de workflow ("simple", "research_then_create", etc.)
        **kwargs: Arguments supplémentaires
        
    Returns:
        Résultat du workflow
    """
    orchestrator = AgentOrchestrator(project_name, **kwargs)
    
    workflow_type = None
    if workflow:
        try:
            workflow_type = WorkflowType(workflow)
        except ValueError:
            pass
    
    return orchestrator.run(question, workflow=workflow_type)


# Tentative d'import de LangGraph pour le workflow avancé
try:
    from langgraph.graph import StateGraph, END
    
    def create_langgraph_workflow(project_name: str) -> StateGraph:
        """
        Crée un workflow LangGraph avec routing conditionnel.
        
        Args:
            project_name: Nom du projet
            
        Returns:
            StateGraph configuré
        """
        orchestrator = AgentOrchestrator(project_name)
        
        def route_question(state: AgentState) -> Literal["rechercheur", "creatif", "coherence"]:
            """Route vers l'agent approprié."""
            q_type = state.get("question_type", "factual")
            
            if q_type == "creative":
                return "creatif"
            elif q_type == "coherence":
                return "coherence"
            else:
                return "rechercheur"
        
        def rechercheur_node(state: AgentState) -> AgentState:
            agent = orchestrator.agents[AgentType.RECHERCHEUR]
            return agent.process(state)
        
        def creatif_node(state: AgentState) -> AgentState:
            agent = orchestrator.agents[AgentType.CREATIF]
            return agent.process(state)
        
        def coherence_node(state: AgentState) -> AgentState:
            agent = orchestrator.agents[AgentType.COHERENCE]
            return agent.process(state)
        
        # Créer le graphe
        workflow = StateGraph(AgentState)
        
        # Ajouter les nœuds
        workflow.add_node("rechercheur", rechercheur_node)
        workflow.add_node("creatif", creatif_node)
        workflow.add_node("coherence", coherence_node)
        
        # Définir le point d'entrée avec routing
        workflow.set_conditional_entry_point(
            route_question,
            {
                "rechercheur": "rechercheur",
                "creatif": "creatif",
                "coherence": "coherence"
            }
        )
        
        # Définir les sorties
        workflow.add_edge("rechercheur", END)
        workflow.add_edge("creatif", END)
        workflow.add_edge("coherence", END)
        
        return workflow.compile()
    
    LANGGRAPH_AVAILABLE = True
    
except ImportError:
    LANGGRAPH_AVAILABLE = False
    
    def create_langgraph_workflow(project_name: str):
        raise ImportError(
            "LangGraph n'est pas installé.\n"
            "Installez-le avec: pip install langgraph"
        )


# Test du module
if __name__ == "__main__":
    print("\n🎭 Test de l'Orchestrateur d'Agents")
    print("=" * 50)
    
    orchestrator = AgentOrchestrator("anomalie2084")
    
    # Test de classification
    questions = [
        "Qui est Alex Chen?",
        "Écris une scène où Alex utilise ses pouvoirs",
        "Y a-t-il des incohérences dans le worldbuilding?",
        "Analyse la structure narrative de la saison 1"
    ]
    
    print("\n📊 Classification des questions:")
    for q in questions:
        classification = orchestrator.classify_request(q)
        print(f"\n   Question: {q[:50]}...")
        print(f"   Type: {classification['question_type']}")
        print(f"   Workflow: {classification['workflow'].value}")
        
        agents = orchestrator.get_workflow_agents(classification['workflow'])
        print(f"   Agents: {[a.value for a in agents]}")
    
    print(f"\n📦 LangGraph disponible: {LANGGRAPH_AVAILABLE}")
    
    print("\n✅ Test terminé!")

