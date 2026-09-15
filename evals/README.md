# Évaluer la méthode sans surpromesse

`cases.jsonl` reprend les 40 situations de recette du plan fourni. Il s'agit
d'attendus à développer et qualifier, pas de 40 conversations réussies.
Chaque ligne conserve explicitement l'état non exécuté du benchmark et de la revue humaine.

Un premier [essai indépendant par agent](forward-test-2026-09-15.md) porte sur
trois demandes fictives. Il a utilisé le skill et des pages officielles ;
il ne teste pas le MCP et ne remplace pas une revue juridique humaine.

## Protocole comparatif

Pour un corpus gelé, utiliser le même modèle, version, paramètres, dossiers,
fenêtre temporelle et budget de recherche dans les trois configurations :

1. Modèle seul, avec les capacités documentaires de base explicitement décrites.
2. Même modèle avec le skill, capacités de base identiques.
3. Même modèle avec le skill et le MCP, accès effectivement configurés.

Rendre les dossiers et cas complets avant la campagne : pièces fictives, dates,
réponses officielles de référence et cas contradictoires. Ne pas donner les
attendus au modèle évalué. Répéter les cas sensibles et les variantes de panne.

Conserver pour chaque exécution : `case_id`, configuration, modèle/version,
horodatage, prompt, empreinte des pièces, réponse, événements d'outils réellement
émis, résultats récupérés, version de méthode, temps et coût observables.
Un identifiant présent dans une requête ne suffit pas : vérifier sa présence
dans une réponse officielle de consultation.

## Jugement et mesures

Les contrôles déterministes portent sur identité, citations retrouvées,
intervalle de version, erreurs, bornes et accès. Le relecteur juridique examine
qualification, compétence, application, exceptions, portée des décisions,
pertinence de l'action et traitement des objections. Aucun LLM juge ne suffit seul.

Rapporter séparément : références non étayées, erreurs de qualification,
conclusions déterminantes sans preuve/réserve, demandes de pièces inutiles,
actions réalisables, coût de recherche et pannes. Ne pas récompenser un refus
global qui évite de traiter les parties pourtant établissables.

L'objectif est une amélioration mesurée de la méthode. Aucun gain chiffré par
rapport au modèle seul n'est revendiqué pour cette version.

## Exécuter le contrôle de campagne (0.2.0)

`development-cases.jsonl` contient six demandes avec pièces synthétiques complètes.
Donner au modèle uniquement `prompt` et `pieces` du cas ; garder le
[guide de relecture](reviewer-guide.md) hors de son contexte.

```bash
uv run python scripts/evaluate_benchmark.py
uv run python scripts/evaluate_benchmark.py --runs runs.jsonl --reviews reviews.jsonl
uv run python scripts/qualify_sources.py
```

Sans exécutions, la première commande annonce `incomplete`, jamais une réussite.
Ces scripts n’appellent aucun modèle payant. La dernière sonde peut effectuer
les appels PISTE si des accès sont déjà fournis à l’environnement.

Les schémas exacts sont `Run` et `Review` dans `src/droit_territorial/evaluation.py`.
Un `Run` conserve modèle/version, paramètres, outils, budget, date de connaissance,
répétition, réponse et événements d’outils. Calculer `case_hash` avec
`fingerprint(cas_complet)` et `response_hash` avec `fingerprint(reponse)` ; cette
fonction sérialise en JSON canonique avant SHA-256. `method_hash` identifie le
skill réellement utilisé, par exemple l’empreinte de son ZIP de distribution.

Une campagne compare un modèle/version à la fois, avec le même ensemble d’outils,
paramètres et budget pour `baseline` et `skill`. `skill_mcp` reste séparé.
Les pièces changées, avis liés à une autre réponse, paires manquantes ou divergences
entre relecteurs sont signalés. Les identités et exécutions fournies sont des
**déclarations de l’opérateur**, pas une preuve d’identité ou un journal signé.
Une revue par agent ne compte jamais comme revue juridique humaine.

Le [résultat actuel](benchmark-0.2.0.json) constate les six paires manquantes.
Le [nouvel essai par agent](forward-test-0.2.0.md) explore deux de ces cas ;
il ne les transforme pas en corpus inconnu ou en benchmark humain.
