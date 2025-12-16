# 🚀 Démarrage Rapide - 5 minutes

## Étape 1 : Installation (2 min)

```bash
# Installer les dépendances
pip install -r requirements.txt
```

## Étape 2 : Configuration (1 min)

1. Créez un fichier `.env` à la racine :
```bash
OPENAI_API_KEY=votre_clé_api_openai
```

2. Obtenez une clé API sur https://platform.openai.com/api-keys

## Étape 3 : Test avec l'exemple (2 min)

```bash
# Indexer le projet exemple
python -m src.indexer anomalie2084

# Lancer le chat
python -m src.cli anomalie2084
```

## Étape 4 : Essayez !

Dans le chat, tapez :

```
💭 Qui est Alex Chen ?
💭 Quelle est la relation entre Alex et Maya ?
💭 Propose une scène où Alex utilise ses pouvoirs
💭 /help
```

## 🎉 C'est tout !

Consultez le `README.md` pour plus de détails ou `GUIDE_UTILISATION.md` pour des exemples avancés.

---

## 📝 Créer votre propre projet

```bash
# 1. Créer la structure
mkdir -p data/mon_projet/{lore,personnages,intrigue,chapitres,notes}

# 2. Ajouter vos fichiers .md ou .txt dans data/mon_projet/

# 3. Indexer
python -m src.indexer mon_projet

# 4. Utiliser
python -m src.cli mon_projet
```

C'est aussi simple que ça ! ✨

