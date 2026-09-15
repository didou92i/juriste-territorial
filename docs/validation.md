# Validation de la version 0.2.0

Date : **15 septembre 2026**. Statut : **pilote expérimental**.

| Vérification exécutée | Résultat | Portée |
|---|---|---|
| Python 3.12.5, macOS | **122 réussis, 1 ignoré** | Contrats, sources simulées, accès, preuves, dossiers, règles et MCP |
| Ruff, validateur de skill, liens et contrat des outils | Réussite | Qualité statique et présence des 14 outils |
| Wheel installé en environnement isolé et ZIP du skill | Réussite | Version, schéma de dossier et méthode embarquée contrôlés |
| MCP stdio et HTTP 127.0.0.1 | Réussite | Client SDK réel, 14 outils, ressources, prompt ; magasins locaux désactivés en HTTP |
| Import officiel CE/CAA/TA | **522 décisions** | 40 CE, 211 CAA, 271 TA dans trois lots historiques |
| Recherche puis consultation réelle | **3 décisions** | Pagination complète, empreintes texte/XML/ZIP et citation retrouvée |
| Essai indépendant par agent | **2 réponses examinées** | Gouvernance privée et portée d’un référé, sans validation humaine |
| Campagne comparative | **Non exécutée** | Six dossiers disponibles, aucune paire de réponses avec revue humaine |
| Recette PISTE | **Non exécutée** | Identifiants absents ; sondes historique, courant et requête improbable signalées `not_run` |

Les tests ignorés ne sont pas des réussites. Le test HTTP local nécessite une
permission d’ouverture de port ; il a été exécuté après le refus technique du
bac à sable. Aucune panne d’un fournisseur n’a été provoquée pour la recette.

## Éléments contrôlables

- [Sondes CE/CAA/TA](admin-probes-0.2.0.json) : URL, compte, dates et empreintes.
- [Sondes PISTE](piste-probes-0.2.0.json) : prérequis réellement absents.
- [État du benchmark](../evals/benchmark-0.2.0.json) : incomplet, sans gain annoncé.
- [Essai par agent](../evals/forward-test-0.2.0.md) : réponses et ressources consultées.
- [Validation historique 0.1.0](validation-0.1.0.md), conservée séparément.

Les nouvelles régressions couvrent faux identifiants, citation inventée, fait
contesté, date de connaissance dépassée, annexe absente, attribution non certifiée,
archive après redémarrage, mauvais principal, pièce d’un autre dossier, retrait,
corruption, ZIP dangereux, DTD, pagination et campagnes non comparables.

## Non démontré

Pertinence sémantique de toutes les réponses, exhaustivité des conditions,
robustesse nationale CE/CAA/TA, benchmark comparatif humain, performances sur
cas nouveaux, accès PISTE/JudiLibre authentifiés, veille automatisée ou service
multiutilisateur. Les six dossiers publics restent des cas de développement.

La CI Linux Python 3.12/3.13 et la distribution doivent être contrôlées sur le
commit publié. Voir les résultats Actions et les artefacts de la release.
