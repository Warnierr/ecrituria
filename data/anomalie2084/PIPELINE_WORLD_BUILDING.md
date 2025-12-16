# 🧠 PIPELINE DE WORLD BUILDING — CI/CD D'ÉCRITURE

Ce document complète `ARCHITECTURE.md` et sert de référentiel Obsidian/agent IA pour garantir la cohérence du monde narratif en continu.

---

## 0. RÈGLE D'OR

- Le monde ne doit jamais servir l'intrigue de façon magique.
- L'intrigue doit émerger des règles du monde.

---

## 1. ARCHITECTURE GLOBALE DU MONDE (ROOT)

### 1.1 Identité du Monde

- Nom du monde :
- Genre :
- Ton dominant :
- Niveau de réalisme :
- Inspiration dominante :

✅ **Validation IA**  
- Le ton est-il stable ?  
- Y a-t-il des contradictions de genre ?

### 1.2 Lois Fondamentales (INVIOLABLES)

- Lois physiques :
- Lois sociales :
- Lois technologiques :
- Lois spirituelles/magiques :
- Lois politiques :

✅ **Test IA**  
- Un événement du récit viole-t-il une loi sans explication ?

---

## 2. TEMPORALITÉ

### 2.1 Timeline Globale

- Ère 1 :
- Ère 2 :
- Ère 3 :
- Présent de l'histoire :

### 2.2 Rythme du Monde

- Vitesse d'évolution :
- Temps long / temps court :
- Mémoire collective :

✅ **Test IA**  
- Un événement ancien a-t-il encore un impact logique ?

---

## 3. GÉOGRAPHIE & LIEUX

### 3.1 Carte Mentale

Pour chaque lieu :

- Nom :
- Type :
- Climat :
- Ressources :
- Dangers :
- Population :
- Rôle dans l'histoire :

✅ **Test IA**  
- Ce lieu pourrait-il exister physiquement ?  
- Sert-il à autre chose que le décor ?

---

## 4. PERSONNAGES (DOSSIER VIVANT)

### 4.1 Fiche Personnage Standard

- Nom :
- Âge :
- Origine :
- Statut social :
- Métier/fonction :
- Caractère dominant :
- Peurs :
- Désirs :
- Blessure fondatrice :
- Contradiction interne :
- Objectif conscient :
- Objectif inconscient :
- Rapports importants :
- Ce qu'il cache :

✅ **Test IA**  
- Le personnage agit-il selon ses peurs ou selon les besoins de scénariste ?  
- Son évolution est-elle progressive ?

---

## 5. OBJETS, RELIQUES, TECHNOLOGIES

Pour chaque objet important :

- Nom :
- Origine :
- Fonction :
- Limite :
- Prix à payer :
- Qui le contrôle ?
- Qui le convoite ?

✅ **Loi**  
- Tout pouvoir doit avoir un coût narratif.

---

## 6. SOCIÉTÉS, PEUPLES, FACTIONS

- Nom :
- Organisation :
- Valeurs :
- Tabous :
- Vision de la mort :
- Vision du pouvoir :
- Ennemis :
- Mythes fondateurs :

✅ **Test IA**  
- Une scène pourrait-elle exister telle quelle dans un autre peuple ?  
  - Si oui : peuple pas assez distinct.

---

## 7. NARRATION & POINT DE VUE

- Type de narration :
- Focalisation :
- Fiabilité du narrateur :
- Distance émotionnelle :

✅ **Test IA**  
- Le lecteur sait-il plus que le personnage ?  
- Est-ce volontaire ?

---

## 8. CONTINUITÉ (ANTI-INCOHÉRENCE)

Checklist automatique à chaque chapitre :

- Âges cohérents
- Lieux cohérents
- Relations cohérentes
- Capacités cohérentes
- Technologies cohérentes
- Chronologie cohérente

✅ **Mission IA**  
- Lister toutes les incohérences potentielles.

---

## 9. SYMBOLIQUE & THÉMATIQUE

- Thème principal :
- Thèmes secondaires :
- Symboles récurrents :
- Objets métaphoriques :
- Évolution symbolique :

✅ **Test IA**  
- Le symbole évolue-t-il comme le personnage ?

---

## 10. PIPELINE CI/CD D'ÉCRITURE

- 🟢 **COMMIT — Écriture brute** : écrire sans filtre.
- 🔵 **BUILD — Vérification logique IA** : cohérence monde/personnages/chronologie.
- 🟠 **TEST — Impact émotionnel** : tension ? malaise ? question ?
- 🔴 **DEBUG — Nettoyage** : supprimer surcharge, dialogues inutiles, exposition trop explicite.
- ✅ **DEPLOY — Intégration monde** : lier lieux, personnages, timeline et symboles.

---

## 11. MÉMOIRE IA (CONSIGNE À STOCKER EN CONTEXTE)

L'agent doit toujours privilégier :

- La cohérence au spectaculaire
- Les conséquences aux rebondissements gratuits
- La lenteur quand il faut
- Le silence quand c'est plus fort que le dialogue

---

## 12. STRUCTURE OBSIDIAN RECOMMANDÉE

```
/Monde
  /Timeline
  /Cartes
  /Peuples
  /Factions
/Personnages
/Objets
/Lieux
/Chapitres
/Symboles
/Logs_IA
```

---

## 13. PROMPT SYSTÈME POUR L'AGENT IA

> Tu es l'architecte du monde.  
> Tu vérifies systématiquement la cohérence, la continuité, la psychologie, les lois du monde, la symbolique et l'impact émotionnel.  
> Tu proposes, mais tu n'imposes jamais.  
> Tu signales toute incohérence même légère.  
> Tu t'appuies sur les fichiers Obsidian comme source de vérité.

---

## Ressources complémentaires

- Templates Obsidian par type (personnage, lieu, faction, objet) — à générer si besoin.
- Version JSON/YAML pour automatisation agent — possible sur demande.
- Intégration au RAG narratif (`src/indexer.py`, `src/rag.py`) — brancher les dossiers Obsidian comme source de vérité.


