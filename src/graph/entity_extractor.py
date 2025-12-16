"""
Extraction automatique d'entités narratives depuis les documents.
Phase 2.2 du plan d'évolution Ecrituria v2.0

Utilise un LLM pour extraire:
- Personnages
- Lieux
- Événements
- Objets importants
- Relations entre entités
"""
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ExtractedEntity:
    """Entité extraite d'un document."""
    id: str
    type: str  # Personnage, Lieu, Evenement, Objet, Theme
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_file: str = ""
    confidence: float = 1.0


@dataclass
class ExtractedRelation:
    """Relation extraite entre deux entités."""
    source_entity: str
    target_entity: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_file: str = ""


# Prompt pour l'extraction d'entités
ENTITY_EXTRACTION_PROMPT = """Tu es un expert en analyse narrative. Analyse le texte suivant et extrait les entités importantes.

TEXTE À ANALYSER:
{text}

INSTRUCTIONS:
Extrait les entités suivantes si présentes:
1. PERSONNAGES: Noms, rôles, descriptions, traits de caractère
2. LIEUX: Noms, descriptions, atmosphère
3. ÉVÉNEMENTS: Actions importantes, dates si mentionnées
4. OBJETS: Objets importants pour l'histoire
5. THÈMES: Thèmes narratifs identifiés

Réponds UNIQUEMENT avec un JSON valide au format suivant:
{{
    "entities": [
        {{
            "type": "Personnage|Lieu|Evenement|Objet|Theme",
            "name": "Nom de l'entité",
            "properties": {{
                "description": "Description courte",
                "role": "Rôle si applicable",
                "traits": ["trait1", "trait2"]
            }}
        }}
    ],
    "relations": [
        {{
            "source": "Nom entité source",
            "target": "Nom entité cible",
            "type": "CONNAIT|VIENT_DE|PARTICIPE_A|POSSEDE|ALLIE_DE|ENNEMI_DE|FAMILLE_DE",
            "properties": {{}}
        }}
    ]
}}

JSON:"""


# Prompt pour l'extraction depuis une fiche personnage structurée
CHARACTER_EXTRACTION_PROMPT = """Tu es un expert en analyse de fiches personnages. Analyse cette fiche et extrait les informations structurées.

FICHE PERSONNAGE:
{text}

Réponds UNIQUEMENT avec un JSON valide contenant:
{{
    "personnage": {{
        "nom": "Nom complet",
        "role": "Rôle dans l'histoire",
        "age": "Âge si mentionné",
        "description_physique": "Description physique",
        "personnalite": "Traits de personnalité",
        "capacites": ["capacité1", "capacité2"],
        "objectifs": "Objectifs du personnage",
        "background": "Histoire personnelle"
    }},
    "relations": [
        {{
            "avec": "Nom de l'autre personnage",
            "type": "ami|ennemi|famille|collegue|autre",
            "description": "Nature de la relation"
        }}
    ],
    "lieux_associes": ["lieu1", "lieu2"],
    "themes": ["thème1", "thème2"]
}}

JSON:"""


def normalize_entity_id(name: str) -> str:
    """
    Normalise un nom en ID unique.
    
    Args:
        name: Nom de l'entité
        
    Returns:
        ID normalisé (snake_case, sans accents)
    """
    import unicodedata
    
    # Supprimer les accents
    normalized = unicodedata.normalize('NFKD', name)
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    
    # Convertir en snake_case
    normalized = normalized.lower()
    normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
    normalized = normalized.strip('_')
    
    return normalized


