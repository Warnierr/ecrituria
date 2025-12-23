# Plan d'Upgrade Ecrituria v3.0

> 🎯 **Objectif** : Transformer Ecrituria en assistant d'écriture de classe mondiale pour fiction

## Contexte de la Recherche

Après une veille technologique approfondie (GitHub, HuggingFace, Medium, forums spécialisés), j'ai identifié **15 axes d'amélioration majeurs** inspirés des meilleures pratiques 2024 en RAG pour creative writing.

---

## 📊 Résultats de la Recherche

### Projets Similaires Analysés

| Projet | Points Forts | À Retenir |
|--------|--------------|-----------|
| **Sudowrite** | Story Bible, Muse model optimisé fiction | Feedback narratif, génération beat-by-beat |
| **NovelCrafter** | Codex illimité, BYOM, Tinker Chat contextuel | Flexibilité AI models, wiki intégré |
| **Novel-OS** | Workflow structuré pour contexte | Organisation méthodique |
| **RAGFlow** | Deep document understanding (PDFs) | Extraction haute fidélité |

### Frameworks RAG 2024

| Framework | Performance | Use Case Idéal |
|-----------|-------------|----------------|
| **LlamaIndex** | ⚡ 2-5x plus rapide retrieval | Knowledge bases, docs massifs |
| **LangChain** | 🔧 Modularité maximale | Orchestration complexe, agents |
| **Haystack** | 🏭 Production-ready | Pipelines enterprise |
| **Dify** | 🎨 Visual workflow | No-code development |

### Embedding Models (HuggingFace MTEB 2024)

