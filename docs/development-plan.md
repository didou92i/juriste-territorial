# Plan initial et progression

Le tableau ci-dessous décrit la livraison **0.1.0**. L’index administratif,
l’archive persistante, les dossiers structurés et le contrôleur d’évaluation
sont désormais livrés en [0.2.0](release-0.2.0.md). Les qualifications PISTE,
juridiques humaines et sur corpus nouveau restent à obtenir.

## État historique 0.1.0

## Décision

Construire un produit unique avec un noyau canonique, des modules chargés à la
demande et une bibliothèque de sources indépendante du MCP. La première
livraison est un pilote local utilisable et testable. Les portes de validation
ci-dessous ne sont pas considérées franchies du seul fait de publier le dépôt.

| Lot du plan initial | Livré dans cette version | Suite nécessaire |
|---|---|---|
| 0 — Reprises et licences | Inventaire par fichier, commits, empreintes, adaptation CC BY-SA et code original MIT | Réexaminer avant toute nouvelle reprise |
| 1 — Schémas | Dossier, faits, source, preuve, intervalle, affirmation et erreurs | Ajouter les schémas métier au besoin |
| 2 — Skill | Noyau, méthode, compétence, temps, articulation, preuve et restitutions | Étendre les essais à des dossiers moins proches des exemples |
| 3 — Textes datés | Adaptateur Légifrance, recherche/fetch/version/diff et contrats simulés | Recette authentifiée avec accès PISTE et réponses réelles |
| 4 — Justice administrative | CETAT, références ArianeWeb/open data, lecteur de pages | Import XML, index, dédoublonnage, retrait et couverture mesurée |
| 5 — Judiciaire/autres | Adaptateur JudiLibre, taxonomie, lecteur officiel et registre | Recette authentifiée ; adaptateurs UE/constitutionnels spécialisés si requis |
| 6 — Preuves | Instantanés, hash, citations, dates et contrôle technique | Archivage pérenne des dossiers et graphe de dépendances complet |
| 7 — Pièces locales | Import TXT/MD, original conservé, accès par identité/dossier, révocation | PDF/OCR revu et authentification d'un service partagé |
| 8 — Territoire pilote | Guides institutions, actes, FPT, dialogue social et contentieux | Corpus métier complet et revue juridique humaine indépendante |
| 9 — Commande publique | Module et deux tests de montant datés, frontières testées | Autres branches, publicité/délais et qualification humaine du registre |
| 10 — Autres métiers | Modules d'orientation et d'analyse expérimentaux | Recette distincte par domaine avant promotion de maturité |
| 11 — MCP/distribution | 11 outils, ressources, prompt, stdio et HTTP local, skill et wheel | Tests dans les applications cibles ; HTTPS/OAuth partagé si choisi |
| 12 — Maintenance | Procédure, liste de retrait, CI et versions | Détection automatique et propositions de changement, sans promotion automatique |
| 13 — Benchmark | 40 situations recensées, protocole comparatif, essai sur trois demandes | Trois campagnes réelles et revue juridique des réponses |

## Ordre recommandé pour la suite

1. **Activer et qualifier PISTE.** Souscrire aux API, injecter les accès via le
   gestionnaire de secrets, exécuter des recherches/fetch/versions sur des cas
   officiels connus, conserver des réponses de contrat minimisées.
2. **Qualifier la méthode sur le périmètre prioritaire.** Faire préparer les
   pièces et attendus de cas FPT, délégations, actes et contentieux par un juriste ;
   exécuter le benchmark et corriger les erreurs observées.
3. **Compléter la justice administrative.** Index XML avec couverture explicite,
   correction/retrait, provenance officielle et décisions anciennes via ArianeWeb.
4. **Choisir le déploiement.** Conserver stdio si l'usage reste individuel ;
   concevoir identité, autorisation par dossier et OAuth avant un service partagé.

## Critères de passage à un usage opérationnel qualifié

Appels API réels réussis ; sources et versions confirmées ; cas métier relus par
une personne compétente ; aucune erreur critique connue sur le corpus retenu ;
limites et coûts observés publiés ; accès, conservation et correction adaptés
au contexte d'hébergement. La réussite d'un corpus ne garantit pas les cas hors corpus.
