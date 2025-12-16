# 📘 Guide d'utilisation - Assistant Fiction RAG

Ce guide vous accompagne pas à pas dans l'utilisation de votre assistant d'écriture.

## 🎬 Démarrage rapide (5 minutes)

### 1. Tester avec le projet exemple

Un projet complet "Anomalie 2084" est déjà fourni. C'est parfait pour découvrir l'outil !

```bash
# Étape 1 : Indexer le projet exemple
python -m src.indexer anomalie2084

# Étape 2 : Lancer le chat
python -m src.cli anomalie2084
```

### 2. Essayez ces questions

Une fois dans le chat, testez :

```
💭 Qui est Alex Chen ?
💭 Quelle est la relation entre Alex et Maya ?
💭 Décris-moi l'univers d'Anomalie 2084
💭 Propose une scène où Alex utilise ses pouvoirs
💭 /search Nexus
💭 /sources Qui sont les Éveillés ?
```

## 📝 Créer votre propre projet

### Étape 1 : Structure de dossiers

Créez votre projet dans `data/` :

```bash
# Windows
mkdir data\mon_roman
mkdir data\mon_roman\personnages
mkdir data\mon_roman\lore
mkdir data\mon_roman\chapitres
mkdir data\mon_roman\notes

# Linux/Mac
mkdir -p data/mon_roman/{personnages,lore,chapitres,notes}
```

### Étape 2 : Organisez vos documents

Voici une structure recommandée :

```
data/mon_roman/
├── lore/
│   ├── monde.md           # Description de l'univers
│   ├── histoire.md        # Histoire du monde
│   └── magie_systeme.md   # Système de magie/tech
│
├── personnages/
│   ├── protagoniste.md    # Fiche détaillée
│   ├── antagoniste.md
│   └── secondaires.md
│
├── intrigue/
│   ├── arc_principal.md   # Synopsis, structure
│   ├── sous_intrigues.md
│   └── timeline.md        # Chronologie des événements
│
├── chapitres/
│   ├── chapitre_01.md
│   ├── chapitre_02.md
│   └── ...
│
├── lieux/
│   ├── ville_capitale.md
│   └── regions.md
│
└── notes/
    ├── idees.md           # Brainstorming
    ├── themes.md          # Thèmes à explorer
    └── recherches.md      # Notes de recherche
```

### Étape 3 : Format des fichiers

#### Exemple de fiche personnage

```markdown
# Nom du personnage

## Informations de base
- Âge : 
- Origine :
- Occupation :

## Apparence
Description physique...

## Personnalité
Traits principaux...

## Histoire
Background du personnage...

## Relations
- Personnage A : description de la relation
- Personnage B : description de la relation

## Arc narratif
Évolution prévue...

## Particularités
Pouvoirs, compétences spéciales...
```

#### Exemple de worldbuilding

```markdown
# Titre de l'élément de lore

## Description générale
Vue d'ensemble...

## Histoire
Comment c'est apparu, évolué...

## Fonctionnement
Détails techniques/magiques...

## Impact sur l'intrigue
En quoi c'est important...

## Notes
Idées supplémentaires...
```

### Étape 4 : Indexer et utiliser

```bash
# Indexer votre projet
python -m src.indexer mon_roman

# Lancer le chat
python -m src.cli mon_roman
```

## 🎨 Cas d'usage par type de besoin

### 1. Vérification de cohérence

**Situation** : Vous écrivez le chapitre 15 et vous n'êtes plus sûr d'un détail.

```
💭 Dans quel chapitre j'ai décrit la première rencontre entre X et Y ?
💭 Quelle couleur ont les yeux de ce personnage ?
💭 Est-ce que j'ai déjà mentionné cette capacité magique ?
💭 Vérifie si ce rebondissement est cohérent avec ce qui existe
```

### 2. Brainstorming créatif

**Situation** : Vous cherchez des idées pour avancer l'intrigue.

```
💭 Propose 5 complications qui pourraient surgir maintenant
💭 Imagine un dialogue tendu entre X et Y sur le thème de la trahison
💭 Quelles seraient les conséquences logiques de cet événement ?
💭 Suggère des scènes pour développer la relation entre ces personnages
```

### 3. Résumés et synthèses

**Situation** : Vous revenez sur le projet après une pause.

```
💭 Résume-moi l'arc narratif du personnage principal
💭 Quels sont les événements majeurs jusqu'ici ?
💭 Rappelle-moi les points clés de l'intrigue secondaire
💭 Fais-moi un résumé du chapitre précédent
```

### 4. Aide à la rédaction

**Situation** : Vous voulez améliorer un passage.

```
💭 Propose des variations de cette scène avec différents tons
💭 Continue ce passage : [votre texte]
💭 Réécris cette description en plus sensoriel/émotionnel
💭 Suggère des métaphores cohérentes avec l'univers pour décrire X
```

### 5. Recherche dans l'univers

**Situation** : Vous cherchez tous les passages sur un sujet.

```
💭 /search combat épée
💭 /search relation père-fils
💭 /search description ville
💭 /search pouvoir magique
```

### 6. Analyse et développement

