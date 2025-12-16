"""
Agent Cohérence: Détecte les incohérences narratives.
Phase 3 du plan d'évolution Ecrituria v2.0
"""
from typing import Dict, Any, List
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentState, AgentType


@dataclass
class CoherenceIssue:
    """Représente une incohérence détectée."""
    type: str  # temporal, character, worldbuilding, plot
    severity: str  # low, medium, high
    description: str
    sources: List[str]
    suggestion: str = ""


COHERENCE_PROMPT = """Tu es un expert en cohérence narrative. Analyse les informations suivantes pour détecter d'éventuelles incohérences.

INFORMATIONS DE L'UNIVERS:
{context}

{specific_query}

Recherche les types d'incohérences suivants:
1. TEMPORELLES: Dates contradictoires, chronologie impossible
2. PERSONNAGES: Traits contradictoires, capacités incohérentes
3. WORLDBUILDING: Règles de l'univers contradictoires
4. INTRIGUE: Événements qui ne s'enchaînent pas logiquement

Pour chaque incohérence trouvée, indique:
- Type (temporal/character/worldbuilding/plot)
- Sévérité (low/medium/high)
- Description du problème
- Sources concernées
- Suggestion de correction

Si aucune incohérence n'est trouvée, dis-le clairement.

Analyse:"""


SPECIFIC_CHECK_PROMPT = """Tu es un vérificateur de cohérence narrative.

CONTEXTE:
{context}

VÉRIFICATION DEMANDÉE:
{check_request}

Analyse cette situation et indique:
1. Est-ce cohérent avec l'univers établi? (oui/non/partiellement)
2. Si non, explique pourquoi
3. Suggère des corrections si nécessaire

Réponse:"""


