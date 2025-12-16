# 🏗️ Architecture du système

Ce document décrit l'architecture technique de l'Assistant Fiction RAG.

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR                               │
│                  (Écrivain de fiction)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Édite/Consulte
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              DOCUMENTS DE FICTION                            │
│   data/mon_projet/{lore,personnages,chapitres,...}           │
│              (Fichiers .md / .txt)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ 1. Indexation
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   INDEXEUR                                   │
│              (src/indexer.py)                                │
│                                                              │
│  1. Charge les documents (loaders.py)                       │
│  2. Découpe en chunks (RecursiveCharacterTextSplitter)      │
│  3. Crée les embeddings (OpenAI Embeddings)                 │
│  4. Stocke dans ChromaDB                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Sauvegarde
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            BASE VECTORIELLE LOCALE                           │
│                  (ChromaDB)                                  │
│              db/mon_projet/                                  │
│                                                              │
│  Contient les embeddings + métadonnées                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ 2. Utilisation
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              INTERFACE CLI                                   │
│              (src/cli.py)                                    │
│                                                              │
│  - Chat interactif                                          │
│  - Commandes spéciales (/search, /sources)                 │
│  - Affichage formaté                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Question utilisateur
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                MOTEUR RAG                                    │
│               (src/rag.py)                                   │
│                                                              │
│  ┌────────────────────────────────────────────────┐        │
│  │  1. RETRIEVAL (Récupération)                   │        │
│  │     - Vectorise la question                    │        │
│  │     - Recherche similarité dans ChromaDB       │        │
│  │     - Récupère les k chunks pertinents         │        │
│  └────────────────┬───────────────────────────────┘        │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐        │
│  │  2. AUGMENTATION (Enrichissement)              │        │
│  │     - Construit le contexte avec chunks        │        │
│  │     - Ajoute le prompt spécialisé fiction      │        │
│  │     - Prépare l'entrée pour le LLM             │        │
│  └────────────────┬───────────────────────────────┘        │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐        │
│  │  3. GENERATION (Création)                      │        │
│  │     - Appel API OpenAI (GPT-4, etc.)           │        │
│  │     - Génération de la réponse                 │        │
│  │     - Retour au format approprié               │        │
│  └────────────────────────────────────────────────┘        │
│                                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Réponse contextuelle
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   UTILISATEUR                                │
│              Reçoit une réponse informée                     │
│           par son propre univers narratif                    │
└─────────────────────────────────────────────────────────────┘
```

## Composants détaillés

### 1. Loaders (src/loaders.py)

**Responsabilité** : Charger et préparer les documents

**Fonctions clés** :
- `load_project_documents()` : Parcourt récursivement le dossier projet
- `split_documents()` : Découpe en chunks avec chevauchement

**Technologies** :
- LangChain TextLoader
- RecursiveCharacterTextSplitter

### 2. Indexer (src/indexer.py)

**Responsabilité** : Créer et mettre à jour l'index vectoriel

**Workflow** :
```
Documents → Chunks → Embeddings → ChromaDB
```

**Technologies** :
- OpenAI Embeddings API (text-embedding-3-small)
- ChromaDB pour le stockage

### 3. RAG Engine (src/rag.py)

**Responsabilité** : Orchestrer le processus RAG complet

**Composants** :

#### Retriever
```python
vectordb.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)
```
- Recherche de similarité cosine
- Retourne les k passages les plus pertinents

#### Prompt Template
```python
FICTION_PROMPT_TEMPLATE = """
Tu es un assistant créatif...
Context: {context}
Question: {question}
"""
```
- Spécialisé pour l'écriture de fiction
- Encourage la cohérence narrative

#### Chain
```python
RetrievalQA.from_chain_type(
    llm=ChatOpenAI,
    retriever=retriever,
    chain_type="stuff"
)
```
- Type "stuff" : met tout le contexte dans un seul prompt
- Alternative possible : "map_reduce" pour beaucoup de documents

### 4. CLI (src/cli.py)

**Responsabilité** : Interface utilisateur

**Fonctionnalités** :
- Boucle interactive de chat
- Commandes spéciales (`/search`, `/sources`, `/help`)
- Affichage formaté avec emojis et couleurs
- Gestion des erreurs

## Flux de données

### Flux d'indexation

```
1. Utilisateur modifie data/projet/chapitre1.md
2. Utilisateur lance: python -m src.indexer projet
3. Loaders charge tous les .md/.txt
4. Documents découpés en chunks (1000 chars, overlap 150)
5. Chaque chunk → embedding via OpenAI API
6. Embeddings + métadonnées → ChromaDB (db/projet/)
7. Index prêt à l'utilisation
```

### Flux de requête

```
1. Utilisateur pose question: "Qui est Alex ?"
2. CLI transmet à RAG engine
3. Question → embedding via OpenAI API
4. Recherche similarité dans ChromaDB
5. Récupération des 5 chunks les plus proches
6. Construction du prompt avec contexte
7. Appel ChatGPT avec prompt enrichi
8. Réponse générée retournée à CLI
9. Affichage formaté à l'utilisateur
```

## Structure des données

### Document Chunk

```python
{
    "page_content": "Texte du chunk...",
    "metadata": {
        "source": "data/projet/personnages/alex.md",
        "relative_path": "personnages/alex.md",
        "file_name": "alex.md"
    }
}
```

### Embedding Vector

- Dimension : 1536 (OpenAI text-embedding-3-small)
- Format : Liste de floats
- Stocké dans ChromaDB avec le chunk

### ChromaDB Collection

```python
{
    "name": "nom_projet",
    "embeddings": [...],  # Vecteurs
    "documents": [...],   # Textes originaux
    "metadatas": [...],   # Métadonnées
    "ids": [...]          # Identifiants uniques
}
```

## Configuration

### settings.yaml

```yaml
indexing:
  chunk_size: 1000       # Taille optimale pour narratif
  chunk_overlap: 150     # Évite coupures abruptes

