# 0.2.0 — rendre les preuves et les dossiers contrôlables

Cette version répond à l’audit du pilote en renforçant les 11 modules existants.
La note de 17,5/20 donnée dans l’audit reste une appréciation, pas une mesure du dépôt.

| Axe de l’audit | Livré | Preuve / limite |
|---|---|---|
| Articulation juridique | Dossier structuré, faits/pièces, conditions, objections, moyens et effets ; outil `review_case` | Références et structure contrôlées ; pertinence juridique non automatisée |
| Pièces locales | Cohérence des références, empreintes attendues, liens entre pièces, dossier autorisé | Absence, changement de version et retrait testés ; pas OCR |
| Droit dans le temps | Date applicable distincte de la connaissance disponible ; notes conservées | Réexamen signalé ; effets transitoires à analyser |
| Jurisprudence administrative | Import XML CE/CAA/TA, recherche filtrée, provenance et lecture de la portée | 522 décisions importées sur trois lots ; trois décisions consultées de bout en bout |
| Sécurité et conservation | Archive facultative par principal, intégrité, retraits, fermeture des accès HTTP aux magasins locaux | Poste/opérateur de confiance ; pas service distant partagé |
| Évaluation | Six dossiers fictifs, contrôle de comparabilité, liaison réponse/relecture, sondes exécutables | Benchmark humain non exécuté ; essais par agent distincts |
| PISTE | Recette réelle exécutable et rapport explicite des prérequis absents | Accès manquants : aucune connexion authentifiée validée |

Voir le [rapport de validation](validation.md), les [preuves d’import](admin-probes-0.2.0.json)
et l’[état du benchmark](../evals/benchmark-0.2.0.json).

## Prochaines preuves à obtenir

1. Qualifier PISTE avec des accès autorisés, puis les versions et erreurs réelles.
2. Geler un corpus nouveau préparé par des juristes territoriaux ; exécuter les
   configurations comparables et faire relire indépendamment les réponses.
3. Mesurer les erreurs critiques, la recherche CE/CAA/TA et la couverture métier.
4. Étendre seulement ensuite la veille, la couverture et les essais multi-modèles.

La publication de cette version ne franchit pas ces étapes à leur place.
