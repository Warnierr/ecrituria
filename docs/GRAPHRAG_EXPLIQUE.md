# 🔗 GraphRAG - Guide Interne Ecrituria

## Qu'est-ce que le GraphRAG ?

**GraphRAG** = Graph + RAG (Retrieval-Augmented Generation)

C'est une évolution du RAG classique qui ajoute un **graphe de connaissances** pour mieux comprendre les relations entre les éléments de ton univers narratif.

---

## 🎯 Le problème que ça résout

### RAG classique (vecteurs seuls)
```
Question: "Quelle est la relation entre Alex et Maya ?"

RAG classique cherche des passages qui MENTIONNENT Alex ET Maya ensemble.
→ Si ces infos sont dans des fichiers séparés, il rate la connexion.
```

### Avec GraphRAG
```
Question: "Quelle est la relation entre Alex et Maya ?"

1. Identifie "Alex" et "Maya" comme entités
2. Cherche dans le graphe: Alex --[CONNAIT]--> Maya (type: ami)
3. Récupère aussi les passages textuels
4. Combine les deux pour une réponse complète
```

---

## 📊 Structure du graphe

### Types de nœuds (entités)
| Type | Description | Exemple |
|------|-------------|---------|
| **Personnage** | Protagonistes, antagonistes, PNJ | Alex Chen, Maya, Voss |
| **Lieu** | Endroits de l'univers | Le Nexus, Zone Alpha |
| **Événement** | Actions importantes | La Découverte, L'Évasion |
| **Objet** | Items significatifs | La Bague de Lumeris |
| **Thème** | Concepts narratifs | Liberté, Technologie |

### Types de relations
| Relation | Signification |
|----------|---------------|
| `CONNAIT` | Deux personnages se connaissent |
| `VIENT_DE` | Un personnage vient d'un lieu |
| `PARTICIPE_A` | Impliqué dans un événement |
| `POSSEDE` | Possède un objet |
| `ALLIE_DE` | Alliance entre personnages |
| `ENNEMI_DE` | Opposition/conflit |
| `FAMILLE_DE` | Lien familial |
| `INCARNE` | Personnage incarne un thème |

---

## 🔄 Comment ça fonctionne

### 1. Population du graphe (bouton "Peupler Graphe")
```
Fichiers .md/.txt
       ↓
   LLM extrait les entités et relations (JSON)
       ↓
   Stockage dans le graphe (Neo4j simulé)
       ↓
   67 nœuds, 58 relations
```

### 2. Requête avec GraphRAG activé
```
Question utilisateur
       ↓
   LLM identifie les entités mentionnées
       ↓
   Traversée du graphe (voisinage, chemins)
       ↓
   Recherche vectorielle classique (BM25 + embeddings)
       ↓
   Fusion des contextes
       ↓
   Génération de la réponse enrichie
```

---

## ✅ Avantages du GraphRAG

### 1. **Compréhension des relations**
- Qui connaît qui ?
- Qui est allié/ennemi de qui ?
- Quels personnages partagent un lieu ?

### 2. **Cohérence narrative**
- Détecte les incohérences (X est ami de Y dans un fichier, ennemi dans un autre)
- Maintient une vue d'ensemble de l'univers

### 3. **Découverte de connexions**
- Trouve des chemins entre entités éloignées
- "Comment Alex pourrait-il rencontrer le Commandant Voss ?" → via Maya → via Zone Alpha

### 4. **Contexte enrichi**
- Ne se limite pas aux passages textuels
- Ajoute le "réseau social" de l'univers

---

## ❌ Inconvénients / Limites

### 1. **Temps de population**
- ~10-15 secondes par fichier (appel LLM)
- 14 fichiers = ~3 minutes
- À refaire si les fichiers changent significativement

### 2. **Qualité dépend du LLM**
- L'extraction peut rater des entités subtiles
- Peut créer des faux positifs (entités qui n'en sont pas)

### 3. **Complexité ajoutée**
- Plus de paramètres à gérer
- Debug plus difficile

### 4. **Coût API**
- Chaque extraction = 1 appel LLM
- Population complète = ~14 appels supplémentaires

---

## 🎛️ Quand utiliser GraphRAG ?

### ✅ Recommandé pour :
- Questions sur les **relations** entre personnages
- Vérification de **cohérence** narrative
- Exploration de l'**univers** (qui va où, qui fait quoi)
- Projets avec **beaucoup de personnages** interconnectés

### ❌ Pas nécessaire pour :
- Questions simples sur un seul personnage
- Recherche de passages spécifiques
- Génération créative libre
- Petits projets (< 5 fichiers)

---

## 📈 Exemple concret

### Sans GraphRAG
```
Q: "Qui pourrait aider Alex à s'échapper du Nexus ?"

Réponse basée uniquement sur les passages trouvés.
Peut manquer des connexions si les infos sont dispersées.
```

### Avec GraphRAG
```
Q: "Qui pourrait aider Alex à s'échapper du Nexus ?"

Le système voit dans le graphe:
- Alex --[CONNAIT]--> Maya (ami)
- Alex --[CONNAIT]--> vieille_dame_brebis (guide)
- Maya --[VIENT_DE]--> Zone Alpha (connaît les sorties?)

Réponse: "Maya, son amie d'enfance, pourrait l'aider car elle 
connaît bien la Zone Alpha. La vieille dame brebis, avec sa 
connaissance des anciennes voies, serait aussi une alliée 
potentielle..."
```

---

## 🔧 Commandes utiles

| Action | Comment |
|--------|---------|
| Peupler le graphe | Bouton "🔗 Peupler Graphe" |
| Activer GraphRAG | Cocher ☑️ GraphRAG avant d'envoyer |
| Voir les stats | Bouton "📊 Stats" |

---

## 📊 Stats actuelles du graphe

Après population du projet `anomalie2084` :
- **67 nœuds** (entités uniques)
- **58 relations** (connexions entre entités)
- **Temps de population** : ~180 secondes

---

## 🚀 Évolutions futures possibles

1. **Visualisation du graphe** : Voir les nœuds et relations graphiquement
2. **Édition manuelle** : Ajouter/modifier des relations à la main
3. **Détection d'incohérences** : Alerter si le graphe contient des contradictions
4. **Population incrémentale** : Ne ré-extraire que les fichiers modifiés
5. **Export/Import** : Sauvegarder le graphe pour ne pas repeupler

---

## 💡 Conseil pratique

> **Commence sans GraphRAG** pour les questions simples.
> **Active GraphRAG** quand tu as besoin de comprendre les relations
> ou vérifier la cohérence de ton univers.

Le RAG vectoriel seul est déjà très puissant pour 80% des cas d'usage.
GraphRAG ajoute de la valeur pour les 20% où les relations comptent.

