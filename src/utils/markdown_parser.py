"""
Parser Markdown avancé avec support du frontmatter YAML.
Utilitaire pour l'extraction d'entités et métadonnées.
"""
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    """Document Markdown parsé avec métadonnées."""
    content: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    headers: List[Dict[str, Any]] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """
    Extrait le frontmatter YAML d'un document Markdown.
    
    Le frontmatter doit être au début du fichier, entre deux lignes '---':
    ---
    title: Mon titre
    tags: [tag1, tag2]
    ---
    Contenu...
    
    Args:
        content: Contenu du fichier Markdown
        
    Returns:
        Tuple (frontmatter_dict, contenu_sans_frontmatter)
    """
    frontmatter = {}
    
    # Pattern pour le frontmatter YAML
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            frontmatter = {}
        content = content[match.end():]
    
    return frontmatter, content


class MarkdownParser:
    """
    Parser Markdown avancé pour extraire:
    - Frontmatter YAML
    - Titres et structure
    - Liens (wiki-style [[...]] et standard)
    - Tags (#tag)
    """
    
    # Patterns regex
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    WIKI_LINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
    MD_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    TAG_PATTERN = re.compile(r'(?:^|\s)#([a-zA-Z0-9_-]+)')
    
    def __init__(self):
        pass
    
    def parse(self, content: str) -> ParsedDocument:
        """
        Parse un document Markdown complet.
        
        Args:
            content: Contenu Markdown
            
        Returns:
            ParsedDocument avec toutes les métadonnées
        """
        # Extraire le frontmatter
        frontmatter, body = parse_frontmatter(content)
        
        # Extraire les headers
        headers = self._extract_headers(body)
        
        # Extraire le titre (premier H1 ou du frontmatter)
        title = frontmatter.get('title')
        if not title and headers:
            for h in headers:
                if h['level'] == 1:
                    title = h['text']
                    break
        
        # Extraire les liens
        links = self._extract_links(body)
        
        # Extraire les tags (du frontmatter ou du contenu)
        tags = frontmatter.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        tags.extend(self._extract_tags(body))
        tags = list(set(tags))  # Dédupliquer
        
        return ParsedDocument(
            content=body,
            frontmatter=frontmatter,
            title=title,
            headers=headers,
            links=links,
            tags=tags
        )
    
    def parse_file(self, file_path: Path) -> ParsedDocument:
        """
        Parse un fichier Markdown.
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            ParsedDocument
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        doc = self.parse(content)
        
        # Ajouter le nom du fichier comme titre par défaut
        if not doc.title:
            doc.title = file_path.stem
        
        return doc
    
    def _extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extrait tous les titres avec leur niveau."""
        headers = []
        for match in self.HEADER_PATTERN.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            headers.append({
                'level': level,
                'text': text,
                'position': match.start()
            })
        return headers
    
    def _extract_links(self, content: str) -> List[str]:
        """Extrait tous les liens (wiki-style et markdown)."""
        links = []
        
        # Liens wiki-style [[...]]
        for match in self.WIKI_LINK_PATTERN.finditer(content):
            links.append(match.group(1))
        
        # Liens markdown standard
        for match in self.MD_LINK_PATTERN.finditer(content):
            link_text = match.group(2)
            # Ignorer les liens externes
            if not link_text.startswith(('http://', 'https://', 'mailto:')):
                links.append(link_text)
        
        return list(set(links))
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extrait les tags #tag du contenu."""
        return list(set(self.TAG_PATTERN.findall(content)))
    
    def extract_sections(self, content: str) -> Dict[str, str]:
        """
        Découpe le document en sections par titre.
        
        Returns:
            Dict titre -> contenu de la section
        """
        sections = {}
        current_title = "Introduction"
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            match = self.HEADER_PATTERN.match(line)
            if match:
                # Sauvegarder la section précédente
                if current_content:
                    sections[current_title] = '\n'.join(current_content).strip()
                
                current_title = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Dernière section
        if current_content:
            sections[current_title] = '\n'.join(current_content).strip()
        
        return sections
    
    def extract_character_info(self, content: str) -> Dict[str, Any]:
        """
        Extrait les informations d'une fiche personnage.
        Format attendu avec des sections:
        - Identité
        - Description
        - Personnalité
        - Capacités
        - Relations
        - etc.
        
        Returns:
            Dict avec les informations extraites
        """
        doc = self.parse(content)
        sections = self.extract_sections(doc.content)
        
        info = {
            'name': doc.title or doc.frontmatter.get('name'),
            'tags': doc.tags,
            'sections': sections,
            'metadata': doc.frontmatter
        }
        
        # Chercher des patterns spécifiques
        for key in ['role', 'age', 'occupation', 'species', 'location']:
            if key in doc.frontmatter:
                info[key] = doc.frontmatter[key]
        
        return info


# Fonctions utilitaires
def parse_markdown_file(file_path: Path) -> ParsedDocument:
    """Fonction utilitaire pour parser un fichier."""
    parser = MarkdownParser()
    return parser.parse_file(file_path)


def extract_all_links(directory: Path, extensions: List[str] = None) -> Dict[str, List[str]]:
    """
    Extrait tous les liens de tous les fichiers d'un répertoire.
    
    Args:
        directory: Répertoire à scanner
        extensions: Extensions à inclure (défaut: .md)
        
    Returns:
        Dict fichier -> liste de liens
    """
    if extensions is None:
        extensions = ['.md']
    
    parser = MarkdownParser()
    all_links = {}
    
    for ext in extensions:
        for file_path in directory.rglob(f'*{ext}'):
            try:
                doc = parser.parse_file(file_path)
                rel_path = str(file_path.relative_to(directory))
                all_links[rel_path] = doc.links
            except Exception:
                continue
    
    return all_links


# Test du module
if __name__ == "__main__":
    print("\n📝 Test du parser Markdown")
    print("=" * 50)
    
    # Document de test avec frontmatter
    test_doc = """---
title: Alex Chen
tags: [personnage, protagoniste]
role: Technicien
---

# Alex Chen

## Identité
Alex est un technicien de maintenance du Nexus.

## Capacités
- Perception des flux de données
- Manipulation du [[Nexus]]

## Relations
Il est ami avec [[Maya]] depuis l'enfance.

#anomalie #héros
"""
    
    parser = MarkdownParser()
    doc = parser.parse(test_doc)
    
    print(f"\n📄 Titre: {doc.title}")
    print(f"🏷️  Tags: {doc.tags}")
    print(f"🔗 Liens: {doc.links}")
    print(f"📋 Frontmatter: {doc.frontmatter}")
    print(f"\n📚 Headers:")
    for h in doc.headers:
        indent = "  " * (h['level'] - 1)
        print(f"   {indent}H{h['level']}: {h['text']}")
    
    print("\n📑 Sections:")
    sections = parser.extract_sections(doc.content)
    for title, content in sections.items():
        preview = content[:50].replace('\n', ' ') + "..."
        print(f"   • {title}: {preview}")
    
    print("\n✅ Test réussi!")

