# 🔑 Guide de Configuration de la Clé API OpenRouter

## Vue d'ensemble

Écrituria v2.1 intègre maintenant une interface graphique pour configurer votre clé API OpenRouter directement depuis l'application, sans avoir à éditer manuellement le fichier `.env`.

![Configuration Modal Preview](../../.gemini/antigravity/brain/841dcdf7-dcb7-42ee-9d3f-4d9c2bfb7382/config_modal_preview_1766393739004.png)

---

## 📖 Instructions d'utilisation

### Étape 1: Accéder à la configuration

1. Lancez le serveur Écrituria:
   ```bash
   python -m src.server
   ```

2. Ouvrez votre navigateur sur `http://localhost:8000`

3. Dans la barre d'outils supérieure, cliquez sur le bouton **⚙️ Configuration**

### Étape 2: Visualiser la clé actuelle

- La clé API actuellement configurée s'affiche masquée: `sk-****...****`
- Cliquez sur l'icône **👁️** pour afficher/masquer la clé complète
- Si aucune clé n'est configurée, vous verrez "Non configurée"

### Étape 3: Configurer une nouvelle clé

1. **Obtenir une clé OpenRouter**:
   - Visitez [openrouter.ai/keys](https://openrouter.ai/keys)
   - Créez un compte ou connectez-vous
   - Cliquez sur "Create Key"
   - Copiez votre nouvelle clé (commence par `sk-or-v1-`)

2. **Entrer la clé dans Écrituria**:
   - Dans le champ "Nouvelle clé API", collez votre clé
   - Vérifiez qu'elle commence bien par `sk-or-`
   - Cliquez sur **💾 Enregistrer**

3. **Redémarrer le serveur**:
   - Fermez le serveur (Ctrl+C dans le terminal)
   - Relancez-le:
     ```bash
     python -m src.server
     ```

### Étape 4: Vérifier la configuration

- Testez avec une question dans le chat
- Si tout fonctionne, vous recevrez une réponse de l'IA
- En cas d'erreur, vérifiez que:
  - La clé est correcte
  - Vous avez redémarré le serveur
  - Votre compte OpenRouter a du crédit

---

## 🔒 Sécurité

### Protection de la clé

- ✅ La clé est masquée par défaut (`************`)
- ✅ Le fichier `.env` n'est **jamais** accessible via le web
- ✅ Le fichier `.env` est dans `.gitignore` (ne sera pas commité)
- ✅ La clé est stockée localement sur votre machine

### Bonnes pratiques

1. **Ne partagez jamais votre clé API**
   - Ne la publiez pas sur GitHub, Discord, etc.
   - Ne la mettez pas dans des screenshots publics

2. **Régénérez votre clé si exposée**
   - Si vous pensez que votre clé a été compromise
   - Allez sur OpenRouter et régénérez une nouvelle clé
   - Mettez à jour dans Écrituria

3. **Utilisez des clés séparées par projet**
   - Créez une clé dédiée pour Écrituria
   - Facilitera le tracking de consommation
   - Plus facile de révoquer si nécessaire

---

## ❓ Questions Fréquentes

### Pourquoi dois-je redémarrer le serveur?

Le serveur charge les variables d'environnement au démarrage. Le redémarrage est nécessaire pour que Python charge la nouvelle clé depuis `.env`.

### Puis-je utiliser une clé OpenAI?

Oui! Vous pouvez configurer `OPENAI_API_KEY` dans le fichier `.env` directement. L'interface de configuration supporte actuellement OpenRouter uniquement, mais les deux clés fonctionnent.

### Où est stockée ma clé?

La clé est stockée dans le fichier `.env` à la racine du projet:
```
Ecrituria/
├── fiction-assistant/
│   ├── .env          ← Ici
│   ├── src/
│   └── ...
```

### Que se passe-t-il si je n'ai pas de clé?

Sans clé API configurée:
- ✅ L'interface fonctionne normalement
- ✅ Vous pouvez parcourir vos fichiers
- ✅ Vous pouvez upload et éditer
- ❌ Le chat IA ne fonctionnera pas
- ❌ Les requêtes RAG échoueront

### Comment vérifier ma consommation?

1. Allez sur [openrouter.ai/activity](https://openrouter.ai/activity)
2. Vous verrez l'historique et les coûts par requête
3. Configurez des alertes de budget si nécessaire

---

## 🛠️ Dépannage

### Erreur: "API key not found"

**Solution**:
```bash
# Vérifier que le fichier .env existe
ls .env

# Vérifier le contenu (masquer votre vraie clé!)
cat .env

# Si le fichier n'existe pas, créez-le
cp env_example.txt .env
```

### Erreur: "Invalid API key"

**Causes possibles**:
1. La clé est incorrecte (typo lors du copier-coller)
2. La clé a été révoquée sur OpenRouter
3. Vous n'avez pas redémarré le serveur

**Solution**:
- Générez une nouvelle clé sur OpenRouter
- Configurez-la dans Écrituria
- Redémarrez le serveur

### La modal ne s'ouvre pas

**Solution**:
```bash
# Vider le cache du navigateur
Ctrl + Shift + Delete

# Ou forcer le rechargement
Ctrl + F5
```

### Changements non pris en compte

**Solution**:
```bash
# 1. Arrêter le serveur
Ctrl + C

# 2. Vérifier le .env
cat .env

# 3. Relancer
python -m src.server

# 4. Recharger la page
Ctrl + F5
```

---

## 🎯 Utilisation Avancée

### Variables d'environnement disponibles

Vous pouvez configurer d'autres options dans `.env`:

```bash
# Clés API
OPENROUTER_API_KEY=sk-or-v1-votre-cle
OPENAI_API_KEY=sk-proj-votre-cle-openai

# Modèle par défaut
DEFAULT_MODEL=gpt-4o-mini

# Température (créativité)
DEFAULT_TEMPERATURE=0.7

# Provider par défaut
DEFAULT_PROVIDER=openrouter
```

### Configuration programmatique

Si vous développez des extensions, vous pouvez aussi accéder à l'API:

```python
import requests

# Récupérer la clé masquée
response = requests.get('http://localhost:8000/api/config/apikey')
print(response.json())
# {'has_key': True, 'masked_key': 'sk-o****...****'}

# Mettre à jour la clé
response = requests.post(
    'http://localhost:8000/api/config/apikey',
    json={'api_key': 'sk-or-v1-nouvelle-cle'}
)
print(response.json())
# {'success': True, 'message': 'Clé API mise à jour avec succès'}
```

---

## 📊 Endpoints API

### GET `/api/config/apikey`

Récupère la clé API masquée.

**Réponse**:
```json
{
  "has_key": true,
  "masked_key": "sk-o****...****2aBc"
}
```

### POST `/api/config/apikey`

Met à jour la clé API.

**Requête**:
```json
{
  "api_key": "sk-or-v1-votre-nouvelle-cle"
}
```

**Réponse**:
```json
{
  "success": true,
  "message": "Clé API mise à jour avec succès"
}
```

---

## 📝 Notes de version

### v2.1.0 (22 Décembre 2025)

**Nouveau**:
- ✨ Interface de configuration de clé API
- 🔑 Gestion complète depuis l'UI (lecture, masquage, modification)
- 🎨 Design moderne cohérent avec le thème de l'application
- 🔒 Sécurité: clé masquée par défaut

**Technique**:
- Backend: 2 nouveaux endpoints (`GET` et `POST /api/config/apikey`)
- Frontend: Modal de configuration + fonctions JavaScript
- CSS: 158 lignes de styles dédiés

---

## 🔮 Prochaines améliorations

Fonctionnalités prévues pour les versions futures:

- [ ] Support de multiples clés API (rotation)
- [ ] Gestion des crédits directement dans l'UI
- [ ] Configuration d'autres providers (Anthropic, Google)
- [ ] Historique des clés utilisées
- [ ] Test de connexion automatique
- [ ] Import/Export de configuration

---

**Pour plus d'informations**: Voir `STATUS_ET_PROCHAINES_ETAPES.md`

**Besoin d'aide?**: Consultez le `GUIDE_UTILISATION.md` principal
