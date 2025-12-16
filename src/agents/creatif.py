"""
Agent Créatif: Génère du contenu créatif cohérent avec l'univers.
Phase 3 du plan d'évolution Ecrituria v2.0
"""
from typing import Dict, Any, List
from enum import Enum

from .base_agent import BaseAgent, AgentState, AgentType


class CreativeTaskType(Enum):
    """Types de tâches créatives."""
    SCENE = "scene"
    DIALOGUE = "dialogue"
    DESCRIPTION = "description"
    BRAINSTORM = "brainstorm"
    CONTINUATION = "continuation"
    VARIATION = "variation"


CREATIVE_PROMPTS = {
    "scene": """Tu es un écrivain talentueux qui crée des scènes immersives.

UNIVERS ET CONTEXTE:
{context}

DEMANDE: {request}

Écris une scène qui:
- Respecte parfaitement le ton et le style de l'univers
- Utilise les personnages et lieux établis correctement
- Inclut des descriptions sensorielles vivantes
- Maintient la cohérence avec ce qui existe

SCÈNE:""",

    "dialogue": """Tu es un dialoguiste expert qui capture les voix uniques des personnages.

INFORMATIONS SUR LES PERSONNAGES:
{context}

DEMANDE: {request}

Écris un dialogue qui:
- Reflète la personnalité unique de chaque personnage
- Fait avancer l'intrigue ou révèle des informations
- Sonne naturel et authentique
- Respecte les relations établies entre les personnages

DIALOGUE:""",

    "description": """Tu es un maître des descriptions évocatrices.

CONTEXTE DE L'UNIVERS:
{context}

DEMANDE: {request}

Écris une description qui:
- Peint une image vivante dans l'esprit du lecteur
- Utilise les cinq sens
- Crée l'atmosphère appropriée
- S'intègre naturellement dans l'univers

DESCRIPTION:""",

    "brainstorm": """Tu es un co-scénariste créatif qui génère des idées originales.

CONTEXTE ACTUEL:
{context}

DEMANDE: {request}

Propose plusieurs idées qui:
- S'intègrent parfaitement dans l'univers établi
- Offrent des possibilités narratives intéressantes
- Explorent des aspects inattendus
- Respectent les personnages et leur développement

IDÉES:""",

    "continuation": """Tu es un écrivain qui continue l'histoire de façon naturelle.

CONTEXTE ET CE QUI PRÉCÈDE:
{context}

TEXTE À CONTINUER: {request}

Continue le texte en:
- Gardant exactement le même style et ton
- Respectant la voix narrative établie
- Faisant progresser naturellement l'histoire
- Maintenant la cohérence avec l'univers

CONTINUATION:""",

    "variation": """Tu es un écrivain qui crée des variations créatives.

CONTEXTE:
{context}

ÉLÉMENT À VARIER: {request}

Propose des variations qui:
- Explorent différentes possibilités
- Restent cohérentes avec l'univers
- Offrent des perspectives nouvelles
- Peuvent enrichir l'histoire

VARIATIONS:"""
}