rag:
  model: "gpt-4o-mini"   # Balance qualité/coût
  temperature: 0.7       # Créatif mais cohérent
  k_results: 5           # Contexte suffisant
```

### Variables d'environnement

```bash
OPENAI_API_KEY=sk-...   # Obligatoire
DEFAULT_MODEL=...       # Optionnel
DEFAULT_TEMPERATURE=... # Optionnel
```

## Optimisations possibles

### Performance

1. **Cache des embeddings** : Ne pas recréer si contenu inchangé
2. **Indexation incrémentale** : Mettre à jour seulement les fichiers modifiés
3. **Batch processing** : Traiter plusieurs chunks en parallèle

### Qualité

1. **Hybrid search** : Combiner recherche vectorielle et BM25
2. **Reranking** : Réordonner les résultats avec un modèle dédié
3. **Metadata filtering** : Filtrer par type de document avant recherche

### Scalabilité

1. **Modèles locaux** : Ollama, LMStudio pour éviter coûts API
2. **Base vectorielle distante** : Pinecone, Weaviate pour gros projets
3. **Chunking adaptatif** : Taille variable selon type de document

## Sécurité et confidentialité

### Données locales
- ✅ Documents stockés localement
- ✅ Base vectorielle locale (ChromaDB)

### Données externes
- ⚠️ Embeddings créés via OpenAI API
- ⚠️ Questions + contexte envoyés à OpenAI
- ⚠️ Pas de stockage par OpenAI (selon leurs conditions)

### Pour une confidentialité totale
- Utiliser Ollama ou LMStudio
- Modèles d'embeddings locaux (sentence-transformers)
- Tout reste sur votre machine

## Dépendances

```
langchain          # Orchestration RAG
langchain-openai   # Intégration OpenAI
langchain-community # Loaders et utils
chromadb          # Base vectorielle
openai            # API client
tiktoken          # Tokenization
python-dotenv     # Config
pyyaml            # Settings
```

## Extensibilité

### Ajouter un nouveau type de document

```python
# Dans loaders.py
from langchain_community.document_loaders import PDFLoader

if path.suffix == ".pdf":
    loader = PDFLoader(str(path))
```

### Changer de LLM

```python
# Dans rag.py
from langchain_community.llms import Ollama

llm = Ollama(model="llama2")
```

### Ajouter une interface web

```python
# Nouveau fichier: src/server.py
from fastapi import FastAPI
from src.rag import ask

app = FastAPI()

@app.post("/ask")
def query(project: str, question: str):
    return {"answer": ask(project, question)}
```

---

Cette architecture est conçue pour être :
- **Simple** : Facile à comprendre et modifier
- **Modulaire** : Chaque composant est indépendant
- **Extensible** : Facile d'ajouter des fonctionnalités
- **Efficace** : Performant pour des projets de taille raisonnable