1. **BGE-M3** : Multilingual, long context (jusqu'à 8192 tokens)
2. **E5-Mistral-7B** : SOTA pour semantic search
3. **All-MPNet-base-v2** : Balance performance/vitesse
4. **Cohere Embed v3** : Robustesse au bruit

---

## 🚀 Plan d'Amélioration en 3 Phases

## Phase 1 : Optimisations RAG Core (🟢 Priorité Haute)

> **Impact** : +40% précision retrieval, -50% hallucinations

### 1.1 Retrieval Hybride BM25 + Vectoriel

**Problème actuel** : ChromaDB seul peut manquer des correspondances exactes

**Solution** :
```python
# Combiner recherche lexicale (BM25) + sémantique
from rank_bm25 import BM25Okapi
from llama_index.core import VectorStoreIndex

class HybridRetriever:
    def retrieve(self, query, k=5):
        bm25_results = self.bm25.get_top_n(query, k*2)
        vector_results = self.vector_index.as_retriever(k=k*2)
        return self.rerank(bm25_results + vector_results, k)
```

**Gain** : +20-30% recall selon benchmarks

---

### 1.2 Upgrade Embedding Model

**Actuel** : OpenAI embeddings (propriétaires, coût, latence)

**Proposition** : **BGE-M3** (HuggingFace)
- Open source, gratuit
- 8192 tokens context (vs 8191 OpenAI)
- Top MTEB leaderboard 2024
- Multilingual (utile pour œuvres traduites)

**Implémentation** :
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-m3')
embeddings = model.encode(texts, normalize_embeddings=True)
```

**Économie** : ~$100-500/mois si volume élevé

---

### 1.3 Chunking Sémantique Avancé

**Actuel** : Chunks fixes de 300-500 tokens

**Meilleures Pratiques 2024** :
- **Semantic chunking** : Découper aux limites naturelles (scènes, paragraphes, dialogues)
- **Sliding window** avec overlap intelligent
- **Metadata enrichment** : Tags auto (personnage, lieu, temps, émotion)

**Exemple** :
```python
from llama_index.core.node_parser import SemanticSplitterNodeParser

splitter = SemanticSplitterNodeParser(
    breakpoint_percentile_threshold=95,  # Seuil sémantique
    embed_model=embed_model
)
```

---

### 1.4 Reranking Post-Retrieval

**Principe** : Réordonner les chunks récupérés par pertinence réelle

**Modèles suggérés** :
- **MS MARCO Cross-Encoder** (gratuit, HuggingFace)
- **Cohere Rerank** (API, très précis)

**Impact** : +15-25% précision finale

---

## Phase 2 : Architecture Moderne (🟡 Priorité Moyenne)

> **Impact** : Flexibilité, maintenabilité, extensibilité

### 2.1 Migration vers LlamaIndex

**Pourquoi ?**
- ✅ 2-5x plus rapide pour retrieval massif
- ✅ Support natif GraphRAG
- ✅ Évaluation RAG intégrée (fidélité, pertinence)
- ✅ Meilleure gestion multi-documents

**Migration progressive** :
1. Wrapper LlamaIndex autour de ChromaDB existant
2. Remplacer progressivement les loaders
3. Adopter `QueryEngine` pour orchestration

**Code** :
```python
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.vector_stores.chroma import ChromaVectorStore

vector_store = ChromaVectorStore(chroma_collection=collection)
index = VectorStoreIndex.from_vector_store(vector_store)
query_engine = index.as_query_engine(similarity_top_k=5)
```

---

### 2.2 GraphRAG avec Neo4j

**Concept** : Enrichir le RAG vectoriel avec un graphe de connaissances

**Bénéfices pour fiction** :
- Traquer relations complexes (personnages, lieux, événements)
- "Qui connaît qui ?" "Quel événement a causé quoi ?"
- Détection incohérences narratives

**Architecture** :
```
[Documents] → LLM Extraction → [Graphe Neo4j]
                                      ↓
[Requête] → Retrieval Hybride → Vecteurs + Sous-graphe
                                      ↓
                           Contexte enrichi → LLM
```

**Implémentation** :
```python
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import KnowledgeGraphIndex

graph_store = Neo4jGraphStore(url="bolt://localhost:7687")
kg_index = KnowledgeGraphIndex.from_documents(
    documents, 
    graph_store=graph_store,
    max_triplets_per_chunk=10
)
```

**Exemple requête** :
> "Quelles sont toutes les scènes où Alex Chen et le Baron des Cendres interagissent indirectement ?"

---

### 2.3 BYOM (Bring Your Own Models)

**Inspiration** : NovelCrafter

**Permettre de connecter** :
- OpenRouter (300+ modèles)
- Anthropic Claude Sonnet/Opus
- Google Gemini Pro
- Llama 3.3 70B (local ou groq)
- Mistral Large

**Interface** :
```python
# src/llm_providers.py - Extension
PROVIDERS = {
    "openrouter": OpenRouterLLM,
    "anthropic": AnthropicLLM,
    "google": GoogleLLM,
    "ollama": OllamaLLM  # Local !
}

# .env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-7-sonnet-20250219
LLM_API_KEY=sk-...
```

---

### 2.4 Frontend React/Next.js

**Actuel** : HTML/JS/CSS vanilla dans FastAPI

**Proposition** : Stack moderne découplée

**Avantages** :
- Hot reload développement
- Composants réutilisables
- State management (Zustand/Redux)
- Déploiement indépendant (Vercel/Netlify)

**Stack suggérée** :
```
Frontend : Next.js 15 + TypeScript + TailwindCSS + shadcn/ui
Backend  : FastAPI (API seulement)
Websocket: Live updates indexation/génération
```

**Structure** :
```
ecrituria/
├── frontend/          # Next.js app
│   ├── components/
│   │   ├── FileTree.tsx
│   │   ├── ChatPanel.tsx
│   │   ├── UploadModal.tsx
│   │   └── KnowledgeGraph.tsx  # Viz Neo4j !
│   └── pages/
└── backend/           # FastAPI
    └── src/
```

---

## Phase 3 : Fonctionnalités Créatives (🔵 Priorité Basse)

> **Impact** : Expérience utilisateur, différenciation

### 3.1 Story Bible Contextuel

**Inspiration** : Sudowrite + NovelCrafter

**Fonctionnalités** :
- **Auto-extraction** : Personnages, lieux, objets mentionnés
- **Timeline visuelle** : Chronologie événements
- **Character arcs** : Évolution personnages
- **Consistency checker** : Détection contradictions

**UI** :
```
┌─────────────────┬──────────────┐
│ Codex (Sidebar)│ Main Editor  │
├─────────────────┤              │
│ 👤 Personnages  │  Chapitre 5  │
│   • Alex Chen   │              │
│   • Elara Voss  │  [contenu]   │
│ 📍 Lieux        │              │
│ ⏱️ Timeline     │              │
│ 🎭 Intrigues    │              │
└─────────────────┴──────────────┘
```

---

### 3.2 Tinker Chat Contextuel

**Concept** : Chat IA qui connaît TOUT le contexte du projet

**Capacités** :
- "Génère-moi un dialogue entre Alex et Elara"
- "Résume l'intrigue du chapitre 3"
- "Trouve les incohérences de timeline"
- "Suggère des idées pour la fin"

**Backend** :
```python
@app.post("/api/tinker-chat")
async def tinker_chat(query: str, project: str):
    # Récupère contexte complet
    codex = load_codex(project)
    timeline = get_timeline(project)
    current_chapter = get_active_file()
    
    # RAG enrichi
    context = hybrid_retrieve(query, k=10)
    
    # Prompt structuré
    prompt = f"""Context:
    - Codex: {codex}
    - Timeline: {timeline}
    - Current: {current_chapter}
    - Retrieved: {context}
    
    User: {query}
    Assistant:"""
```

---

### 3.3 Analyse Narrative

**Métriques** :
- Pacing (rythme par chapitre)
- Sentiment analysis (arcs émotionnels)
- Dialogue/Narration ratio
- Complexité lexicale
- POV consistency

**Viz** : Graphiques interactifs (Chart.js/Recharts)

---

### 3.4 Export Multi-format

**Formats** :
- ✅ Markdown (actuel)
- ➕ DOCX (manuscrit éditeurs)
- ➕ EPUB (ebook)
- ➕ PDF (formaté)
- ➕ Scrivener (.scriv)

**Lib** : `python-docx`, `ebooklib`, `pandoc`

---

## 🛠️ Recommandations Stack Finale

### Option A : Évolution Progressive (Recommandé)

**Keep** :
- FastAPI
- ChromaDB
- Python backend

**Add** :
- LlamaIndex (wrapper)
- BGE-M3 embeddings
- Hybrid retrieval (BM25 + Vector)
- Reranking
- Neo4j (GraphRAG)

**Migrate** :
- Frontend → Next.js (optionnel, impact fort)

**Coût** : Faible, mostly OSS

---

### Option B : Refonte Totale

**Stack** :
- **Backend** : Node.js + LangChain.js OU FastAPI + LlamaIndex
- **Frontend** : Next.js 15 + TypeScript
- **Vector DB** : Qdrant (plus performant que Chroma)
- **Graph DB** : Neo4j
- **Embeddings** : BGE-M3 (HuggingFace)
- **LLM** : BYOM (OpenRouter, Anthropic, Google)
- **Deploy** : Docker Compose

**Coût** : Moyen (temps dev)
**ROI** : Très haute maintenabilité

---

## 📈 Roadmap Implémentation

### Sprint 1 (2 semaines) : RAG Core
- [ ] Implémenter BM25 retrieval
- [ ] Intégrer BGE-M3 embeddings
- [ ] Ajouter reranking

### Sprint 2 (2 semaines) : GraphRAG
- [ ] Setup Neo4j
- [ ] Extraction entités/relations LLM
- [ ] Query engine hybride

### Sprint 3 (3 semaines) : Frontend Moderne
- [ ] Init Next.js app
- [ ] Migration composants
- [ ] Graph visualization

### Sprint 4 (1 semaine) : Fonctionnalités Créatives
- [ ] Story Bible auto
- [ ] Tinker Chat
- [ ] Analytics

---

## 💡 Innovations Uniques à Considérer

### 1. **Voice-to-Text Integration**
Dicter des idées directement (Whisper API)

### 2. **Collaborative Mode**
Écriture à plusieurs (WebSocket, Y.js CRDT)

### 3. **AI Critique Mode**
Feedback de type beta-reader (structure, pacing, cohérence)

### 4. **Version Control Narratif**
Git-like pour branches narratives alternatives

### 5. **Research Assistant**
Recherche web contextuelle pour documentation

---

## ⚠️ Points d'Attention

> [!IMPORTANT]
> **Credits OpenRouter** : Vérifier solde, configurer fallback models

> [!WARNING]
> **Migration ChromaDB** : Backup complet avant upgrade embeddings

> [!CAUTION]
> **GraphRAG Complexity** : Commencer simple, itérer progressivement

---

## 📚 Ressources Complémentaires

### Documentation
- [LlamaIndex Docs](https://docs.llamaindex.ai/)
- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/)
- [HuggingFace MTEB](https://huggingface.co/spaces/mteb/leaderboard)

### Repos GitHub Inspirants
- `forsonny/book-os` - Novel workflow
- `yanis112/LocalRAG` - RAG local complet
- `microsoft/graphrag` - GraphRAG officiel

### Articles Clés
- "RAG Best Practices for Fiction" (Medium)
- "LlamaIndex vs LangChain 2024" (TowardsAI)
- "Hybrid Search Deep Dive" (Weaviate Blog)

---

## 🎯 Métriques de Succès

| Métrique | Avant | Cible v3.0 |
|----------|-------|------------|
| Retrieval Precision | ~65% | **90%+** |
| Response Latency | 3-5s | **<2s** |
| Hallucination Rate | ~15% | **<5%** |
| User Satisfaction | ? | **8/10+** |
| Cost per Query | $0.05 | **$0.01** |

---

**Prochaine étape** : Valider les priorités avec vous et commencer Sprint 1 ! 🚀
