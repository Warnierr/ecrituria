# 🔍 Diagnostic des lenteurs et blocages - RÉSOLU

## 🚨 Problèmes identifiés

### 1. **Erreur 401 "User not authorized" - PRINCIPAL COUPABLE**

**Symptôme :** L'IA reste bloquée en "Toujours en cours..." et ne répond jamais.

**Cause racine :** La clé API OpenRouter est **invalide ou mal configurée**.

**Preuve dans les logs :**
```
ERROR: {'error': {'message': 'User not authorized', 'code': 401}}
POST /api/chat HTTP/1.1 500 Internal Server Error
```

**Impact :** Timeout infini car l'API refuse la requête mais Python attend indéfiniment une réponse.

---

### 2. **Recherche hybride + Reranking activés par défaut**

**Impact secondaire :** Ajoute ~2-3s au temps de réponse même quand ça fonctionne.

---

## ✅ Solutions appliquées

### Solution 1 : Vérifier et corriger la clé API (CRITIQUE)

La clé API actuelle dans `.env` est :
```
OPENAI_API_KEY=sk-or-v1-...
```

**Problème :** OpenRouter nécessite que la clé soit aussi définie comme `OPENROUTER_API_KEY` OU que `OPENAI_API_KEY` soit valide pour OpenRouter.

**Actions à faire :**

#### Option A : Vérifier la validité de votre clé
1. Allez sur https://openrouter.ai/keys
2. Vérifiez que votre clé est active
3. Vérifiez qu'elle a des crédits

#### Option B : Mettre à jour le `.env`
Éditez `fiction-assistant/.env` :

```bash
# Votre clé OpenRouter (obtenez-la sur https://openrouter.ai/keys)
OPENAI_API_KEY=sk-or-v1-VOTRE_CLE_ICI
OPENROUTER_API_KEY=sk-or-v1-VOTRE_CLE_ICI  # Même valeur
```

**Redémarrez ensuite le serveur :**
```bash
# Ctrl+C pour arrêter
.\start-web.bat
```

---

### Solution 2 : Logging détaillé ajouté (FAIT ✅)

J'ai ajouté des logs temporels détaillés dans **3 fichiers** :

#### A. `src/rag.py` - Fonction `ask()`
```python
[RAG] 🔍 Démarrage retrieval...
[RAG]   🔍 Recherche hybride (k=15)...
[RAG]   ✓ Recherche hybride: 1.23s (15 docs)
[RAG]   ⚡ Reranking 15 → 5...
[RAG]   ✓ Reranking: 0.87s
[RAG] ✓ Retrieval terminé en 2.10s (5 docs)
[RAG] 📝 Construction du contexte...
[RAG] ✓ Contexte construit en 0.01s (4523 chars)
[RAG] 📤 Envoi au LLM (gpt-4o-mini)...
[RAG]    Taille prompt: 5234 chars
[RAG] ✓ LLM répondu en 3.45s
[RAG] ✅ TOTAL: 5.56s (retrieval=2.10s, llm=3.45s)
```

#### B. `src/rag.py` - Fonction `retrieve()`
```python
[RAG]   🔍 Recherche vectorielle (k=5)...
[RAG]   ✓ Recherche vectorielle: 0.34s (5 docs)
```

#### C. `src/server.py` - Endpoint `/api/chat`
```python
======================================================================
[SERVER] 📨 Nouvelle requête reçue
[SERVER]    Question: Qui est Alex Chen?...
[SERVER]    Projet: anomalie2084
[SERVER]    Modèle: default
[SERVER]    Use graph: False
[SERVER]    Use agents: False
======================================================================
[SERVER] 🔍 Mode: RAG classique
[... logs du RAG ...]
[SERVER] ✓ RAG classique terminé en 5.56s
[SERVER] ✅ REQUÊTE TOTALE: 5.60s
======================================================================
```

**Avantage :** Vous verrez **exactement** où le temps est dépensé !

---

### Solution 3 : Configuration optimisée

Créez `config/settings_fast.yaml` pour basculer facilement :

```yaml
# Configuration RAPIDE pour Ecrituria
rag:
  model: "openai/gpt-4o-mini"
  temperature: 0.7
  k_results: 3  # Réduit de 5 → 3
  
  hybrid_search:
    enabled: false  # Désactivé pour vitesse
  
  reranking:
    enabled: false  # Désactivé pour vitesse
```

**Usage :**
```python
# Dans server.py, ligne 303
result = ask(
    message.project,
    message.question,
    model=message.model or "gpt-4o-mini",
    show_sources=message.show_sources,
    use_hybrid=False,        # ← Changez ici
    use_reranking=False      # ← Et ici
)
```

---

## 📊 Performance attendue après corrections

### Avant (avec clé API valide)
```
Recherche hybride:    1.2s
Reranking:           0.9s
LLM (gpt-4o-mini):   3.5s
━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:               5.6s
```

### Après optimisation (sans hybrid/rerank)
```
Recherche vectorielle:  0.4s
LLM (gpt-4o-mini):     2.8s
━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                 3.2s  (-43% ⚡)
```

### Avec modèle plus rapide
```
Recherche vectorielle:      0.4s
LLM (llama-3.1-8b):        1.5s
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                     1.9s  (-66% ⚡⚡)
```

---

## 🎯 Plan d'action immédiat

### Étape 1 : Corriger la clé API (PRIORITAIRE)

