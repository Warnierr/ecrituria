"""
GraphRAG: Recherche augmentée combinant graphe de connaissances et RAG vectoriel.
Phase 2.3 du plan d'évolution Ecrituria v2.0

Ce module combine:
- Recherche vectorielle (sémantique)
- Traversée du graphe (relations)
- Contexte enrichi pour la génération
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

from src.graph.neo4j_client import Neo4jClient, Node, Relationship, get_neo4j_client
from src.graph.entity_extractor import EntityExtractor, normalize_entity_id

load_dotenv()


@dataclass
class GraphContext:
    """Contexte enrichi par le graphe."""
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    paths: List[List[Dict[str, Any]]]
    text_context: str


# Prompt GraphRAG enrichi
GRAPHRAG_PROMPT_TEMPLATE = """Tu es un assistant créatif spécialisé dans l'écriture de fiction.
Tu as accès à l'univers narratif de l'auteur via deux sources:

1. GRAPHE DE CONNAISSANCES (entités et relations):
{graph_context}

2. PASSAGES TEXTUELS PERTINENTS:
{text_context}

Question de l'auteur: {question}

Instructions:
- Utilise le graphe pour comprendre les relations entre les personnages, lieux et événements
- Utilise les passages textuels pour les détails et le contexte narratif
- Réponds de manière créative et cohérente avec l'univers établi
- Si tu proposes du contenu créatif, reste fidèle au ton et au style
- Mentionne explicitement les connexions importantes issues du graphe

Réponse:"""


class GraphRAGEngine:
    """
    Moteur GraphRAG combinant recherche vectorielle et traversée de graphe.
    
    Workflow:
    1. Extraire les entités de la question
    2. Récupérer le contexte du graphe (voisinage des entités)
    3. Effectuer une recherche vectorielle classique
    4. Fusionner les deux contextes
    5. Générer une réponse enrichie
    """
    
    def __init__(
        self,
        project_name: str,
        model: str = "gpt-4o-mini",
        use_openrouter: bool = True,
        graph_depth: int = 2,
        vector_k: int = 5
    ):
        """
        Initialise le moteur GraphRAG.
        
        Args:
            project_name: Nom du projet
            model: Modèle LLM à utiliser
            use_openrouter: Utiliser OpenRouter
            graph_depth: Profondeur de traversée du graphe
            vector_k: Nombre de documents vectoriels à récupérer
        """
        self.project_name = project_name
        self.model = model
        self.use_openrouter = use_openrouter
        self.graph_depth = graph_depth
        self.vector_k = vector_k
        
        # Initialiser les composants
        self.graph_client = get_neo4j_client(simulation_mode=True)  # Mode simulation par défaut
        self.entity_extractor = EntityExtractor(model=model, use_openrouter=use_openrouter)
        
        # LLM pour la génération
        if use_openrouter:
            self.llm = ChatOpenAI(
                model=model,
                temperature=0.7,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant RAG"
                }
            )
        else:
            self.llm = ChatOpenAI(model=model, temperature=0.7)
        
        # RAG vectoriel
        self._rag_engine = None
    
    @property
    def rag_engine(self):
        """Lazy loading du moteur RAG vectoriel."""
        if self._rag_engine is None:
            from src.rag import RAGEngine
            self._rag_engine = RAGEngine(
                self.project_name,
                model=self.model,
                use_openrouter=self.use_openrouter,
                use_hybrid_search=True,
                use_reranking=True
            )
        return self._rag_engine
    
    def extract_question_entities(self, question: str) -> List[str]:
        """
        Extrait les entités mentionnées dans une question.
        
        Args:
            question: Question de l'utilisateur
            
        Returns:
            Liste des IDs d'entités détectées
        """
        # Méthode 1: Utiliser le LLM pour l'extraction
        prompt = f"""Identifie les noms de personnages, lieux ou concepts mentionnés dans cette question.
Question: {question}

Réponds uniquement avec une liste JSON de noms:
["nom1", "nom2"]

Si aucune entité n'est trouvée, réponds: []

