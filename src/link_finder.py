"""
Module de recherche de liens entre concepts dans l'univers de fiction.
Identifie les connexions entre personnages, lieux, événements, objets, thèmes.
"""
from pathlib import Path
from typing import List, Dict, Set, Tuple
from src.rag import get_relevant_passages
import re


def extract_entities(text: str) -> Dict[str, Set[str]]:
    """
    Extrait les entités nommées d'un texte.
    
    Returns:
        Dict avec clés: 'personnages', 'lieux', 'objets', 'concepts'
    """
    entities = {
        'personnages': set(),
        'lieux': set(),
        'objets': set(),
        'concepts': set()
    }
    
    # Patterns simples pour détecter les entités
    # Personnages : noms propres suivis de descriptions de personnage
    person_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
    
    # Lieux : mots-clés géographiques
    lieu_keywords = ['Lutéris', 'Lutèce', 'Zone', 'quartier', 'Nord', 'Sud', 'Docker', 'BNF']
    
    # Objets : artefacts, technologies
    objet_keywords = ['tablette', 'artefact', 'compagnon', 'IA', 'Nexus', 'médaillon']
    
    # Concepts : thèmes récurrents
    concept_keywords = ['Anomalie', 'mémoire', 'archives', 'résistance', 'Empire', 'Tao']
    
    # Extraction basique
    words = text.split()
    for i, word in enumerate(words):
        if any(kw.lower() in word.lower() for kw in lieu_keywords):
            entities['lieux'].add(word)
        if any(kw.lower() in word.lower() for kw in objet_keywords):
            entities['objets'].add(word)
        if any(kw.lower() in word.lower() for kw in concept_keywords):
            entities['concepts'].add(word)
    
    return entities


def find_links(project_name: str, concept: str, k: int = 10) -> Dict[str, List[Dict]]:
    """
    Trouve les liens entre un concept et d'autres éléments de l'univers.
    
    Args:
        project_name: Nom du projet
        concept: Concept à analyser (ex: "Lutéris", "Anomalie", "Historien")
        k: Nombre de passages à analyser
        
    Returns:
        Dict avec les liens trouvés par catégorie
    """
    # Récupérer les passages pertinents
    passages = get_relevant_passages(project_name, concept, k=k)
    
    links = {
        'personnages': [],
        'lieux': [],
        'objets': [],
        'concepts': [],
        'fichiers': []
    }
    
    # Extraire les entités de chaque passage
    for doc in passages:
        entities = extract_entities(doc.page_content)
        source_file = doc.metadata.get('relative_path', 'source inconnue')
        
        # Compter les occurrences
        for category, items in entities.items():
            for item in items:
                if item.lower() != concept.lower():
                    # Chercher si l'item existe déjà
                    found = False
                    for link in links[category]:
                        if link['nom'].lower() == item.lower():
                            link['occurrences'] += 1
                            if source_file not in link['sources']:
                                link['sources'].append(source_file)
                            found = True
                            break
                    
                    if not found:
                        links[category].append({
                            'nom': item,
                            'occurrences': 1,
                            'sources': [source_file],
                            'contexte': doc.page_content[:200] + "..."
                        })
    
    # Trier par nombre d'occurrences
    for category in links:
        links[category].sort(key=lambda x: x['occurrences'], reverse=True)
    
    # Ajouter les fichiers sources
    links['fichiers'] = list(set([doc.metadata.get('relative_path', '?') for doc in passages]))
    
    return links


def suggest_connections(project_name: str, entity1: str, entity2: str) -> Dict:
    """
    Suggère des connexions entre deux entités.
    
    Args:
        project_name: Nom du projet
        entity1: Première entité
        entity2: Deuxième entité
        
    Returns:
        Dict avec les passages qui mentionnent les deux entités
    """
    # Rechercher les deux entités
    passages1 = get_relevant_passages(project_name, entity1, k=5)
    passages2 = get_relevant_passages(project_name, entity2, k=5)
    
    # Trouver les passages qui mentionnent les deux
    common_passages = []
    passages1_ids = {id(doc): doc for doc in passages1}
    
    for doc in passages2:
        if id(doc) in passages1_ids:
            common_passages.append({
                'contenu': doc.page_content,
                'source': doc.metadata.get('relative_path', 'source inconnue')
            })
    
    return {
        'entity1': entity1,
        'entity2': entity2,
        'passages_communs': common_passages,
        'lien_direct': len(common_passages) > 0
    }


def analyze_worldbuilding_gaps(project_name: str) -> List[Dict]:
    """
    Analyse les lacunes dans le worldbuilding.
    Suggère ce qui pourrait être développé.
    
    Returns:
        Liste de suggestions de développement
    """
    suggestions = []
    
    # Concepts clés à vérifier
    key_concepts = ['Lutéris', 'Anomalie', 'Historien', 'Protagoniste', 'tablette', 'compagnon IA']
    
    for concept in key_concepts:
        passages = get_relevant_passages(project_name, concept, k=3)
        
        if len(passages) < 2:
            suggestions.append({
                'type': 'concept_sous_developpe',
                'concept': concept,
                'passages_trouves': len(passages),
                'suggestion': f"Le concept '{concept}' est peu développé. Considérez ajouter plus de détails."
            })
    
    return suggestions

