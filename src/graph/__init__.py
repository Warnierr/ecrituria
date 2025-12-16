"""
Module de gestion du graphe de connaissances pour Ecrituria.
Phase 2 du plan d'évolution v2.0

Ce module permet de:
- Connecter et gérer une base Neo4j
- Extraire automatiquement les entités des documents
- Effectuer des requêtes GraphRAG (graphe + vecteurs)
"""
from .neo4j_client import Neo4jClient, get_neo4j_client
from .entity_extractor import EntityExtractor, extract_entities_from_text
from .graph_rag import GraphRAGEngine, ask_with_graph

__all__ = [
    "Neo4jClient",
    "get_neo4j_client",
    "EntityExtractor",
    "extract_entities_from_text",
    "GraphRAGEngine",
    "ask_with_graph"
]