class CreatifAgent(BaseAgent):
    """
    Agent spécialisé dans la génération de contenu créatif.
    
    Capable de générer:
    - Scènes narratives
    - Dialogues
    - Descriptions
    - Idées et brainstorming
    - Continuations de texte
    - Variations créatives
    """
    
    agent_type = AgentType.CREATIF
    description = "Génère du contenu créatif cohérent avec l'univers"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Température plus haute pour la créativité
        self.temperature = 0.8
    
    def should_run(self, state: AgentState) -> bool:
        """S'exécute pour les demandes créatives."""
        question_type = state.get("question_type", "")
        question = state.get("question", "").lower()
        
        creative_keywords = [
            "écris", "crée", "génère", "imagine", "propose",
            "invente", "scène", "dialogue", "description",
            "continue", "variation", "idée", "brainstorm"
        ]
        
        return (
            question_type == "creative" or
            any(kw in question for kw in creative_keywords)
        )
    
    def process(self, state: AgentState) -> AgentState:
        """
        Génère du contenu créatif basé sur le contexte.
        """
        question = state.get("question", "")
        
        # Récupérer le contexte
        if not state.get("documents"):
            context = self.retrieve_context(question, k=5, use_graph=True)
            state["documents"] = context["documents"]
            state["graph_context"] = context.get("graph_context", {})
        
        # Déterminer le type de tâche créative
        task_type = self._classify_creative_task(question)
        
        # Formater le contexte
        text_context = self.format_documents_context(state.get("documents", []))
        
        # Ajouter le contexte du graphe si disponible
        graph_ctx = state.get("graph_context", {})
        if hasattr(graph_ctx, 'text_context'):
            text_context += f"\n\n### Relations connues:\n{graph_ctx.text_context}"
        
        # Générer le contenu
        prompt_template = CREATIVE_PROMPTS.get(task_type.value, CREATIVE_PROMPTS["brainstorm"])
        prompt = prompt_template.format(context=text_context, request=question)
        
        # Utiliser une température plus haute pour la créativité
        original_temp = self.llm.temperature
        self.llm.temperature = 0.8
        
        answer = self.invoke_llm(prompt)
        
        self.llm.temperature = original_temp
        
        # Stocker les suggestions créatives
        state["creative_suggestions"] = state.get("creative_suggestions", []) + [answer]
        
        state["answer"] = answer
        state["sources"] = [
            doc.metadata.get("relative_path", "")
            for doc in state.get("documents", [])
        ]
        
        state["agent_chain"] = state.get("agent_chain", []) + [self.agent_type.value]
        
        return state
    
    def _classify_creative_task(self, question: str) -> CreativeTaskType:
        """Classifie le type de tâche créative demandée."""
        question_lower = question.lower()
        
        if any(kw in question_lower for kw in ["scène", "scene", "moment"]):
            return CreativeTaskType.SCENE
        elif any(kw in question_lower for kw in ["dialogue", "conversation", "échange"]):
            return CreativeTaskType.DIALOGUE
        elif any(kw in question_lower for kw in ["description", "décris", "décrire"]):
            return CreativeTaskType.DESCRIPTION
        elif any(kw in question_lower for kw in ["continue", "suite", "après"]):
            return CreativeTaskType.CONTINUATION
        elif any(kw in question_lower for kw in ["variation", "alternative", "autrement"]):
            return CreativeTaskType.VARIATION
        else:
            return CreativeTaskType.BRAINSTORM
    
    def generate_scene(
        self,
        description: str,
        characters: List[str] = None,
        location: str = None,
        mood: str = None
    ) -> str:
        """
        Génère une scène avec des paramètres spécifiques.
        
        Args:
            description: Description de la scène souhaitée
            characters: Personnages à inclure
            location: Lieu de la scène
            mood: Atmosphère souhaitée
            
        Returns:
            Scène générée
        """
        # Construire la requête enrichie
        query_parts = [description]
        if characters:
            query_parts.append(f"Personnages: {', '.join(characters)}")
        if location:
            query_parts.append(f"Lieu: {location}")
        if mood:
            query_parts.append(f"Atmosphère: {mood}")
        
        full_query = ". ".join(query_parts)
        
        # Récupérer le contexte pertinent
        context = self.retrieve_context(full_query, k=5)
        text_context = self.format_documents_context(context["documents"])
        
        prompt = CREATIVE_PROMPTS["scene"].format(
            context=text_context,
            request=full_query
        )
        
        return self.invoke_llm(prompt)
    
    def generate_dialogue(
        self,
        situation: str,
        characters: List[str],
        tension_level: str = "normal"
    ) -> str:
        """
        Génère un dialogue entre personnages.
        
        Args:
            situation: Contexte du dialogue
            characters: Personnages impliqués
            tension_level: Niveau de tension (low, normal, high)
            
        Returns:
            Dialogue généré
        """
        # Récupérer les infos sur les personnages
        char_query = f"Personnalité et façon de parler de {', '.join(characters)}"
        context = self.retrieve_context(char_query, k=5)
        text_context = self.format_documents_context(context["documents"])
        
        request = f"""Situation: {situation}
Personnages: {', '.join(characters)}
Niveau de tension: {tension_level}"""
        
        prompt = CREATIVE_PROMPTS["dialogue"].format(
            context=text_context,
            request=request
        )
        
        return self.invoke_llm(prompt)
    
    def brainstorm_ideas(
        self,
        topic: str,
        count: int = 5
    ) -> List[str]:
        """
        Génère plusieurs idées sur un sujet.
        
        Args:
            topic: Sujet du brainstorming
            count: Nombre d'idées souhaitées
            
        Returns:
            Liste d'idées
        """
        context = self.retrieve_context(topic, k=5)
        text_context = self.format_documents_context(context["documents"])
        
        request = f"{topic}\n\nGénère exactement {count} idées distinctes."
        
        prompt = CREATIVE_PROMPTS["brainstorm"].format(
            context=text_context,
            request=request
        )
        
        response = self.invoke_llm(prompt)
        
        # Parser les idées (simple split par numéros)
        import re
        ideas = re.split(r'\d+\.\s*', response)
        ideas = [idea.strip() for idea in ideas if idea.strip()]
        
        return ideas[:count]


# Test du module
if __name__ == "__main__":
    print("\n🎨 Test de l'Agent Créatif")
    print("=" * 50)
    
    agent = CreatifAgent("anomalie2084")
    
    # Test de classification
    questions = [
        "Écris une scène où Alex découvre ses pouvoirs",
        "Imagine un dialogue entre Alex et Maya",
        "Décris le Nexus au lever du soleil",
        "Propose des idées pour le chapitre 2",
        "Continue cette phrase: Alex posa sa main sur le terminal et..."
    ]
    
    for q in questions:
        state: AgentState = {
            "question": q,
            "project_name": "anomalie2084"
        }
        
        task = agent._classify_creative_task(q)
        print(f"\n📝 [{task.value:12}] {q[:50]}...")
        print(f"   Should run: {agent.should_run(state)}")
    
    print("\n✅ Test terminé!")

