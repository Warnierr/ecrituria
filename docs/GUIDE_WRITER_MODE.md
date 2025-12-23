# ✍️ Guide d'utilisation - Writer Mode

## 🎉 Writer Mode activé !

Le Writer Mode permet à l'IA de générer et sauvegarder du contenu directement dans vos fichiers.

---

## 📋 Accès au Writer Mode

1. Ouvrez l'interface web : **http://localhost:8000**
2. Redémarrez le serveur pour charger les nouveaux fichiers :
   ```bash
   # Arrêtez avec Ctrl+C
   .\start-web.bat
   ```
3. Un nouvel onglet "✍️ Writer" sera disponible

---

## 🎯 Les 4 Actions disponibles

### 1. **Réécrire** (Rewrite)
Régénère complètement le contenu d'un fichier existant.

**Exemple d'instruction :**
> "Réécris ce chapitre en amplifiant la tension dramatique entre Alex et le système."

**Résultat :** Le fichier entier est réécrit selon vos instructions

---

### 2. **Ajouter** (Append)
Ajoute du nouveau contenu à la fin d'un fichier existant.

**Exemple d'instruction :**
> "Ajoute une scène où Chen révèle à Alex l'existence des Archives cachées."

**Résultat :** La nouvelle scène est ajoutée à la fin du fichier

---

### 3. **Créer** (Create)
Crée un tout nouveau fichier.

**Exemple d'instruction :**
> "Crée le chapitre 8 : Alex découvre la vérité sur son passé dans les Archives."

**Résultat :** Un nouveau fichier `chapitres/chapitre_08.md` est créé

---

### 4. **Modifier** (Edit)
Modifie un passage spécifique tout en gardant le reste.

**Exemple d'instruction :**
> "Améliore le dialogue entre Alex et Chen, rends-le plus philosophique et profond."

**Résultat :** Seul le dialogue est modifié, le reste du chapitre reste intact

---

## 📝 Workflow typique

### Étape 1 : Choisir l'action
```
┌─────────────────────────────┐
│ Action : [Réécrire ▼]      │
└─────────────────────────────┘
```

### Étape 2 : Sélectionner le fichier
```
┌─────────────────────────────┐
│ Fichier : chapitres/        │
│   ├─ chapitre_01.md         │
│   ├─ chapitre_02.md ← ici   │
│   └─ chapitre_03.md         │
└─────────────────────────────┘
```

### Étape 3 : Donner des instructions
```
┌──────────────────────────────────────────┐
│ Instructions pour l'IA :                 │
│ ┌──────────────────────────────────────┐ │
│ │ Réécris ce chapitre en ajoutant     │ │
│ │ plus de tension et de suspense.      │ │
│ │ Amplifie le conflit intérieur d'Alex.│ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### Étape 4 : Prévisualiser
```
[ 👁️ Voir le résultat ]  ← Clic !
```

**L'IA génère le contenu (5-10s)...**

### Étape 5 : Comparer
```
┌─────────────────────┬─────────────────────┐
│ ORIGINAL            │ NOUVEAU (IA)        │
├─────────────────────┼─────────────────────┤
│ Alex regarda Chen.  │ Alex fixa Chen,     │
│ « C'est impossible  │ l'incrédulité       │
│ », dit-il.          │ peignant son visage.│
│                     │ « C'est impossible, │
│                     │ tu le sais bien. »  │
└─────────────────────┴─────────────────────┘
```

### Étape 6 : Valider ou ajuster
```
[ ✓ Sauvegarder ]  [ ✗ Annuler ]  [ 🔄 Régénérer ]
```

- **Sauvegarder** :  Confirme et écrit le fichier
- **Annuler** : Rejette et revient à l'original
- **Régénérer** : Redemande à l'IA (nouvelle variation)

### Étape 7 : Confirmation finale
```
⚠️ Confirmer: Réécriture de chapitres/chapitre_02.md ?
   [ Oui ]  [ Non ]
```

### Étape 8 : Résultat
```
✅ Fichier écrit avec succès !

Fichier: chapitres/chapitre_02.md
Temps: 8.45s
💾 Backup créé: chapitre_02_20251223_114530.md
```

---

## 🔒 Sécurité

### Backup automatique
**Avant chaque modification, un backup est créé :**
```
data/.backups/anomalie2084/
  ├─ chapitre_01_20251223_103000.md
  ├─ chapitre_01_20251223_110500.md
  └─ chapitre_02_20251223_114530.md
