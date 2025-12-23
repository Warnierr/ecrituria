# ✅ Configuration OpenRouter CORRIGÉE

## Ce qui a été fait

J'ai ajouté la variable `OPENROUTER_API_KEY` dans votre fichier `.env` :

```bash
OPENAI_API_KEY=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
OPENROUTER_API_KEY=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
```

**Pourquoi les deux ?**
- `OPENAI_API_KEY` : Utilisé par LangChain (bibliothèque Python)
- `OPENROUTER_API_KEY` : Utilisé par OpenRouter pour l'authentification

Les deux doivent avoir la **même valeur** (votre clé OpenRouter).

---

## 🧪 Test immédiat

### 1. Ouvrez l'interface web
http://localhost:8000

### 2. Posez une question
Par exemple : **"Qui est Alex Chen?"**

### 3. Observez le terminal
Vous devriez voir des logs comme :

```
======================================================================
[SERVER] 📨 Nouvelle requête reçue
[SERVER]    Question: Qui est Alex Chen?...
[SERVER]    Projet: anomalie2084
======================================================================
[SERVER] 🔍 Mode: RAG classique
[RAG] 🔍 Démarrage retrieval...
[RAG]   🔍 Recherche hybride (k=15)...
[RAG]   ✓ Recherche hybride: 1.23s (15 docs)
[RAG]   ⚡ Reranking 15 → 5...
[RAG]   ✓ Reranking: 0.87s
[RAG] ✓ Retrieval terminé en 2.10s (5 docs)
[RAG] 📝 Construction du contexte...
[RAG] ✓ Contexte construit en 0.02s (3892 chars)
[RAG] 📤 Envoi au LLM (gpt-4o-mini)...
[RAG]    Taille prompt: 4567 chars
[RAG] ✓ LLM répondu en 3.21s                    ← Ça doit afficher un temps, pas une erreur !
[RAG] ✅ TOTAL: 5.33s
[SERVER] ✅ REQUÊTE TOTALE: 5.35s
======================================================================
```

---

## ✅ Si ça fonctionne

Vous devriez voir :
- ✅ Une réponse s'affiche dans l'interface web (pas bloqué)
- ✅ Les logs montrent `✓ LLM répondu en X.XXs`
- ✅ Pas d'erreur 401 "User not authorized"

**Performance normale : 4-7 secondes par requête**

---

## ❌ Si ça ne fonctionne toujours pas

### Erreur possible : "User not authorized" (401)

**Cause :** Votre clé OpenRouter est invalide ou n'a plus de crédits.

**Solution :**
1. Allez sur https://openrouter.ai/keys
2. Vérifiez que votre clé est **active**
3. Vérifiez vos **crédits** (il en faut > $0)
4. Si nécessaire, **créez une nouvelle clé**
5. Mettez à jour les deux variables dans `.env` avec la nouvelle clé
6. Redémarrez le serveur (Ctrl+C puis `.\start-web.bat`)

---

## ⚡ Pour aller plus vite (optionnel)

Si ça fonctionne mais c'est **trop lent (> 5s)**, optimisez :

### Option 1 : Désactiver hybrid search + reranking

Éditez `src/server.py` ligne 303 :
```python
result = ask(
    message.project,
    message.question,
    model=message.model or "gpt-4o-mini",
    show_sources=message.show_sources,
    use_hybrid=False,        # ← False
    use_reranking=False      # ← False
)
```

**Gain :** 5-7s → 2-4s ⚡

### Option 2 : Changer de modèle LLM

Dans `config/settings.yaml` :
```yaml
rag:
  model: "meta-llama/llama-3.1-8b-instruct"  # Plus rapide
```

**Gain :** 5-7s → 2-3s ⚡

---

## 📊 Interprétation des logs

### Logs normaux (tout va bien)
```
[RAG] ✓ LLM répondu en 3.21s           ← Temps raisonnable
[SERVER] ✅ REQUÊTE TOTALE: 5.35s      ← Requête terminée
```
→ **Tout fonctionne !**

### Logs d'erreur (problème d'authentification)
```
[RAG] ❌ ERREUR LLM après 0.52s: AuthenticationError
[SERVER] ❌ ERREUR après 0.89s
[SERVER]    Message: User not authorized
```
→ **Problème de clé API !** Vérifiez sur openrouter.ai

### Logs trop lents (besoin d'optimisation)
```
[RAG]   ✓ Recherche hybride: 2.34s     ← Trop long
[RAG]   ✓ Reranking: 1.87s             ← Trop long
[RAG] ✓ LLM répondu en 5.12s           ← Trop long
[SERVER] ✅ REQUÊTE TOTALE: 9.45s       ← Beaucoup trop long !
```
→ **Optimisez !** Désactivez hybrid/rerank ou changez de modèle

---

## 🎯 Checklist de vérification

- [ ] Le serveur est démarré (`.\start-web.bat`)
- [ ] L'interface web est accessible (http://localhost:8000)
- [ ] Le fichier `.env` contient les deux clés (OPENAI_API_KEY et OPENROUTER_API_KEY)
- [ ] Les deux clés ont la même valeur (votre clé OpenRouter)
- [ ] J'ai posé une question dans l'interface
- [ ] J'observe les logs dans le terminal
- [ ] Les logs montrent "✓ LLM répondu" (pas d'erreur 401)
- [ ] La réponse s'affiche dans l'interface web

---

**Testez maintenant et dites-moi ce que vous voyez dans les logs !** 🚀

---

**Fichier créé le :** 2025-12-22  
**Serveur :** Redémarré ✅  
**Config :** OpenRouter API configurée ✅
