# Essai indépendant — juriste-territorial 0.2.0

Date : 15 septembre 2026. Essai effectué par un agent, sans validation humaine. Les deux dossiers sont fictifs ; aucune décision réelle n’est attribuée à un tribunal.

## dev-01 — Annonce d’une aide aux adhérents

**Non : les pièces ne permettent pas d’annoncer un droit certain au versement.** Dans ce cas fictif, il s’agit de la gouvernance interne d’un syndicat d’adhérents, pas d’un établissement intercommunal.

Les **statuts.txt** réservent au conseil syndical la création des prestations et le vote du budget ; le bureau exécute ses décisions. Le **projet.txt** du 12 septembre 2026 ne prouve donc pas, seul, l’adoption de l’aide. L’accord oral du trésorier est seulement rapporté par le secrétaire dans **courriel.txt** : même confirmé, il ne remplacerait ni la décision de l’organe compétent ni la délégation écrite et précise exigée par les statuts. L’absence de ces pièces au dossier ne prouve pas qu’elles n’existent pas.

**Formulation proposée :**

> Le bureau propose une aide de 70 € pour les adhérents participant à la grève du 29 septembre 2026. Le projet prévoit une cotisation à jour lors de la demande et un dépôt avant le 30 novembre 2026. La création de cette aide, son financement et ses modalités restent à confirmer par une décision prise conformément aux statuts. Aucun versement n’est garanti à ce stade.

**Action utile :** obtenir la décision du conseil créant et finançant l’aide ou, si une délégation est invoquée, son texte et la décision prise dans son champ. À défaut, soumettre le projet au conseil. Vérifier ensuite les conditions adoptées et l’habilitation du signataire avant une annonce ferme.

## dev-04 — Portée d’un rejet en référé

**Non : la conclusion de la note doit être corrigée.** L’extrait est exclusivement fictif.

Dans **ordonnance-fictive.txt**, l’atteinte au principe d’égalité est un **argument du requérant**. Le **motif du juge** est uniquement l’absence d’urgence ; il indique expressément ne pas examiner les moyens. Le **dispositif** rejette la requête en référé. Il n’écarte donc pas l’argument d’égalité et ne valide pas la légalité du tarif.

Le rejet signifie ici que cette ordonnance n’accorde pas la suspension demandée. Il ne préjuge pas de l’issue au fond. Cette distinction correspond à l’office du juge des référés, qui ne statue pas sur le principal : [CJA, article L. 511-1](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000006449324/2024-04-21).

**Formulation proposée :**

> Le juge des référés a rejeté la demande de suspension pour défaut d’urgence, sans examiner les moyens de légalité, notamment celui tiré du principe d’égalité. Cette ordonnance n’établit pas la légalité du tarif.

**Action utile :** remplacer la conclusion de la note par cette formulation. Dans un dossier réel, consulter la décision intégrale et vérifier l’état du recours au fond avant toute affirmation sur sa portée ; aucune échéance ne peut être calculée avec cet extrait.

## Ressources effectivement consultées

### Pièces et méthode

- `evals/development-cases.jsonl` : uniquement les entrées dev-01 et dev-04 et leurs cinq pièces intégrées.
- `skills/juriste-territorial/SKILL.md`.
- Dans ce même dossier de skill : `references/methode.md`, `references/competence.md`, `references/preuve-et-recherche.md`, `references/jurisprudence.md`, `modules/contentieux.md`.

### Source officielle et limites d’accès

- [Légifrance — CJA, L. 511-1, LEGIARTI000006449324](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000006449324/2024-04-21), consulté le 15 septembre 2026 : texte de l’article lu, version affichée en vigueur depuis le 1er janvier 2001. URL historique au 21 avril 2024 ; l’accès demandé à la date du 15 septembre 2026 a échoué. Cette source corrobore la distinction procédurale ; l’analyse du cas découle directement de l’extrait fictif.
- Recherches abstraites des articles L. 511-1 et L. 521-1, sans données personnelles. Accès direct à L. 521-1 infructueux : cet article n’est pas employé comme preuve. Les résultats de recherche non officiels n’ont pas servi de sources.
- Aucun outil MCP `get_source_status` / `get_methodology` disponible dans l’inventaire interrogé.

Aucun test, attendu, code ou historique d’autres évaluations consulté. Aucun envoi, publication ou modification du dépôt.