```

**Format du nom :** `fichier_AAAAMMJJ_HHMMSS.md`

**Pour restaurer un backup :**
1. Allez dans `data/.backups/anomalie2084/`
2. Copiez le fichier backup
3. Remplacez le fichier actuel

### Double validation
1. **Prévisualisation obligatoire** - Vous voyez le résultat avant sauvegarde
2. **Confirmation manuelle** - Popup de confirmation

### Limitations
- ✅ Ne peut modifier QUE dans `data/`
- ✅ Extensions autorisées : `.md`, `.txt`
- ✅ Taille max : 50 000 caractères

---

## 💡 Exemples d'instructions efficaces

### ✅ BON - Instructions précises

**Pour réécrire :**
> "Réécris ce chapitre du point de vue de Chen au lieu d'Alex. Garde les mêmes événements mais change la perspective narrative."

**Pour ajouter :**
> "Ajoute une scène de 500 mots où Alex explore les ruines du vieux serveur et découvre un message crypté."

**Pour modifier :**
> "Réécris le dialogue entre Alex et Chen (lignes 45-78) en utilisant plus de métaphores liées à la technologie et moins de langage direct."

### ❌ MAUVAIS - Instructions vagues

> "Améliore ce chapitre"  
→ Trop vague, l'IA ne sait pas quoi améliorer

> "Fais quelque chose de bien"  
→ Pas d'instructions concrètes

> "Change tout"  
→ Pas de direction claire

---

## 📊 Performance

### Temps de génération typiques

| Action | Longueur | Temps |
|--------|----------|-------|
| Réécrire chapitre (2000 mots) | Long | 8-12s |
| Ajouter scène (500 mots) | Moyen | 5-8s |
| Modifier dialogue (200 mots) | Court | 3-5s |
| Créer nouveau chapitre | Long | 10-15s |

**Facteurs influençant la vitesse :**
- Longueur du contenu à générer
- Complexité des instructions
- Nombre de fichiers de contexte

---

## 🎨 Conseils d'utilisation

### 1. Commencez avec "Ajouter"
Si vous n'êtes pas sûr, commencez par **ajouter** du contenu plutôt que réécrire. C'est moins risqué.

### 2. Utilisez des instructions spécifiques
Plus vos instructions sont précises, meilleur sera le résultat.

### 3. Itérez avec "Régénérer"
Si le premier résultat ne vous plaît pas, cliquez "Régénérer" pour obtenir une variation.

### 4. Modifiez manuellement après
Le contenu généré est un **point de départ**. N'hésitez pas à l'éditer après sauvegarde.

### 5. Gardez vos backups
Les backups sont dans `.backups/` - ils ne sont jamais supprimés automatiquement.

---

## 🐛 Troubleshooting

### "Erreur 500" lors de la génération
**Cause :** Problème de clé API ou prompt trop long  
**Solution :** Vérifiez vos crédits OpenRouter

### Le résultat ne correspond pas à la demande
**Cause :** Instructions trop vagues  
**Solution :** Soyez plus précis dans vos instructions

### Le fichier n'est pas sauvegardé
**Cause :** Vous n'avez pas cliqué "Sauvegarder"  
**Solution :** La prévisualisation ne sauvegarde pas, il faut valider

### "Chemin non autorisé"
**Cause :** Tentative d'écriture hors de `data/`  
**Solution :** Sécurité normale, choisissez un fichier dans le projet

---

## 📝 Réindexation après modifications

**Important :** Après avoir modifié vos chapitres, **réindexez** pour que l'IA en tienne compte :

```bash
python -m src.indexer anomalie2084
```

Ou utilisez le bouton "Réindexer" dans l'interface web.

---

## 🎯 Prochaines étapes

1. **Testez le Writer Mode !**
2. Commencez par une petite modification (action "Ajouter")
3. Vérifiez le résultat dans la prévisualisation
4. Sauvegardez si satisfait
5. Itérez et améliorez

---

**Le Writer Mode est un assistant, pas un remplaçant.**  
Vous restez le créateur principal de votre univers ! ✨

---

**Date :** 2025-12-23  
**Version :** Writer Mode v1.0  
**Status :** ✅ Opérationnel
