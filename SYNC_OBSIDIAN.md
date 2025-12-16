# 🔄 Synchroniser Obsidian avec l'Assistant Fiction RAG

## 1. Organisation recommandée

Dans votre vault Obsidian `Ecrituria`, utilisez la structure suivante :

```
Ecrituria/
└─ Anomalie2084/
   ├─ lore/
   ├─ personnages/
   ├─ intrigue/
   ├─ chapitres/
   └─ notes/
```

> Ces dossiers correspondent à `data/anomalie2084/` dans le projet RAG.

## 2. Pré-requis

- Vault créé dans `C:\Users\User\Documents\Ecrituria`
- Vos fichiers `.md` / `.txt` rangés dans les sous-dossiers ci-dessus

## 3. Script de synchronisation

Commande à exécuter depuis la racine du projet :

```powershell
python -m src.sync_obsidian --vault "C:/Users/User/Documents/Ecrituria" --project anomalie2084
```

Options disponibles :

| Option | Description |
|--------|-------------|
| `--vault` | Chemin du vault Obsidian (par défaut `~/Documents/Ecrituria`) |
| `--project` | Nom du projet (défaut `anomalie2084`) |
| `--mode merge` | (Défaut) remplace fichier par fichier |
| `--mode replace` | Supprime `data/<projet>` avant copie |
| `--dry-run` | Simule la commande sans copier |

## 4. Workflow complet

1. Modifiez vos fichiers dans Obsidian
2. Synchronisez :
   ```powershell
   python -m src.sync_obsidian --vault "C:/Users/User/Documents/Ecrituria"
   ```
3. Reconstruisez l'index vectoriel :
   ```powershell
   python -m src.indexer anomalie2084
   ```
4. Interagissez avec l'IA (`python -m src.cli anomalie2084` ou interface web)

## 5. Notes

- Le script copie uniquement `.md` et `.txt`
- Les autres fichiers (images, templates) sont ignorés
- Les sous-dossiers supplémentaires sont conservés tels quels
- Vous pouvez créer d'autres projets en ajoutant d'autres dossiers dans le vault (ex: `Ecrituria/NouveauRoman`) et en utilisant `--project nouveauRoman`

