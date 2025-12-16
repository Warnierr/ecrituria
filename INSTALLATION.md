# 📦 Installation détaillée

Guide complet d'installation de l'Assistant Fiction RAG.

## Prérequis système

### Obligatoire
- **Python 3.10 ou supérieur**
  - Vérifiez : `python --version`
  - Téléchargement : https://www.python.org/downloads/

### Recommandé
- **pip** (gestionnaire de packages Python)
  - Normalement installé avec Python
  - Vérifiez : `pip --version`

### Optionnel
- **Git** (pour le versionnage de vos projets)
- **Un éditeur de texte** (VS Code, Notepad++, etc.)

## Installation pas à pas

### Étape 1 : Vérifier Python

Ouvrez un terminal (PowerShell sur Windows) et vérifiez :

```bash
python --version
```

Vous devriez voir quelque chose comme : `Python 3.10.x` ou supérieur.

### Étape 2 : (Optionnel) Créer un environnement virtuel

**Recommandé** pour isoler les dépendances :

```bash
# Windows
cd fiction-assistant
python -m venv venv
venv\Scripts\activate

# Linux/Mac
cd fiction-assistant
python -m venv venv
source venv/bin/activate
```

Vous verrez `(venv)` apparaître dans votre terminal.

### Étape 3 : Installer les dépendances

```bash
cd fiction-assistant
pip install -r requirements.txt
```

Cela va installer :
- LangChain et ses dépendances
- ChromaDB
- OpenAI
- Et autres utilitaires

**Durée** : 1-3 minutes selon votre connexion.

### Étape 4 : Configuration OpenAI

#### Option A : Créer le fichier .env

Créez un fichier nommé `.env` à la racine de `fiction-assistant/` :

```bash
# Contenu du fichier .env
OPENAI_API_KEY=sk-votre_clé_api_ici
```

#### Option B : Variable d'environnement système

**Windows** :
```bash
setx OPENAI_API_KEY "sk-votre_clé_api_ici"
```

**Linux/Mac** :
```bash
export OPENAI_API_KEY="sk-votre_clé_api_ici"
```

#### Obtenir une clé API OpenAI

1. Allez sur https://platform.openai.com/
2. Créez un compte ou connectez-vous
3. Allez dans **API Keys**
4. Cliquez sur **Create new secret key**
5. Copiez la clé (vous ne pourrez plus la voir après !)
6. Ajoutez du crédit si nécessaire (https://platform.openai.com/account/billing)

**Coût estimé** : 
- Indexation d'un projet moyen : ~$0.50
- 100 questions/réponses : ~$1-2 avec GPT-4o-mini

### Étape 5 : Test de l'installation

```bash
# Indexer le projet exemple
python -m src.indexer anomalie2084

# Si ça fonctionne, vous verrez :
# ✓ Chargé: lore/monde.md
# ✓ Chargé: personnages/alex.md
# ...
# ✅ Index construit avec succès !
```

Si vous avez des erreurs, consultez la section **Dépannage** ci-dessous.

### Étape 6 : Lancer le chat

```bash
python -m src.cli anomalie2084
```

Vous devriez voir :

```
============================================================
✨ ASSISTANT FICTION RAG ✨
============================================================
📖 Projet actif: anomalie2084
============================================================
```

Tapez une question pour tester !

## Installation alternative (avec scripts)

### Windows

Utilisez les fichiers `.bat` fournis :

```bash
# Pour indexer
index.bat anomalie2084

# Pour lancer le chat
start.bat anomalie2084
```

### Linux/Mac

Créez des scripts shell équivalents ou utilisez directement les commandes Python.

## Configuration avancée

### Changer le modèle OpenAI

Dans votre fichier `.env` :

```bash
DEFAULT_MODEL=gpt-4o        # Plus puissant mais plus cher
# ou
DEFAULT_MODEL=gpt-4o-mini   # Recommandé : bon rapport qualité/prix
```

### Ajuster les paramètres

Éditez `config/settings.yaml` :

```yaml
rag:
  model: "gpt-4o-mini"
  temperature: 0.7    # 0 = factuel, 1 = créatif
  k_results: 5        # Nombre de passages à récupérer
```

## Dépannage

### Erreur : "python n'est pas reconnu"

**Solution** : Python n'est pas dans le PATH.
- Réinstallez Python en cochant "Add to PATH"
- Ou utilisez `py` au lieu de `python`

### Erreur : "pip n'est pas reconnu"

**Solution** :
```bash
python -m pip install -r requirements.txt
```

### Erreur : "No module named 'langchain'"

**Solution** : Les dépendances ne sont pas installées.
```bash
pip install -r requirements.txt
```

### Erreur : "OpenAI API key not found"

**Solution** : Vérifiez votre fichier `.env`
- Le fichier est bien nommé `.env` (pas `env.txt`)
- Il est à la racine de `fiction-assistant/`
- La clé commence par `sk-`

### Erreur lors de l'indexation : "RateLimitError"

**Solution** : Vous avez dépassé les limites d'OpenAI
- Ajoutez du crédit sur votre compte OpenAI
- Ou attendez (limites par minute)

### ChromaDB erreur : "sqlite3"

**Solution** (Windows) :
```bash
pip install pysqlite3-binary
```

### Erreur : "No such file or directory: data/projet"

**Solution** : Le projet n'existe pas
```bash
# Vérifier les projets disponibles
dir data     # Windows
ls data      # Linux/Mac
```

## Mise à jour

Pour mettre à jour les dépendances :

```bash
pip install --upgrade -r requirements.txt
```

## Désinstallation

Pour supprimer complètement :

1. Supprimez le dossier `fiction-assistant/`
2. Si vous avez créé un venv, il sera supprimé avec
3. Supprimez la variable d'environnement si vous l'avez définie

```bash
# Windows
setx OPENAI_API_KEY ""

# Linux/Mac - retirez la ligne de ~/.bashrc ou ~/.zshrc
```

## Support

Si vous rencontrez des problèmes :

1. ✅ Vérifiez cette documentation
2. ✅ Consultez le fichier `README.md`
3. ✅ Testez avec le projet exemple `anomalie2084`
4. ✅ Vérifiez que votre clé API OpenAI est valide

---

Une fois l'installation réussie, consultez le `GUIDE_UTILISATION.md` pour apprendre à utiliser efficacement l'outil ! 🚀

