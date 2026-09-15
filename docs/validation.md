# Validation de la version 0.1.0

Date : **15 septembre 2026**. Statut : **pilote expérimental**.

## Vérifications réellement exécutées

| Vérification | Résultat observé | Portée |
|---|---|---|
| Suite Python, macOS, Python 3.12.5 | **91 tests réussis, 1 ignoré** | Unités, contrats simulés, erreurs, accès, dates, règles et MCP |
| Lint et format Ruff | Réussite | Qualité statique du code livré |
| Validateur `skill-creator` | Réussite | Frontmatter et structure du skill |
| Liens internes et outils annoncés | Réussite | Tous les renvois du skill et ses 11 outils existent |
| MCP stdio | Réussite | Initialisation, liste, appels, ressources et prompt via client SDK réel |
| MCP HTTP sur 127.0.0.1 | Réussite | Initialisation/appels réels ; accès aux pièces privées désactivé |
| Source distante : portail open data administratif | Lecture réussie | Extraction HTML, sans certification de complétude/version |
| Source distante : page Légifrance | Refus HTTP 403 correctement remonté | Aucune prétendue récupération du texte |
| Essai de méthode par un agent distinct | Trois réponses examinées, aucun défaut matériel signalé | Cas fictifs IHTS, transition de seuil et compétence/signature |

Les tests ignorés ne comptent pas comme réussites. Le test API Légifrance est
ignoré faute d'activation explicite et d'accès PISTE configurés. JudiLibre est
testé sur son contrat simulé, pas sur un accès authentifié réel.

Les [sondes publiques](live-probes.json) consignent URL, résultat et empreinte
lorsque le contenu a été récupéré. Le [rapport d'essai](../evals/forward-test-2026-09-15.md)
précise le périmètre de la passe indépendante par agent.

## Cas techniques couverts

Version historique/future, début absent, fin absente/invalide/ouverte et borne
exclusive ; identifiant absent ou différent dans la réponse ; citation inventée ;
source officielle à applicabilité inconnue ; réponse incomplète ; panne/quota ;
renouvellement OAuth borné ; destinations réseau refusées ; pagination stable ;
requêtes de texte et CETAT séparées ; taxonomie judiciaire ; code erroné ;
dates de jugement/publication séparées ; accès privés, retrait et intégrité ;
seuils exacts, HT/TTC, type d'acheteur et fait générateur.

Le test d'injection logiciel vérifie que le texte reste une donnée non fiable ;
l'essai par agent observe un comportement sur un exemple. Cela ne garantit pas
une résistance générale de tous les modèles à toutes les injections.

## Distribution

Le skill est empaqueté depuis sa source canonique. Le wheel embarque la méthode,
les registres et les notices ; leur présence et leur concordance sont contrôlées
lors du test d'installation isolé. Les archives n'incluent aucun document privé
ni environnement virtuel.

La CI exécute la suite sous Linux avec Python 3.12 et 3.13. Son résultat distant
reste consultable dans l'onglet Actions du dépôt et doit être vérifié pour le
commit distribué ; ce tableau rapporte les résultats locaux ci-dessus.

## Non démontré par cette version

- Validité juridique générale, revue humaine indépendante ou gain chiffré face au modèle seul.
- Campagne comparative des 40 situations, qualification métier de tous les modules.
- Succès des endpoints avec une application PISTE réelle, disponibilité future des fournisseurs.
- Exhaustivité nationale des décisions, indexation XML, extraction OCR ou PDF.
- Installation et comportement dans chaque client final, service distant multiutilisateur.

Voir le [plan de qualification](development-plan.md) pour les étapes restantes.