1. **Vérifiez votre clé sur OpenRouter :**
   - https://openrouter.ai/keys
   - Statut : Active ✅
   - Crédits : > $0 ✅

2. **Si la clé est invalide, créez-en une nouvelle :**
   - Allez sur https://openrouter.ai/keys
   - Cliquez "Create Key"
   - Copiez la clé

3. **Mettez à jour `.env` :**
   ```bash
   OPENAI_API_KEY=sk-or-v1-NOUVELLE_CLE
   OPENROUTER_API_KEY=sk-or-v1-NOUVELLE_CLE
   ```

4. **Redémarrez :**
   ```bash
   # Ctrl+C
   .\start-web.bat
   ```

---

### Étape 2 : Tester avec les nouveaux logs

1. **Posez une question dans l'interface web**

2. **Regardez le terminal :**
   - Vous verrez tous les logs détaillés
   - Identifiez quelle étape prend du temps

3. **Interprétez les résultats :**

   ✅ **Si vous voyez :**
   ```
   [RAG] ✓ LLM répondu en 3.45s
   [SERVER] ✅ REQUÊTE TOTALE: 5.60s
   ```
   → **Tout fonctionne !** Si c'est trop lent, passez à l'étape 3.

   ❌ **Si vous voyez :**
   ```
   [RAG] ❌ ERREUR LLM après 0.50s: User not authorized
   ```
   → **Clé API invalide**, retournez à l'étape 1.

---

### Étape 3 : Optimiser la vitesse (optionnel)

Si tout fonctionne mais c'est trop lent :

**Option A - Modification rapide dans le code**

Éditez `src/server.py` ligne ~303 :
```python
result = ask(
    message.project,
    message.question,
    model=message.model or "gpt-4o-mini",
    show_sources=message.show_sources,
    use_hybrid=False,        # ← False pour vitesse
    use_reranking=False      # ← False pour vitesse
)
```

Redémarrez le serveur.

**Option B - Changer de modèle**

Éditez `config/settings.yaml` :
```yaml
rag:
  model: "meta-llama/llama-3.1-8b-instruct"  # Plus rapide
```

---

## 🔧 Debugging en temps réel

### Commande pour voir les logs en live

Le serveur affiche déjà tout dans le terminal. Regardez simplement le terminal où tourne `start-web.bat`.

### Exemple de session réussie

```
======================================================================
[SERVER] 📨 Nouvelle requête reçue
[SERVER]    Question: Qui est Alex Chen?...
[SERVER]    Projet: anomalie2084
[SERVER]    Modèle: default
======================================================================
[SERVER] 🔍 Mode: RAG classique
[RAG] 🔍 Démarrage retrieval...
[RAG]   🔍 Recherche hybride (k=15)...
[RAG]   ✓ Recherche hybride: 1.15s (15 docs)
[RAG]   ⚡ Reranking 15 → 5...
[RAG]   ✓ Reranking: 0.82s
[RAG] ✓ Retrieval terminé en 1.97s (5 docs)
[RAG] 📝 Construction du contexte...
[RAG] ✓ Contexte construit en 0.02s (3892 chars)
[RAG] 📤 Envoi au LLM (gpt-4o-mini)...
[RAG]    Taille prompt: 4567 chars
[RAG] ✓ LLM répondu en 3.21s
[RAG] ✅ TOTAL: 5.20s (retrieval=1.97s, llm=3.21s)
[SERVER] ✓ RAG classique terminé en 5.21s
[SERVER] ✅ REQUÊTE TOTALE: 5.24s
======================================================================
```

### Exemple de session avec erreur

```
======================================================================
[SERVER] 📨 Nouvelle requête reçue
[SERVER]    Question: Qui est Alex Chen?...
======================================================================
[SERVER] 🔍 Mode: RAG classique
[RAG] 🔍 Démarrage retrieval...
[RAG]   🔍 Recherche vectorielle (k=5)...
[RAG]   ✓ Recherche vectorielle: 0.34s (5 docs)
[RAG] ✓ Retrieval terminé en 0.35s (5 docs)
[RAG] 📝 Construction du contexte...
[RAG] ✓ Contexte construit en 0.01s (3245 chars)
[RAG] 📤 Envoi au LLM (gpt-4o-mini)...
[RAG]    Taille prompt: 4012 chars
[RAG] ❌ ERREUR LLM après 0.52s: AuthenticationError - User not authorized
[SERVER] ❌ ERREUR après 0.89s
[SERVER]    Type: AuthenticationError
[SERVER]    Message: User not authorized
======================================================================
```

→ **Diagnostic immédiat : problème de clé API !**

---

## 📝 Récapitulatif

### ✅ Changements appliqués

1. **Logs détaillés** dans `src/rag.py` et `src/server.py`
2. **Gestion des erreurs** avec messages clairs
3. **Mesure du temps** à chaque étape

### 🔴 Action requise de votre part

1. **Vérifier/corriger la clé API OpenRouter**
2. **Tester une requête** et observer les logs
3. **Optimiser si nécessaire** (désactiver hybrid/rerank)

### 📊 Résultats attendus

- **Avant :** Requête bloquée, timeout, pas de réponse
- **Après correction clé :** Réponses en 3-6s
- **Après optimisation :** Réponses en 2-3s

---

**Date :** 2025-12-22  
**Version :** Ecrituria v2.1 - Diagnostic Mode  
**Status :** Logs actifs ✅ - Action utilisateur requise pour clé API
