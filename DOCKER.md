# 🐳 Guide Docker - Écrituria

## 📖 Qu'est-ce que Docker ?

**Docker** est un système de **containerisation** qui permet d'empaqueter une application avec toutes ses dépendances dans un "conteneur" isolé.

### Analogie simple

Imagine une **boîte magique** qui contient :
- ✅ Python 3.11
- ✅ Toutes les bibliothèques nécessaires
- ✅ La configuration exacte
- ✅ L'application Écrituria

Cette boîte fonctionne **identiquement** sur :
- Windows
- Mac
- Linux
- Serveur cloud

**Sans Docker :** "Ça marche sur ma machine !" 😤  
**Avec Docker :** "Ça marche partout !" 🎉

---

## 🚀 Démarrage rapide

### 1. Installer Docker Desktop

- **Windows/Mac :** [Télécharger Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux :** `sudo apt install docker.io docker-compose`

### 2. Configurer l'environnement

```bash
# Créer le fichier .env
cp env_example.txt .env

# Éditer .env et ajouter ta clé API
# OPENAI_API_KEY=sk-votre_clé_ici
# ou
# OPENROUTER_API_KEY=sk-or-v1-...
```

### 3. Lancer Écrituria

```bash
# Construire et démarrer
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

**C'est tout !** 🎉 L'application est sur http://localhost:8000

---

## 📋 Commandes essentielles

| Commande | Description |
|----------|-------------|
| `docker-compose up -d` | Démarrer en arrière-plan |
| `docker-compose down` | Arrêter |
| `docker-compose restart` | Redémarrer |
| `docker-compose logs -f` | Voir les logs en temps réel |
| `docker-compose ps` | Voir l'état des conteneurs |
| `docker-compose exec ecrituria bash` | Accéder au shell du conteneur |

---

## 🔧 Gestion des données

### Volumes Docker

Les **volumes** permettent de partager des dossiers entre ton PC et le conteneur :

```yaml
volumes:
  - ./data:/app/data      # Tes projets d'écriture
  - ./db:/app/db          # Bases de données (index vectoriel)
  - ./.env:/app/.env:ro   # Configuration (lecture seule)
```

**Cela signifie :**
- ✅ Modifier un fichier dans `data/` depuis ton PC → visible dans le conteneur
- ✅ Les bases de données sont **persistantes** (ne disparaissent pas si tu arrêtes)
- ✅ Tes données restent sur ton PC (pas dans le conteneur)

### Sauvegarder tes données

```bash
# Sauvegarder data/ et db/
tar -czf backup-ecrituria.tar.gz data/ db/

# Restaurer
tar -xzf backup-ecrituria.tar.gz
```

---

## 🛠️ Dépannage

### Le conteneur ne démarre pas

```bash
# Voir les logs d'erreur
docker-compose logs ecrituria

# Vérifier que le port 8000 est libre
netstat -an | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux
```

### Reconstruire l'image

Si tu modifies le code ou `requirements.txt` :

```bash
docker-compose up -d --build
```

### Nettoyer complètement

```bash
# Arrêter et supprimer les conteneurs
docker-compose down

# Supprimer aussi les volumes (⚠️ supprime les données !)
docker-compose down -v

# Nettoyer les images inutilisées
docker system prune -a
```

### Accéder au conteneur pour déboguer

```bash
# Shell interactif
docker-compose exec ecrituria bash

# Exécuter une commande
docker-compose exec ecrituria python -m src.indexer anomalie2084
```

---

## 🎯 Workflow recommandé

### 1. Développement local

```bash
# Modifier le code
# ...

# Reconstruire et redémarrer
docker-compose up -d --build

# Voir les logs
docker-compose logs -f
```

### 2. Indexer un projet

```bash
# Depuis l'extérieur du conteneur
docker-compose exec ecrituria python -m src.indexer anomalie2084

# Ou depuis le shell du conteneur
docker-compose exec ecrituria bash
python -m src.indexer anomalie2084
```

### 3. Mettre à jour les dépendances

```bash
# Modifier requirements.txt
# ...

# Reconstruire
docker-compose up -d --build
```

---

## 🔐 Sécurité

### Variables d'environnement

Le fichier `.env` est monté en **lecture seule** (`:ro`) pour éviter qu'il soit modifié par erreur dans le conteneur.

### Isolation

Le conteneur est **isolé** de ton système :
- ✅ Ne peut pas accéder à d'autres fichiers
- ✅ Ne peut pas modifier ton système
- ✅ S'arrête proprement avec `docker-compose down`

---

## 📚 Ressources

- [Documentation Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Best Practices Docker](https://docs.docker.com/develop/dev-best-practices/)

---

## ❓ Questions fréquentes

**Q : Mes données sont-elles sauvegardées ?**  
R : Oui, les volumes `data/` et `db/` sont persistants sur ton PC.

**Q : Puis-je utiliser plusieurs projets en même temps ?**  
R : Oui, ajoute tes projets dans `data/` et indexe-les normalement.

**Q : Comment mettre à jour Écrituria ?**  
R : `git pull` puis `docker-compose up -d --build`

**Q : Le conteneur prend beaucoup de place ?**  
R : L'image fait ~500-800 MB. Les données (`data/`, `db/`) dépendent de tes projets.

---

**Bon développement ! 🚀**

