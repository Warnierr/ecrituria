# 📖 Assistant Fiction RAG

Un système d'aide à l'écriture de fiction basé sur RAG (Retrieval-Augmented Generation) qui permet de discuter avec votre univers narratif et de maintenir la cohérence de vos histoires.

## 🎯 Qu'est-ce que c'est ?

L'Assistant Fiction RAG est un outil qui :
- 📚 Indexe tous vos documents de fiction (worldbuilding, personnages, intrigues, chapitres)
- 🔍 Peut répondre à des questions précises sur votre univers
- ✍️ Vous aide à générer du contenu cohérent avec ce qui existe déjà
- 🧠 Sert de "mémoire augmentée" pour vos projets créatifs

## ✨ Fonctionnalités

- **Recherche sémantique** : Trouvez instantanément les informations dans vos documents
- **Génération cohérente** : Créez du nouveau contenu qui respecte votre univers
- **Chat interactif** : Discutez naturellement avec votre base de connaissance
- **Multi-projets** : Gérez plusieurs univers de fiction simultanément
- **Sources traçables** : Voyez d'où viennent les informations

## 🚀 Installation rapide

### 1. Prérequis

- Python 3.10 ou supérieur
- Une clé API OpenAI ([obtenir une clé](https://platform.openai.com/api-keys))

### 2. Installation

```bash
# Cloner ou télécharger le projet
cd fiction-assistant

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

Créez un fichier `.env` à la racine du projet :

```bash
# Copier le fichier exemple
cp env_example.txt .env

# Éditer .env et ajouter votre clé API
# OPENAI_API_KEY=sk-votre_clé_ici
```

## 📝 Utilisation

### Étape 1 : Organiser vos documents

Créez vos documents de fiction dans le dossier `data/nom_projet/` :

```
data/
└── mon_projet/
    ├── lore/
    │   └── monde.md
    ├── personnages/
    │   ├── protagoniste.md
    │   └── antagoniste.md
    ├── intrigue/
    │   └── arc_principal.md
    ├── chapitres/
    │   ├── chapitre1.md
    │   └── chapitre2.md
    └── notes/
        └── idees.md
```

**Note** : Un projet exemple "anomalie2084" est déjà fourni !

> 💡 Vous travaillez dans Obsidian ? Consultez `SYNC_OBSIDIAN.md` pour synchroniser automatiquement votre vault (`C:/Users/User/Documents/Ecrituria/Anomalie2084`) avec `data/anomalie2084/`.

### Étape 2 : Indexer votre projet

Avant la première utilisation et après chaque modification importante :

```bash
python -m src.indexer mon_projet
```

Cela va :
- 📂 Charger tous vos fichiers .txt et .md
- ✂️ Les découper en morceaux gérables
- 🔮 Créer les embeddings vectoriels
- 💾 Sauvegarder l'index dans `db/mon_projet/`

### Étape 3 : Discuter avec votre univers

```bash
python -m src.cli mon_projet
```

Vous pouvez alors :

**Poser des questions** :
```
💭 Vous: Quelle est la relation entre Alex et Maya ?
✨ Assistant: Alex et Maya sont meilleurs amis depuis l'enfance...
```

**Générer du contenu** :
```
💭 Vous: Propose 3 idées de scènes pour le prochain chapitre
✨ Assistant: Voici 3 idées cohérentes avec votre univers...
```

**Rechercher** :
```
💭 Vous: /search Nexus
📊 5 passages trouvés...
```

**Voir les sources** :
```
💭 Vous: /sources Qui sont les Éveillés ?
✨ Assistant: Les Éveillés sont...
📚 Sources utilisées:
1. intrigue/saison1.md
2. lore/monde.md
```

## 🎨 Commandes disponibles

Dans le chat interactif :

| Commande | Description |
|----------|-------------|
| `<votre question>` | Pose une question à l'assistant |
| `/sources <question>` | Affiche les sources utilisées pour répondre |
| `/search <mots-clés>` | Recherche des passages dans vos documents |
| `/help` | Affiche l'aide complète |
| `/quit` ou `/exit` | Quitter le chat |

## 💡 Exemples d'utilisation

### Vérifier la cohérence
```
💭 Vous: Alex peut-il voler ? Vérifie dans ses capacités.
✨ Assistant: Non, d'après la fiche personnage d'Alex, ses capacités 
d'Anomalie incluent la perception et manipulation des flux de données 
du Nexus, mais pas de vol physique.
```

### Brainstorming créatif
```
💭 Vous: Imagine une scène où Maya découvre qu'Alex est une Anomalie
✨ Assistant: Voici une proposition de scène cohérente avec le ton 
et les personnages établis...
```

### Résumés et synthèses
```
💭 Vous: Résume l'arc narratif de la saison 1
✨ Assistant: La saison 1 suit Alex Chen qui découvre...
```

### Continuation de texte
```
💭 Vous: Continue ce passage en gardant le même style: 
"Alex posa sa main sur le nœud du Nexus..."
✨ Assistant: Au lieu du contact froid habituel...
```

## 🔧 Configuration avancée

### Fichier `config/settings.yaml`

Personnalisez les paramètres :

```yaml
indexing:
  chunk_size: 1000        # Taille des morceaux de texte
  chunk_overlap: 150      # Chevauchement entre morceaux

rag:
  model: "gpt-4o-mini"    # Modèle OpenAI (gpt-4, gpt-4o-mini, etc.)
  temperature: 0.7        # Créativité (0-1)
  k_results: 5            # Nombre de passages à récupérer
```

### Utilisation programmatique

Vous pouvez aussi utiliser les modules directement dans vos scripts :

```python
from src.rag import ask, get_relevant_passages

# Poser une question
réponse = ask("mon_projet", "Qui est le protagoniste ?")
print(réponse)

# Rechercher des passages
passages = get_relevant_passages("mon_projet", "combat", k=3)
for p in passages:
    print(p.page_content)
```

## 📁 Structure du projet

```
fiction-assistant/
├── data/               # Vos projets de fiction
│   └── anomalie2084/   # Exemple fourni
├── db/                 # Bases vectorielles (généré)
├── config/             # Configuration
├── src/                # Code source
│   ├── loaders.py      # Chargement des documents
│   ├── indexer.py      # Indexation vectorielle
│   ├── rag.py          # Logique RAG
│   └── cli.py          # Interface CLI
├── requirements.txt    # Dépendances Python
├── env_example.txt     # Template de configuration
└── README.md           # Ce fichier
```

## 🎯 Workflow recommandé pour un écrivain

1. **Écrire/Modifier** : Travaillez sur vos fichiers normalement
2. **Réindexer** : `python -m src.indexer mon_projet`
3. **Consulter** : `python -m src.cli mon_projet`
   - Vérifier la cohérence
   - Brainstormer des idées
   - Obtenir des résumés
   - Générer des variations
4. **Retour à l'écriture** : Gardez le contrôle créatif final

## 🔒 Confidentialité et sécurité

- ✅ Toutes vos données restent **locales** (base vectorielle en local)
- ⚠️ Les requêtes sont envoyées à OpenAI (avec les passages pertinents)
- 💡 Utilisez un modèle local (Ollama, LMStudio) pour une confidentialité totale
- 🔐 Ne commitez jamais votre fichier `.env` (déjà dans `.gitignore`)

## 🛠️ Dépannage

### "L'index n'existe pas"
→ Lancez `python -m src.indexer nom_projet`

### "Aucun document trouvé"
→ Vérifiez que vos fichiers sont en `.txt` ou `.md` dans `data/nom_projet/`

### "Error: OpenAI API key"
→ Vérifiez votre fichier `.env` et que la clé API est valide

### Erreurs d'encodage
→ Assurez-vous que vos fichiers sont en UTF-8

## 🚧 Améliorations futures possibles

- [ ] Interface web (FastAPI + frontend)
- [ ] Support de PDF et DOCX
- [ ] Modes spécialisés (correcteur, co-scénariste, etc.)
- [ ] Export des conversations
- [ ] Détection automatique des incohérences
- [ ] Timeline interactive
- [ ] Support de modèles locaux (Ollama)
- [ ] Mise à jour incrémentale de l'index

## 📚 Ressources

- [Documentation LangChain](https://python.langchain.com/)
- [ChromaDB](https://www.trychroma.com/)
- [OpenAI API](https://platform.openai.com/docs/)

## 💬 Support

Pour toute question ou amélioration, n'hésitez pas à ouvrir une issue ou à contribuer au projet !

---

**Bon courage dans votre écriture ! ✍️✨**