class CoherenceAgent(BaseAgent):
    """
    Agent spécialisé dans la détection d'incohérences.
    
    Analyse les documents et le graphe pour trouver:
    - Contradictions temporelles
    - Incohérences de personnages
    - Problèmes de worldbuilding
    - Trous dans l'intrigue
    """
    
    agent_type = AgentType.COHERENCE
    description = "Détecte les incohérences narratives"
    
    def should_run(self, state: AgentState) -> bool:
        """S'exécute pour les questions de cohérence."""
        question_type = state.get("question_type", "")
        question = state.get("question", "").lower()
        
        # Mots-clés de cohérence
        coherence_keywords = [
            "cohérent", "incohérence", "contradiction", "erreur",
            "problème", "vérifier", "checker", "logique", "possible"
        ]
        
        return (
            question_type == "coherence" or
            any(kw in question for kw in coherence_keywords)
        )
    
    def process(self, state: AgentState) -> AgentState:
        """
        Analyse la cohérence et détecte les incohérences.
        """
        question = state.get("question", "")
        
        # Récupérer le contexte si nécessaire
        if not state.get("documents"):
            context = self.retrieve_context(question, k=8, use_graph=True)
            state["documents"] = context["documents"]
            state["graph_context"] = context.get("graph_context", {})
        
        # Formater le contexte
        text_context = self.format_documents_context(state.get("documents", []))
        
        # Déterminer si c'est une vérification spécifique ou générale
        if self._is_specific_check(question):
            answer = self._specific_coherence_check(question, text_context)
        else:
            answer = self._general_coherence_analysis(question, text_context)
        
        # Parser les incohérences trouvées
        issues = self._parse_issues(answer)
        state["coherence_issues"] = [
            {
                "type": issue.type,
                "severity": issue.severity,
                "description": issue.description,
                "sources": issue.sources,
                "suggestion": issue.suggestion
            }
            for issue in issues
        ]
        
        # Mettre à jour la réponse
        state["answer"] = answer
        state["sources"] = [
            doc.metadata.get("relative_path", "")
            for doc in state.get("documents", [])
        ]
        
        state["agent_chain"] = state.get("agent_chain", []) + [self.agent_type.value]
        
        return state
    
    def _is_specific_check(self, question: str) -> bool:
        """Détermine si c'est une vérification spécifique."""
        specific_patterns = [
            "est-ce que", "peut-il", "peut-elle", "est-il possible",
            "serait-il", "comment expliquer", "pourquoi"
        ]
        question_lower = question.lower()
        return any(p in question_lower for p in specific_patterns)
    
    def _specific_coherence_check(self, question: str, context: str) -> str:
        """Effectue une vérification de cohérence spécifique."""
        prompt = SPECIFIC_CHECK_PROMPT.format(
            context=context,
            check_request=question
        )
        return self.invoke_llm(prompt)
    
    def _general_coherence_analysis(self, question: str, context: str) -> str:
        """Effectue une analyse de cohérence générale."""
        specific_query = f"Question spécifique de l'auteur: {question}" if question else ""
        
        prompt = COHERENCE_PROMPT.format(
            context=context,
            specific_query=specific_query
        )
        return self.invoke_llm(prompt)
    
    def _parse_issues(self, analysis: str) -> List[CoherenceIssue]:
        """Parse les incohérences depuis la réponse du LLM."""
        issues = []
        
        # Patterns simples pour extraire les incohérences
        lines = analysis.split('\n')
        current_issue = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Détecter le type
            for issue_type in ["temporal", "character", "worldbuilding", "plot"]:
                if issue_type in line_lower:
                    if current_issue:
                        issues.append(current_issue)
                    current_issue = CoherenceIssue(
                        type=issue_type,
                        severity="medium",
                        description="",
                        sources=[]
                    )
                    break
            
            # Détecter la sévérité
            if current_issue:
                for severity in ["high", "medium", "low"]:
                    if severity in line_lower:
                        current_issue.severity = severity
                        break
                
                # Ajouter la description
                if line.strip() and not any(
                    x in line_lower for x in ["type:", "sévérité:", "sources:", "suggestion:"]
                ):
                    current_issue.description += line.strip() + " "
        
        if current_issue and current_issue.description:
            issues.append(current_issue)
        
        return issues
    
    def check_character_consistency(self, character_name: str) -> Dict[str, Any]:
        """
        Vérifie la cohérence d'un personnage.
        
        Args:
            character_name: Nom du personnage
            
        Returns:
            Analyse de cohérence
        """
        # Récupérer toutes les infos sur le personnage
        docs = self.rag_engine.retrieve(
            f"Tout sur {character_name}: traits, capacités, histoire, relations",
            k=10
        )
        
        context = self.format_documents_context(docs)
        
        prompt = f"""Analyse la cohérence du personnage {character_name} dans cet univers.

INFORMATIONS TROUVÉES:
{context}

Vérifie:
1. Les traits de caractère sont-ils cohérents dans toutes les sources?
2. Les capacités/pouvoirs sont-ils utilisés de façon cohérente?
3. L'histoire personnelle est-elle sans contradictions?
4. Les relations avec d'autres personnages sont-elles logiques?

Analyse détaillée:"""
        
        analysis = self.invoke_llm(prompt)
        
        return {
            "character": character_name,
            "analysis": analysis,
            "sources": [doc.metadata.get("relative_path") for doc in docs]
        }
    
    def check_timeline(self) -> Dict[str, Any]:
        """
        Vérifie la cohérence de la timeline.
        
        Returns:
            Analyse de la chronologie
        """
        # Récupérer les événements
        docs = self.rag_engine.retrieve(
            "Événements, dates, chronologie, timeline, avant, après, pendant",
            k=10
        )
        
        context = self.format_documents_context(docs)
        
        prompt = f"""Analyse la chronologie de cet univers.

ÉVÉNEMENTS ET DATES MENTIONNÉS:
{context}

Vérifie:
1. Les dates sont-elles cohérentes entre elles?
2. L'ordre des événements est-il logique?
3. Y a-t-il des anachronismes?
4. Les durées mentionnées sont-elles réalistes?

Analyse de la timeline:"""
        
        analysis = self.invoke_llm(prompt)
        
        return {
            "analysis": analysis,
            "sources": [doc.metadata.get("relative_path") for doc in docs]
        }


# Test du module
if __name__ == "__main__":
    print("\n🔍 Test de l'Agent Cohérence")
    print("=" * 50)
    
    agent = CoherenceAgent("anomalie2084")
    
    # Test de classification
    questions = [
        "Y a-t-il des incohérences dans l'histoire d'Alex?",
        "Est-ce qu'Alex peut utiliser ses pouvoirs sans le Nexus?",
        "Vérifie la timeline de la saison 1"
    ]
    
    for q in questions:
        state: AgentState = {
            "question": q,
            "project_name": "anomalie2084"
        }
        
        print(f"\n📝 Question: {q[:50]}...")
        print(f"   Should run: {agent.should_run(state)}")
    
    print("\n✅ Test terminé!")

