"""
Module d'agents spécialisés pour l'assistance à l'écriture.
Phase 3 du plan d'évolution Ecrituria v2.0

Agents disponibles:
- RechercheurAgent: Trouve l'information dans les docs et le graphe
- CoherenceAgent: Détecte les incohérences narratives
- CreatifAgent: Génère du contenu créatif (scènes, dialogues)
- EditeurAgent: Améliore le style et corrige
- AnalysteAgent: Analyse la structure narrative
"""
from .base_agent import BaseAgent, AgentState, AgentResponse
from .rechercheur import RechercheurAgent
from .coherence import CoherenceAgent
from .creatif import CreatifAgent
from .orchestrator import AgentOrchestrator, run_agent_workflow

__all__ = [
    "BaseAgent",
    "AgentState",
    "AgentResponse",
    "RechercheurAgent",
    "CoherenceAgent",
    "CreatifAgent",
    "AgentOrchestrator",
    "run_agent_workflow"
]

