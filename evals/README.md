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