class EntityExtractor:
    """
    Extracteur d'entités utilisant un LLM.
    
    Capable d'extraire automatiquement les personnages, lieux,
    événements et relations depuis des documents de fiction.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        use_openrouter: bool = True
    ):
        """
        Initialise l'extracteur.
        
        Args:
            model: Modèle LLM à utiliser
            use_openrouter: Utiliser OpenRouter
        """
        self.model = model
        
        if use_openrouter:
            self.llm = ChatOpenAI(
                model=model,
                temperature=0,  # Déterministe pour l'extraction
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://github.com/fiction-assistant",
                    "X-Title": "Fiction Assistant RAG"
                }
            )
        else:
            self.llm = ChatOpenAI(model=model, temperature=0)
    
    def extract_from_text(
        self,
        text: str,
        source_file: str = "",
        prompt_template: str = None
    ) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        """
        Extrait les entités et relations d'un texte.
        
        Args:
            text: Texte à analyser
            source_file: Fichier source pour la traçabilité
            prompt_template: Template personnalisé (optionnel)
            
        Returns:
            Tuple (entités, relations)
        """
        if prompt_template is None:
            prompt_template = ENTITY_EXTRACTION_PROMPT
        
        # Limiter la taille du texte
        max_chars = 4000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        prompt = prompt_template.format(text=text)
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parser le JSON
            data = self._parse_json_response(content)
            
            # Convertir en objets
            entities = []
            relations = []
            
            for entity_data in data.get("entities", []):
                entity = ExtractedEntity(
                    id=normalize_entity_id(entity_data.get("name", "")),
                    type=entity_data.get("type", "Unknown"),
                    name=entity_data.get("name", ""),
                    properties=entity_data.get("properties", {}),
                    source_file=source_file
                )
                entities.append(entity)
            
            for rel_data in data.get("relations", []):
                relation = ExtractedRelation(
                    source_entity=normalize_entity_id(rel_data.get("source", "")),
                    target_entity=normalize_entity_id(rel_data.get("target", "")),
                    relation_type=rel_data.get("type", "CONNAIT"),
                    properties=rel_data.get("properties", {}),
                    source_file=source_file
                )
                relations.append(relation)
            
            return entities, relations
            
        except Exception as e:
            print(f"⚠️ Erreur d'extraction: {e}")
            return [], []
    
    def extract_from_character_sheet(
        self,
        text: str,
        source_file: str = ""
    ) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        """
        Extrait les informations d'une fiche personnage structurée.
        
        Args:
            text: Contenu de la fiche personnage
            source_file: Fichier source
            
        Returns:
            Tuple (entités, relations)
        """
        prompt = CHARACTER_EXTRACTION_PROMPT.format(text=text)
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            data = self._parse_json_response(content)
            
            entities = []
            relations = []
            
            # Entité principale (le personnage)
            char_data = data.get("personnage", {})
            if char_data.get("nom"):
                char_entity = ExtractedEntity(
                    id=normalize_entity_id(char_data.get("nom")),
                    type="Personnage",
                    name=char_data.get("nom"),
                    properties={
                        "role": char_data.get("role", ""),
                        "age": char_data.get("age", ""),
                        "description": char_data.get("description_physique", ""),
                        "personnalite": char_data.get("personnalite", ""),
                        "capacites": char_data.get("capacites", []),
                        "objectifs": char_data.get("objectifs", ""),
                        "background": char_data.get("background", "")
                    },
                    source_file=source_file
                )
                entities.append(char_entity)
                
                # Relations avec d'autres personnages
                for rel_data in data.get("relations", []):
                    relation = ExtractedRelation(
                        source_entity=char_entity.id,
                        target_entity=normalize_entity_id(rel_data.get("avec", "")),
                        relation_type=self._map_relation_type(rel_data.get("type", "")),
                        properties={"description": rel_data.get("description", "")},
                        source_file=source_file
                    )
                    relations.append(relation)
                
                # Lieux associés
                for lieu in data.get("lieux_associes", []):
                    lieu_entity = ExtractedEntity(
                        id=normalize_entity_id(lieu),
                        type="Lieu",
                        name=lieu,
                        source_file=source_file
                    )
                    entities.append(lieu_entity)
                    
                    relation = ExtractedRelation(
                        source_entity=char_entity.id,
                        target_entity=lieu_entity.id,
                        relation_type="VIENT_DE",
                        source_file=source_file
                    )
                    relations.append(relation)
                
                # Thèmes
                for theme in data.get("themes", []):
                    theme_entity = ExtractedEntity(
                        id=normalize_entity_id(theme),
                        type="Theme",
                        name=theme,
                        source_file=source_file
                    )
                    entities.append(theme_entity)
                    
                    relation = ExtractedRelation(
                        source_entity=char_entity.id,
                        target_entity=theme_entity.id,
                        relation_type="INCARNE",
                        source_file=source_file
                    )
                    relations.append(relation)
            
            return entities, relations
            
        except Exception as e:
            print(f"⚠️ Erreur d'extraction fiche personnage: {e}")
            return [], []
    
    def extract_from_document(
        self,
        doc: Document
    ) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        """
        Extrait les entités d'un document LangChain.
        
        Args:
            doc: Document à analyser
            
        Returns:
            Tuple (entités, relations)
        """
        source_file = doc.metadata.get("relative_path", "")
        folder = doc.metadata.get("folder", "").lower()
        
        # Utiliser le template approprié selon le type de document
        if folder == "personnages" or "personnage" in source_file.lower():
            return self.extract_from_character_sheet(
                doc.page_content,
                source_file
            )
        else:
            return self.extract_from_text(
                doc.page_content,
                source_file
            )
    
    def extract_from_project(
        self,
        project_path: Path,
        extensions: List[str] = None
    ) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
        """
        Extrait toutes les entités d'un projet.
        
        Args:
            project_path: Chemin vers le projet
            extensions: Extensions de fichiers à traiter
            
        Returns:
            Tuple (toutes les entités, toutes les relations)
        """
        if extensions is None:
            extensions = [".md", ".txt"]
        
        from src.loaders import load_project_documents
        
        docs = load_project_documents(project_path, extensions=extensions)
        
        all_entities = []
        all_relations = []
        
        print(f"\n🔍 Extraction d'entités depuis {len(docs)} documents...")
        
        for i, doc in enumerate(docs):
            source = doc.metadata.get("relative_path", f"doc_{i}")
            print(f"   [{i+1}/{len(docs)}] {source}...", end=" ")
            
            entities, relations = self.extract_from_document(doc)
            all_entities.extend(entities)
            all_relations.extend(relations)
            
            print(f"✓ {len(entities)} entités, {len(relations)} relations")
        
        # Dédupliquer les entités par ID
        unique_entities = {}
        for entity in all_entities:
            if entity.id not in unique_entities:
                unique_entities[entity.id] = entity
            else:
                # Fusionner les propriétés
                existing = unique_entities[entity.id]
                existing.properties.update(entity.properties)
        
        print(f"\n📊 Total: {len(unique_entities)} entités uniques, {len(all_relations)} relations")
        
        return list(unique_entities.values()), all_relations
    
    def _parse_json_response(self, content: str) -> dict:
        """Parse une réponse JSON du LLM."""
        # Nettoyer le contenu
        content = content.strip()
        
        # Essayer de trouver le JSON dans le texte
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Tentative de réparation basique
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r',\s*]', ']', content)
            try:
                return json.loads(content)
            except:
                return {"entities": [], "relations": []}
    
    def _map_relation_type(self, rel_type: str) -> str:
        """Mappe un type de relation textuel vers un type standard."""
        mapping = {
            "ami": "CONNAIT",
            "amis": "CONNAIT",
            "ennemi": "ENNEMI_DE",
            "ennemis": "ENNEMI_DE",
            "famille": "FAMILLE_DE",
            "collegue": "CONNAIT",
            "collègue": "CONNAIT",
            "collegues": "CONNAIT",
            "mentor": "CONNAIT",
            "élève": "CONNAIT",
            "allie": "ALLIE_DE",
            "allié": "ALLIE_DE",
        }
        return mapping.get(rel_type.lower(), "CONNAIT")


def extract_entities_from_text(
    text: str,
    source_file: str = ""
) -> Tuple[List[ExtractedEntity], List[ExtractedRelation]]:
    """
    Fonction utilitaire pour extraire des entités d'un texte.
    
    Args:
        text: Texte à analyser
        source_file: Fichier source
        
    Returns:
        Tuple (entités, relations)
    """
    extractor = EntityExtractor()
    return extractor.extract_from_text(text, source_file)


# Test du module
if __name__ == "__main__":
    print("\n🔍 Test de l'extracteur d'entités")
    print("=" * 50)
    
    # Texte de test
    test_text = """
    Alex Chen est un technicien de maintenance du Nexus, âgé de 28 ans.
    Il a découvert récemment qu'il était une Anomalie, capable de percevoir
    et manipuler les flux de données du réseau.
    
    Maya est sa meilleure amie depuis l'enfance. Elle travaille comme
    programmeuse dans la Zone Alpha et l'aide à comprendre ses nouveaux pouvoirs.
    
    Le Consortium contrôle le Nexus et recherche activement les Anomalies
    pour les éliminer. Le Commandant Voss dirige cette traque.
    """
    
    print("\n📝 Texte de test:")
    print(test_text[:200] + "...")
    
    try:
        extractor = EntityExtractor()
        entities, relations = extractor.extract_from_text(test_text, "test.md")
        
        print(f"\n✨ Entités extraites ({len(entities)}):")
        for entity in entities:
            print(f"   [{entity.type}] {entity.name}")
            if entity.properties.get("description"):
                print(f"      → {entity.properties['description'][:50]}...")
        
        print(f"\n🔗 Relations extraites ({len(relations)}):")
        for rel in relations:
            print(f"   {rel.source_entity} --{rel.relation_type}--> {rel.target_entity}")
        
        print("\n✅ Test réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