JSON:"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            import json
            import re
            
            # Trouver le JSON
            match = re.search(r'\[.*?\]', content, re.DOTALL)
            if match:
                names = json.loads(match.group())
                return [normalize_entity_id(name) for name in names if name]
        except Exception:
            pass
        
        # Méthode 2: Fallback - chercher dans les nœuds existants
        words = question.lower().split()
        entity_ids = []
        
        nodes = self.graph_client.find_nodes(limit=100)
        for node in nodes:
            node_name = node.get("nom", node.get("name", "")).lower()
            node_id = node.get("id", "")
            
            for word in words:
                if len(word) > 3 and (word in node_name or node_name in word):
                    if node_id not in entity_ids:
                        entity_ids.append(node_id)
        
        return entity_ids
    
    def get_graph_context(self, entity_ids: List[str]) -> GraphContext:
        """
        Récupère le contexte du graphe pour les entités données.
        
        Args:
            entity_ids: Liste des IDs d'entités
            
        Returns:
            GraphContext avec les entités, relations et chemins
        """
        all_entities = []
        all_relationships = []
        all_paths = []
        
        seen_entities = set()
        seen_rels = set()
        
        for entity_id in entity_ids:
            # Récupérer le contexte de l'entité
            context = self.graph_client.get_node_context(
                entity_id,
                depth=self.graph_depth
            )
            
            # Ajouter l'entité principale
            if context["node"] and context["node"].get("id") not in seen_entities:
                all_entities.append(context["node"])
                seen_entities.add(context["node"].get("id"))
            
            # Ajouter les voisins
            for neighbor in context.get("neighbors", []):
                if neighbor and neighbor.get("id") not in seen_entities:
                    all_entities.append(neighbor)
                    seen_entities.add(neighbor.get("id"))
            
            # Ajouter les relations
            for rel in context.get("relationships", []):
                rel_key = (
                    rel.get("source_id", ""),
                    rel.get("target_id", ""),
                    rel.get("type", "")
                )
                if rel_key not in seen_rels:
                    all_relationships.append(rel)
                    seen_rels.add(rel_key)
        
        # Chercher les chemins entre les entités (si plusieurs)
        if len(entity_ids) >= 2:
            for i, start_id in enumerate(entity_ids[:-1]):
                for end_id in entity_ids[i+1:]:
                    path = self.graph_client.find_path(
                        start_id, end_id,
                        max_depth=self.graph_depth + 1
                    )
                    if path:
                        all_paths.append(path)
        
        # Formater le contexte en texte
        text_context = self._format_graph_context(
            all_entities,
            all_relationships,
            all_paths
        )
        
        return GraphContext(
            entities=all_entities,
            relationships=all_relationships,
            paths=all_paths,
            text_context=text_context
        )
    
    def _format_graph_context(
        self,
        entities: List[Dict],
        relationships: List[Dict],
        paths: List[List[Dict]]
    ) -> str:
        """Formate le contexte du graphe en texte lisible."""
        lines = []
        
        if entities:
            lines.append("### Entités connues:")
            for entity in entities:
                entity_type = entity.get("label", entity.get("type", "?"))
                name = entity.get("nom", entity.get("name", entity.get("id", "?")))
                desc = entity.get("description", "")
                
                line = f"- [{entity_type}] {name}"
                if desc:
                    line += f": {desc[:100]}"
                lines.append(line)
        
        if relationships:
            lines.append("\n### Relations:")
            for rel in relationships:
                source = rel.get("source_id", rel.get("other_id", "?"))
                target = rel.get("target_id", rel.get("other_node", {}).get("id", "?"))
                rel_type = rel.get("type", "LIEN")
                
                lines.append(f"- {source} --[{rel_type}]--> {target}")
        
        if paths:
            lines.append("\n### Connexions trouvées:")
            for path in paths:
                path_names = [
                    p.get("nom", p.get("name", p.get("id", "?")))
                    for p in path
                ]
                lines.append(f"- Chemin: {' → '.join(path_names)}")
        
        return "\n".join(lines) if lines else "Aucune information dans le graphe."
    
    def ask(
        self,
        question: str,
        show_sources: bool = False
    ) -> Dict[str, Any] | str:
        """
        Pose une question avec enrichissement par le graphe.
        
        Args:
            question: Question à poser
            show_sources: Retourner les détails des sources
            
        Returns:
            Réponse (str) ou dict avec détails
        """
        # 1. Extraire les entités de la question
        entity_ids = self.extract_question_entities(question)
        
        # 2. Récupérer le contexte du graphe
        graph_context = self.get_graph_context(entity_ids)
        
        # 3. Récupérer le contexte vectoriel
        vector_docs = self.rag_engine.retrieve(question, k=self.vector_k)
        text_context = "\n\n---\n\n".join([
            f"[Source: {doc.metadata.get('relative_path', 'inconnu')}]\n{doc.page_content}"
            for doc in vector_docs
        ])
        
        # 4. Construire le prompt enrichi
        prompt = GRAPHRAG_PROMPT_TEMPLATE.format(
            graph_context=graph_context.text_context,
            text_context=text_context,
            question=question
        )
        
        # 5. Générer la réponse
        response = self.llm.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        if show_sources:
            return {
                "answer": answer,
                "graph_entities": graph_context.entities,
                "graph_relationships": graph_context.relationships,
                "vector_sources": vector_docs,
                "detected_entities": entity_ids
            }
        
        return answer
    
    def search_related_entities(
        self,
        entity_name: str,
        relation_type: str = None
    ) -> List[Dict]:
        """
        Recherche les entités liées à une entité donnée.
        
        Args:
            entity_name: Nom de l'entité
            relation_type: Filtrer par type de relation
            
        Returns:
            Liste des entités liées
        """
        entity_id = normalize_entity_id(entity_name)
        
        relationships = self.graph_client.get_relationships(
            entity_id,
            rel_type=relation_type
        )
        
        related = []
        for rel in relationships:
            other_id = rel.get("other_id")
            if other_id:
                other_node = self.graph_client.get_node(other_id)
                if other_node:
                    related.append({
                        "entity": other_node,
                        "relation": rel.get("type", "LIEN")
                    })
        
        return related
    
    def populate_graph_from_project(self, project_path: Path = None):
        """
        Peuple le graphe depuis les documents du projet.
        
        Args:
            project_path: Chemin vers le projet (défaut: data/{project_name})
        """
        if project_path is None:
            project_path = Path("data") / self.project_name
        
        print(f"\n📊 Population du graphe depuis {project_path}...")
        
        # Extraire toutes les entités
        entities, relations = self.entity_extractor.extract_from_project(project_path)
        
        # Ajouter au graphe
        print(f"\n💾 Ajout de {len(entities)} entités au graphe...")
        for entity in entities:
            node = Node(
                id=entity.id,
                label=entity.type,
                properties={
                    "nom": entity.name,
                    **entity.properties
                }
            )
            self.graph_client.create_node(node)
        
        print(f"🔗 Ajout de {len(relations)} relations...")
        for rel in relations:
            relationship = Relationship(
                source_id=rel.source_entity,
                target_id=rel.target_entity,
                type=rel.relation_type,
                properties=rel.properties
            )
            self.graph_client.create_relationship(relationship)
        
        stats = self.graph_client.get_stats()
        print(f"\n✅ Graphe peuplé: {stats['node_count']} nœuds, {stats['relationship_count']} relations")