**Situation** : Vous voulez approfondir votre univers.

```
💭 Quels aspects du worldbuilding sont sous-développés ?
💭 Quels personnages secondaires mériteraient plus de profondeur ?
💭 Y a-t-il des incohérences dans le système magique ?
💭 Quels thèmes sont présents dans l'histoire ?
```

## 🔄 Workflow type d'une session d'écriture

### Matin : Planification

```bash
python -m src.cli mon_roman
```

```
💭 Résume ce qui s'est passé dans les 3 derniers chapitres
💭 Rappelle-moi où j'en suis dans l'arc narratif
💭 Quels fils narratifs sont en suspens ?
💭 Propose une structure pour le prochain chapitre
```

### Après-midi : Écriture

Écrivez votre chapitre dans votre éditeur favori (Word, Scrivener, VS Code, etc.)

Consultez l'assistant au besoin :
```
💭 Comment le personnage X réagirait dans cette situation ?
💭 /search description palais royal
💭 Vérifie si ce détail est cohérent
```

### Soir : Révision

Sauvegardez votre nouveau chapitre dans `data/mon_roman/chapitres/`

```bash
# Réindexer pour inclure le nouveau contenu
python -m src.indexer mon_roman

# Vérifier la cohérence
python -m src.cli mon_roman
```

```
💭 Y a-t-il des incohérences dans ce nouveau chapitre ?
💭 Résume le nouveau chapitre et son impact sur l'intrigue
💭 Quels éléments introduits devront être développés plus tard ?
```

## 💡 Bonnes pratiques

### ✅ À faire

- **Réindexer régulièrement** après des modifications importantes
- **Être spécifique** dans vos questions
- **Utiliser /sources** pour vérifier les informations
- **Garder le contrôle créatif** : l'IA suggère, vous décidez
- **Organiser vos documents** clairement dès le début
- **Mettre à jour les fiches** au fur et à mesure de l'écriture

### ❌ À éviter

- Ne pas réindexer et se demander pourquoi l'IA ne connaît pas les nouveautés
- Poser des questions trop vagues ("parle-moi de l'histoire")
- Accepter aveuglément toutes les suggestions
- Laisser l'IA écrire à votre place
- Négliger l'organisation des fichiers

## 🎯 Optimiser les résultats

### Formulation des questions

**❌ Vague** : "Idées de scène"
**✅ Précis** : "Propose 3 scènes où Alex utilise ses pouvoirs pour aider quelqu'un, en gardant le ton sombre mais plein d'espoir de l'univers"

**❌ Trop large** : "Parle-moi des personnages"
**✅ Ciblé** : "Décris l'évolution de la relation entre Alex et Maya depuis le début"

### Utiliser les commandes

```
# Pour voir d'où viennent les infos
/sources <question>

# Pour trouver tous les passages pertinents
/search <mots-clés>

# Pour l'aide
/help
```

### Température et créativité

Dans `config/settings.yaml`, ajustez la `temperature` :

- **0.3-0.5** : Réponses factuelles, cohérentes, prudentes
- **0.7-0.8** : Équilibre (recommandé pour la fiction)
- **0.9-1.0** : Très créatif, plus de variations

## 🔧 Maintenance du projet

### Quand réindexer ?

Réindexez après :
- ✅ Ajout d'un nouveau chapitre
- ✅ Modification majeure d'une fiche personnage
- ✅ Ajout de nouveaux éléments de worldbuilding
- ✅ Corrections importantes d'incohérences

Pas besoin de réindexer pour :
- ❌ Petites corrections orthographiques
- ❌ Reformulations mineures
- ❌ Ajout de notes personnelles sans impact

### Sauvegardes

N'oubliez pas de sauvegarder :
- 📁 Tout le dossier `data/` (vos documents)
- 💾 Le dossier `db/` si vous voulez garder l'index (sinon il se reconstruit)
- ⚙️ Votre fichier `.env` (mais ne le partagez jamais !)

## 🚀 Aller plus loin

### Modes d'utilisation spécialisés

Vous pouvez créer des "personnalités" pour l'assistant en variant vos prompts :

**Mode Éditeur** :
```
💭 Analyse ce passage comme un éditeur critique et suggère des améliorations
```

**Mode Coach d'écriture** :
```
💭 Quels sont les points forts et faibles de mon développement narratif ?
```

**Mode Lecteur test** :
```
💭 En tant que lecteur, qu'est-ce qui te marquerait le plus dans cette scène ?
```

### Intégration avec d'autres outils

L'assistant fonctionne avec vos outils d'écriture habituels :
- **Scrivener** : Exportez vos chapitres en .md
- **Word** : Sauvegardez en .txt ou .md
- **Obsidian/Notion** : Déjà en markdown !
- **VS Code** : Éditez directement dans `data/`

## 📞 Besoin d'aide ?

Si quelque chose ne fonctionne pas :

1. Consultez la section **Dépannage** dans le README
2. Vérifiez que vous avez bien réindexé
3. Testez avec le projet exemple `anomalie2084`
4. Vérifiez votre configuration `.env`

---

**Bonne écriture ! 📖✨**

