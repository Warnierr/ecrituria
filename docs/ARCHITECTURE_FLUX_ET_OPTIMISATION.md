# 🏗️ Architecture, Flux et Optimisation - Ecrituria v2.1

## 📊 Vue d'ensemble : Comment tout interagit

### Le Grand Pipeline (de VOUS à l'IA)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         VOUS (Utilisateur)                           │
│                 Édite vos documents dans data/                       │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
         ╔═══════════════════════════════════════════════════╗
         ║        Phase 1 : INDEXATION (une fois)            ║
         ║      python -m src.indexer anomalie2084           ║
         ╚═══════════════════════════════════════════════════╝
                                 │
        ┌────────────────────────┴────────────────────────┐
        │                                                  │
        ▼                                                  ▼
┌─────────────────┐                             ┌──────────────────┐
│ VOS DOCUMENTS   │                             │  EMBEDDINGS API  │
│ (data/*.md)     │ ──[Chunking]──────────────> │  (OpenRouter)    │
│                 │                             │  text-embed-*    │
└─────────────────┘                             └────────┬─────────┘
                                                         │
                                                         ▼
                                              ┌──────────────────────┐
                                              │  BASE VECTORIELLE    │
                                              │  ChromaDB (locale)   │
                                              │  db/anomalie2084/    │
                                              └──────────┬───────────┘
                                                         │
                                                         │
         ╔═══════════════════════════════════════════════════════════╗
         ║         Phase 2 : UTILISATION (à chaque question)         ║
         ║           Interface Web : http://localhost:8000           ║
         ╚═══════════════════════════════════════════════════════════╝
                                 │
                    [Vous posez une question]
                                 │
                                 ▼
         ┌───────────────────────────────────────────────┐
         │         SERVEUR WEB (FastAPI)                 │
         │         src/server.py (port 8000)             │
         └────────────────────┬──────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────────────┐
         │           MOTEUR RAG (src/rag.py)              │
         │                                                │
         │   ┌──────────────────────────────────┐        │
         │   │ ÉTAPE 1: RETRIEVAL (~1-2s)       │        │
         │   │ --------------------------------- │        │
         │   │ Votre question → Embedding       │ ────┐  │
         │   │ Recherche dans ChromaDB          │     │  │
         │   │ • Vectorielle (similarité)       │     │  │
         │   │ • + BM25 (mots-clés)            │     │  │
         │   │ Récupère ~15 chunks              │     │  │
         │   └──────────────────────────────────┘     │  │
         │                                             │  │
         │   ┌──────────────────────────────────┐     │  │
         │   │ ÉTAPE 2: RERANKING (~0.5-2s)    │ <───┘  │
         │   │ --------------------------------- │        │
         │   │ Cross-Encoder local              │        │
         │   │ Réordonne les 15 → Top 5         │        │
         │   └──────────────────────────────────┘        │
         │                │                               │
         │                ▼                               │
         │   ┌──────────────────────────────────┐        │
         │   │ ÉTAPE 3: AUGMENTATION (~0.1s)   │        │
         │   │ --------------------------------- │        │
         │   │ Construit le prompt avec:        │        │
         │   │ • Contexte (5 chunks)            │        │
         │   │ • Instructions système           │        │
         │   │ • Votre question                 │        │
         │   └──────────────────────────────────┘        │
         │                │                               │
         │                ▼                               │
         │   ┌──────────────────────────────────┐        │
         │   │ ÉTAPE 4: GÉNÉRATION (~2-8s) ⚠️   │        │
         │   │ --------------------------------- │        │
         │   │ Appel LLM (OpenRouter)           │        │
         │   │ → gpt-4o-mini par défaut         │        │
         │   │ Génération de la réponse         │        │
         │   └──────────────────────────────────┘        │
         └────────────────────┬───────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────────────┐
         │            INTERFACE WEB                       │
         │         Affiche la réponse + sources          │
         └────────────────────────────────────────────────┘
                              │
                              ▼
                       VOUS (lisez la réponse)
```

---

## 🔍 Pourquoi l'IA prend du temps ? (Analyse de latence)

### Temps typiques par étape (total: ~4-10s)

| Étape | Temps | % du total | Optimisable? |
|-------|-------|------------|--------------|
| **1. Chargement index** (1ère fois) | 0.5-1s | 10% | ✅ Oui (caching) |
| **2. Recherche vectorielle** | 0.3-0.8s | 8% | ✅ Oui (désactiver hybrid) |
| **3. Recherche BM25** (si hybride) | +0.5-1s | 12% | ✅ Oui (désactiver) |
| **4. Reranking** (si activé) | 0.5-2s | 15% | ✅ Oui (désactiver) |
| **5. Génération LLM** | **2-8s** | **60%** | ⚠️ Principal bottleneck |
| **6. Réseau OpenRouter** | variable | 10% | ✅ Oui (Ollama local) |

### 🚨 Le vrai coupable : Le LLM (Étape 4)

**Le modèle LLM représente 60-70% du temps total !**

Actuellement: `gpt-4o-mini` via OpenRouter
- ✅ Qualité: Excellente
- ⚠️ Vitesse: 2-8 secondes
- 💰 Coût: ~$0.0001/requête

---

## ⚡ Solutions pour accélérer (de la plus efficace à la moins)

### Solution 1 : Changer de modèle LLM (Impact: -40 à -60%)

**Modèles rapides recommandés:**

```yaml
# Dans settings.yaml
rag:
  model: "meta-llama/llama-3.1-8b-instruct"  # ~1-2s au lieu de 4-8s
  # ou
  model: "google/gemini-flash-1.5"  # Ultra rapide
  # ou  
  model: "anthropic/claude-instant-1.2"  # Bon compromis
```

**Avantages:**
- ⚡ Réduction de 40-60% du temps total
- 🎯 Change 1 ligne de config
- ✅ Garde toutes les fonctionnalités

**Inconvénients:**
- Qualité légèrement moindre (mais souvent acceptable)

---

### Solution 2 : Désactiver le Reranking (Impact: -20 à -30%)

Le reranking améliore la qualité mais ajoute 0.5-2s.

**Comment désactiver:**

```yaml
# Dans config/settings.yaml
rag:
  reranking:
    enabled: false  # ← Mettez à false
```

**Ou via l'interface web:**
1. Décoche "Utiliser le reranking"

**Quand désactiver:**
- ✅ Pour des questions simples
- ✅ Si la vitesse est prioritaire
- ❌ Pour des questions complexes nécessitant précision

---

### Solution 3 : Désactiver la recherche hybride (Impact: -10 à -15%)

Le BM25 ajoute ~0.5-1s pour peu de gain sur les questions sémantiques.

```yaml
# Dans config/settings.yaml
rag:
  hybrid_search:
    enabled: false  # ← Mettez à false
```

**Quand désactiver:**
- ✅ Questions sémantiques ("Quelle est la personnalité d'Alex?")
- ❌ Questions avec noms propres ("Trouve toutes les mentions de Neo-Shanghai")

---

### Solution 4 : Réduire k (nombre de documents) (Impact: -5 à -10%)

```yaml
# Dans config/settings.yaml
rag:
  k_results: 3  # Au lieu de 5
```

**Avantages:**
- Moins de texte à traiter par le LLM
- Réponses plus rapides

**Inconvénients:**
- Contexte potentiellement incomplet

---

### Solution 5 : Utiliser Ollama en local (Impact: variable)

**Installation:**
```bash
# 1. Installer Ollama : https://ollama.ai
# 2. Télécharger un modèle
ollama pull llama3.1:8b

# 3. Vérifier qu'il tourne
ollama list
```

**Configuration:**
```yaml
# Dans config/settings.yaml
llm:
  default_provider: "ollama"
  prefer_local: true
  
  ollama:
    base_url: "http://localhost:11434"
    default_model: "llama3.1:8b"
```

**Avantages:**
- ✅ Zéro latence réseau
- ✅ Gratuit (pas de coûts API)
- ✅ 100% privé
- ⚡ Peut être plus rapide (si bon GPU)

**Inconvénients:**
- Nécessite bon CPU/GPU
- Qualité variable selon modèle

---

## 📂 Fichiers obsolètes à nettoyer

J'ai identifié plusieurs fichiers obsolètes/redondants :

### À supprimer du dossier racine `Ecrituria/`:
```
❌ INTERFACE_WEB_CREEE.md      → Obsolète (doc de développement)
❌ LANCEMENT_REUSSI.md         → Obsolète (doc de développement)
❌ SYSTEME_OPERATIONNEL.md     → Obsolète (redondant avec SUCCES_COMPLET.md)
✅ RECAPITULATIF_PROJET.md     → GARDER (utile)
```

### À supprimer de `fiction-assistant/`:
```
❌ CORRECTIFS_APPLIQUES.md     → Obsolète (vieux changelog)
❌ INTERFACE_WEB_LANCEE.md     → Obsolète (doc de dev)
❌ RAPPORT_TEST.md             → Obsolète (vieux tests)
❌ SUCCES_COMPLET.md           → Obsolète (doc de dev)
❌ TEST_DOCKER.md              → Obsolète (test ancien)
❌ DEMARRAGE_RAPIDE.md         → Redondant avec LISEZMOI_DABORD.md

✅ GARDER:
  ✓ LISEZMOI_DABORD.md         → Guide principal
  ✓ README.md                  → Documentation officielle
  ✓ ARCHITECTURE.md            → Documentation technique
  ✓ GUIDE_UTILISATION.md       → Guide utilisateur
  ✓ INSTALLATION.md            → Instructions d'installation
  ✓ CHANGELOG.md               → Historique
  ✓ DOCKER.md                  → Docker docs
```

---

## 🔧 Configuration optimale recommandée

### Pour la **VITESSE** (réponses en ~2-3s)

```yaml
# config/settings.yaml
rag:
  model: "meta-llama/llama-3.1-8b-instruct"  # Modèle rapide
  temperature: 0.7
  k_results: 3  # Moins de documents
  
  hybrid_search:
    enabled: false  # Désactivé
  
  reranking:
    enabled: false  # Désactivé

llm:
  default_provider: "openrouter"  # Ou "ollama" si installé
```

### Pour la **QUALITÉ** (réponses en ~5-8s)

```yaml
# config/settings.yaml
rag:
  model: "openai/gpt-4o-mini"  # Modèle de qualité
  temperature: 0.7
  k_results: 5
  
  hybrid_search:
    enabled: true  # Activé
    bm25_weight: 0.4
    vector_weight: 0.6
  
  reranking:
    enabled: true  # Activé
    model: "fast"
```

### Pour l'**ÉQUILIBRE** (réponses en ~3-4s)

```yaml
# config/settings.yaml
rag:
  model: "anthropic/claude-3-haiku"  # Bon compromis
  temperature: 0.7
  k_results: 4
  
  hybrid_search:
    enabled: true  # Activé
  
  reranking:
    enabled: false  # Désactivé pour vitesse
```

---

## 🎯 Résumé des données qui circulent

### Données LOCALES (sur votre PC)
```
✅ Vos documents (.md)          → data/anomalie2084/
✅ Base vectorielle              → db/anomalie2084/ (ChromaDB)
✅ Graphe de connaissances       → src/graph_simulator.py (en mémoire)
✅ Configuration                 → config/settings.yaml
✅ Clé API                       → .env
```

### Données EXTERNES (envoyées à OpenRouter)
```
⚠️ Votre question                → OpenRouter API
⚠️ Les 5 chunks de contexte      → OpenRouter API
⚠️ Le prompt système             → OpenRouter API

❌ PAS envoyé:
   ✓ Vos documents complets
   ✓ Votre base vectorielle
   ✓ Votre graphe
```

**Note de confidentialité:** Si vous voulez **100% local**, utilisez Ollama.

---

## 🚀 Plan d'action immédiat

### Étape 1 : Nettoyage (maintenant)
Je vais supprimer les fichiers obsolètes pour vous.

### Étape 2 : Diagnostic performance
Exécutez ceci pour voir où sont les lenteurs:
```bash
python -m src.diagnose_performance anomalie2084 "Qui est Alex Chen?"
```

### Étape 3 : Optimisation (selon résultats)
Basé sur le diagnostic, je vous aiderai à:
1. Changer le modèle LLM si nécessaire
2. Ajuster les paramètres de recherche
3. Désactiver les features non essentielles

---

## 📞 Questions fréquentes

**Q: Pourquoi mes documents ne changent pas même après modification?**
A: Il faut réindexer ! Utilisez le bouton "Réindexer" dans l'interface ou:
```bash
python -m src.indexer anomalie2084
```

**Q: L'IA me donne des infos fausses**
A: Vérifiez que vos documents sont bien indexés. Le reranking peut aider.

**Q: Puis-je utiliser plusieurs projets?**
A: Oui ! Créez un dossier `data/mon_projet/` et indexez-le.

**Q: Comment changer de modèle LLM depuis l'interface?**
A: Sélecteur de modèle en haut → Choisir → Les requêtes suivantes l'utiliseront.

---

**Créé le:** 2025-12-22  
**Version:** Ecrituria v2.1  
**Auteur:** Documentation technique