def ask_with_graph(
    project_name: str,
    question: str,
    show_sources: bool = False,
    **kwargs
) -> Dict[str, Any] | str:
    """
    Fonction utilitaire pour poser une question avec GraphRAG.
    
    Args:
        project_name: Nom du projet
        question: Question à poser
        show_sources: Afficher les sources détaillées
        **kwargs: Arguments supplémentaires pour GraphRAGEngine
        
    Returns:
        Réponse enrichie par le graphe
    """
    engine = GraphRAGEngine(project_name, **kwargs)
    return engine.ask(question, show_sources=show_sources)


# Test du module
if __name__ == "__main__":
    print("\n🔍 Test du module GraphRAG")
    print("=" * 50)
    
    # Créer un moteur de test
    engine = GraphRAGEngine("anomalie2084")
    
    # Peupler le graphe avec quelques données de test
    print("\n📝 Création de données de test...")
    
    # Ajouter des nœuds manuellement
    from src.graph.neo4j_client import Node, Relationship
    
    engine.graph_client.create_node(Node(
        id="alex_chen",
        label="Personnage",
        properties={
            "nom": "Alex Chen",
            "role": "Protagoniste",
            "description": "Technicien de maintenance devenu Anomalie"
        }
    ))
    
    engine.graph_client.create_node(Node(
        id="maya",
        label="Personnage",
        properties={
            "nom": "Maya",
            "role": "Alliée",
            "description": "Programmeuse et amie d'enfance d'Alex"
        }
    ))
    
    engine.graph_client.create_node(Node(
        id="nexus",
        label="Lieu",
        properties={
            "nom": "Le Nexus",
            "description": "Cœur du réseau de données du Consortium"
        }
    ))
    
    engine.graph_client.create_relationship(Relationship(
        source_id="alex_chen",
        target_id="maya",
        type="CONNAIT",
        properties={"type_relation": "ami"}
    ))
    
    engine.graph_client.create_relationship(Relationship(
        source_id="alex_chen",
        target_id="nexus",
        type="VIENT_DE"
    ))
    
    stats = engine.graph_client.get_stats()
    print(f"   ✓ Graphe: {stats['node_count']} nœuds, {stats['relationship_count']} relations")
    
    # Test d'extraction d'entités
    print("\n🔍 Test extraction d'entités de question...")
    question = "Quelle est la relation entre Alex Chen et Maya?"
    entities = engine.extract_question_entities(question)
    print(f"   Question: {question}")
    print(f"   Entités détectées: {entities}")
    
    # Test de contexte graphe
    print("\n📊 Test récupération contexte graphe...")
    context = engine.get_graph_context(["alex_chen"])
    print(f"   Entités dans le contexte: {len(context.entities)}")
    print(f"   Relations trouvées: {len(context.relationships)}")
    print(f"\n   Contexte formaté:")
    print(context.text_context)
    
    print("\n✅ Test réussi!")

