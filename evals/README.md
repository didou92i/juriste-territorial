# Évaluer la méthode sans surpromesse

`cases.jsonl` reprend les 40 situations de recette du plan fourni. Il s'agit
d'attendus à développer et qualifier, pas de 40 conversations réussies.
Chaque ligne conserve explicitement l'état non exécuté du benchmark et de la revue humaine.
Les six `development-cases.jsonl` et la [régression CAP AEPE](regression-cap-aepe.jsonl)
sont publics : utiles pour éviter un retour en arrière, mais impropres à mesurer
la généralisation. Un corpus privé de 12 dossiers synthétiques FPT, actes,
compétences et contentieux est préparé localement dans `private/evals/`, ignoré
par Git. Son [manifeste d'empreintes](holdout-manifest.json) est public afin de
figer la version candidate sans publier les dossiers. Il n'a encore été ni
exécuté ni relu par deux juristes.

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
émis, résultats récupérés, version de méthode, durée, appels HTTP et coût déclaré
s'il est réellement connu. Un coût non déclaré reste inconnu, jamais zéro.
Un identifiant présent dans une requête ne suffit pas : vérifier sa présence
dans une réponse officielle de consultation.

## Jugement et mesures

Les contrôles déterministes portent sur identité, citations retrouvées,
intervalle de version, erreurs, bornes et accès. Le relecteur juridique examine
qualification, compétence, application, exceptions, portée des décisions,
pertinence de l'action et traitement des objections. Aucun LLM juge ne suffit seul.

Rapporter séparément : références non étayées, erreurs de version et de portée,
décisions pertinentes retrouvées parmi un jeu de référence revu, conclusions
déterminantes sans preuve/réserve, réserves utiles, demandes de pièces inutiles,
actions réalisables, durée, appels, coût déclaré et pannes. Ne pas récompenser un refus
global qui évite de traiter les parties pourtant établissables.

L'objectif est une amélioration mesurée de la méthode. Aucun gain chiffré par
rapport au modèle seul n'est revendiqué pour cette version.

## Exécuter le contrôle de campagne

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

Une campagne compare un modèle/version à la fois, avec le même ensemble d’outils
de base, paramètres et budget pour `baseline` et `skill`. Le bras `skill_mcp`
ajoute les outils MCP documentés, avec le même plafond de recherche. Les traces
d'outils et les durées permettent de constater les différences réelles.
Les pièces changées, avis liés à une autre réponse, paires manquantes ou divergences
entre relecteurs sont signalés. Les identités et exécutions fournies sont des
**déclarations de l’opérateur**, pas une preuve d’identité ou un journal signé.
Une revue par agent ne compte jamais comme revue juridique humaine.

Le [résultat actuel](benchmark-0.2.0.json) constate les six paires manquantes.
Le [nouvel essai par agent](forward-test-0.2.0.md) explore deux de ces cas ;
il ne les transforme pas en corpus inconnu ou en benchmark humain.

## Corpus inédit et relecture aveugle

Ne publier ni les 12 cas privés ni les réponses avant la fin du test. Geler
corpus, modèle/version, paramètres, budget, méthode et jeux de références ;
exécuter les trois modes par dossier et conserver `case_hash`, `method_hash`,
`tool_events`, `duration_ms`, `network_requests` et `reported_cost_eur` si connu.
Préparer un paquet sans clé de modes, puis en confier une copie à chaque juriste :

```bash
uv run python scripts/prepare_review.py \
  --cases private/evals/holdout-2026-09-22.jsonl \
  --manifest evals/holdout-manifest.json \
  --runs private/evals/runs.jsonl \
  --out private/evals/review-packet.jsonl \
  --map private/evals/operator-map.json
```

Chaque juriste renseigne séparément `Review` et `ReviewMetrics`, sans accès à
`operator-map.json` ni à la réponse de l'autre. L'opérateur réconcilie les
`blind_id` avec les `run_id`, conserve les désaccords, puis lance :

```bash
uv run python scripts/evaluate_benchmark.py \
  --cases private/evals/holdout-2026-09-22.jsonl \
  --manifest evals/holdout-manifest.json \
  --runs private/evals/runs.jsonl \
  --reviews private/evals/reviews.jsonl
```

`private_holdout` exige trois réponses comparables et deux revues humaines
indépendantes concordantes par réponse. Les désaccords restent signalés jusqu'à
arbitrage documenté. Les identités des juristes restent des déclarations de
l'opérateur ; le script ne certifie pas leurs qualifications, l'aveugle effectif
ni la justesse du corrigé. L'état demeure `incomplete` avant ces opérations.
