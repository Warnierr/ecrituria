# 📋 Changelog

Historique des versions de l'Assistant Fiction RAG - Écrituria.

## [2.0.0] - 2025-12-16

### 🚀 Version majeure - Architecture v2

#### ✨ Phase 1: Fondations améliorées

- **Recherche hybride BM25 + Vecteurs** (`src/hybrid_search.py`)
  - Combine recherche lexicale (mots-clés) et sémantique (sens)
  - Poids configurables (défaut: 40% BM25, 60% vecteurs)
  - Meilleure précision sur les noms propres et termes techniques

- **Reranking avec Cross-Encoder** (`src/reranker.py`)
  - Réordonne les résultats par pertinence réelle
  - Modèles: fast, accurate, multilingual
  - Amélioration significative de la qualité des réponses

- **Indexation incrémentale** (`src/indexer.py`)
  - Détection automatique des fichiers modifiés/ajoutés/supprimés
  - Mise à jour partielle de l'index (plus besoin de tout reconstruire)
  - Stockage des hash MD5 dans SQLite

- **Support PDF et DOCX** (`src/loaders.py`)
  - Chargement des fichiers PDF (pypdf)
  - Chargement des fichiers Word (python-docx)
  - Détection automatique du format

#### 🔗 Phase 2: Graphe de connaissances (GraphRAG)

- **Client Neo4j** (`src/graph/neo4j_client.py`)
  - Support Neo4j Desktop et Aura (cloud)
  - Mode simulation en mémoire si Neo4j non installé
  - Schéma: Personnage, Lieu, Événement, Thème, Objet
  - Relations: CONNAIT, VIENT_DE, PARTICIPE_A, etc.

- **Extraction automatique d'entités** (`src/graph/entity_extractor.py`)
  - Extraction via LLM des personnages, lieux, événements
  - Parsing des fiches personnages structurées
  - Construction automatique du graphe

- **GraphRAG** (`src/graph/graph_rag.py`)
  - Combine recherche vectorielle + traversée du graphe
  - Contexte enrichi par les relations entre entités
  - Meilleure compréhension des connexions narratives

#### 🤖 Phase 3: Agents spécialisés

- **Architecture multi-agents** (`src/agents/`)
  - `RechercheurAgent`: Trouve l'information dans docs + graphe
  - `CoherenceAgent`: Détecte les incohérences narratives
  - `CreatifAgent`: Génère du contenu (scènes, dialogues)

- **Orchestrateur** (`src/agents/orchestrator.py`)
  - Routing automatique selon le type de question
  - Workflows prédéfinis (simple, creative, analysis)
  - Support LangGraph optionnel

#### 🏠 Phase 4: Modèles locaux

- **Multi-provider LLM** (`src/llm_providers.py`)
  - OpenRouter (cloud, multi-modèles)
  - OpenAI (direct)
  - Ollama (local: Llama3, Mistral, etc.)

- **Embeddings locaux**
  - sentence-transformers (paraphrase-multilingual)
  - Mode hors-ligne complet possible

#### 🎨 Phase 5: Interface web v2

- **Nouvelle interface** (`src/server.py`)
  - Design moderne dark mode
  - Sélection du mode (GraphRAG, Agents)
  - Sélection du modèle LLM
  - Statistiques en temps réel

- **API enrichie**
  - `/api/graph/{project}` - Données du graphe
  - `/api/stats/{project}` - Statistiques
  - `/api/graph/populate/{project}` - Peupler le graphe

#### 🛠️ Nouveaux fichiers

```
src/
├── hybrid_search.py      # Recherche BM25 + vecteurs
├── reranker.py           # Cross-encoder reranking
├── llm_providers.py      # Multi-provider (OpenRouter, Ollama)
├── graph/
│   ├── __init__.py
│   ├── neo4j_client.py   # Client Neo4j
│   ├── entity_extractor.py # Extraction d'entités
│   └── graph_rag.py      # GraphRAG
├── agents/
│   ├── __init__.py
│   ├── base_agent.py     # Classe de base
│   ├── rechercheur.py    # Agent recherche
│   ├── coherence.py      # Agent cohérence
│   ├── creatif.py        # Agent créatif
│   └── orchestrator.py   # Orchestrateur
└── utils/
    ├── __init__.py
    ├── file_hash.py      # Hash MD5 pour indexation
    └── markdown_parser.py # Parsing Markdown avancé
```

#### 📦 Nouvelles dépendances

```
rank-bm25>=0.2.2          # Recherche BM25
sentence-transformers>=2.2.0  # Reranking + embeddings locaux
neo4j>=5.15.0             # Client Neo4j
langgraph>=0.2.0          # Orchestration agents
pypdf>=3.17.0             # Lecture PDF
python-docx>=1.1.0        # Lecture DOCX
```

---

## [1.0.0] - 2025-11-29

### 🎉 Version initiale

#### ✨ Fonctionnalités

- **Indexation vectorielle** : Transformation automatique de vos documents en base de connaissances
- **Chat interactif** : Interface CLI pour dialoguer avec votre univers
- **Recherche sémantique** : Trouvez des informations par sens, pas par mots-clés
- **Génération cohérente** : Créez du contenu respectant votre univers
- **Multi-projets** : Gérez plusieurs univers de fiction simultanément
- **Traçabilité des sources** : Voyez d'où viennent les informations

#### 🔧 Modules

- `src/loaders.py` : Chargement et découpage des documents
- `src/indexer.py` : Indexation dans ChromaDB
- `src/rag.py` : Moteur RAG complet
- `src/cli.py` : Interface utilisateur

#### 📚 Documentation

- `README.md` : Documentation principale
- `GUIDE_UTILISATION.md` : Guide détaillé d'utilisation
- `DEMARRAGE_RAPIDE.md` : Démarrage en 5 minutes
- `INSTALLATION.md` : Installation pas à pas
- `ARCHITECTURE.md` : Architecture technique

#### 🎨 Exemple

- Projet "Anomalie 2084" complet avec :
  - Worldbuilding (lore)
  - Fiches personnages
  - Arc narratif (saison 1)
  - Premier chapitre
  - Notes de travail

#### 🛠️ Utilitaires

- Scripts `.bat` pour Windows (indexation et lancement)
- Configuration via `settings.yaml`
- Template `.env` pour la configuration

#### 🏗️ Stack technique

- Python 3.10+
- LangChain pour l'orchestration RAG
- ChromaDB pour le stockage vectoriel
- OpenAI pour les embeddings et la génération
- Interface CLI simple et claire

---

## Roadmap future

### [2.1.0] - Visualisation avancée
- [ ] Graphe interactif des relations (D3.js/Cytoscape)
- [ ] Timeline interactive des événements
- [ ] Éditeur Markdown intégré
- [ ] Export des conversations

### [2.2.0] - Analyse narrative
- [ ] Détection automatique d'incohérences
- [ ] Analyse de la structure des arcs
- [ ] Suggestions de développement
- [ ] Statistiques narratives

### [3.0.0] - Collaboration
- [ ] Multi-utilisateurs
- [ ] Versionnage intégré
- [ ] Commentaires et annotations
- [ ] Partage de projets

---

**Note** : Ce changelog est mis à jour à chaque version majeure du projet.
