# Un dossier, de la question à la position juridique

**Exemple fictif : une direction demande si un projet de contrat peut être signé.** Le dossier comprend le projet, une délibération faisant référence à une annexe et un arrêté de délégation. L’annexe n’a pas été transmise.

Ce parcours illustre la méthode. Les extraits ci-dessous sont des exemples de restitution ; ils ne sont pas présentés comme une consultation juridique exécutée sur un dossier réel.

## 1. Poser la question qui commande l’action

L’assistant identifie l’objectif, la personne morale, le type de contrat, la qualité du signataire et les dates pertinentes. Il cherche à savoir si la question porte sur la compétence, le contenu du contrat, la procédure ou plusieurs de ces points.

**Résultat attendu :** un périmètre d’analyse précis. Le simple fait qu’un contrat soit signé ou vise une délibération ne suffit pas à démontrer toute la chaîne de pouvoir.

## 2. Distinguer ce qui est établi et ce qui reste à prouver

| Élément du dossier fictif | Traitement méthodologique |
|---|---|
| Le projet vise une délibération | Constater le visa et consulter la délibération concernée. |
| La délibération renvoie à une annexe | Identifier le contenu attendu et demander cette pièce si elle détermine le champ de l’autorisation. |
| Un arrêté de délégation est fourni | Examiner l’auteur, le bénéficiaire, le champ, les exclusions et les dates. |
| Le service affirme que « tout a été validé » | Conserver cette affirmation comme déclaration tant que ses éléments de preuve ne sont pas établis. |

La demande complémentaire doit expliquer son utilité : **quel point l’annexe permettrait-elle de trancher ?** Les parties du dossier déjà établissables peuvent continuer à être analysées.

## 3. Chercher pour résoudre chaque condition

Le skill oriente la recherche vers les textes applicables à l’acteur et à l’opération, dans leur version pertinente. Le MCP peut retrouver les textes, consulter des décisions et rechercher les pièces locales importées.

Pour chaque référence décisive, l’assistant doit obtenir le texte utile et conserver sa provenance. Un résultat de moteur de recherche reste une piste. Si une source est indisponible, la réponse indique ce qui n’a pas été vérifié et l’effet sur l’analyse.

## 4. Construire une justification que l’on peut relire

| Question | Éléments à relier | Conséquence attendue dans la note |
|---|---|---|
| Qui dispose du pouvoir de décider ? | Règles de compétence, personne morale et organe concerné | Motiver la qualification et la chaîne de pouvoir retenues. |
| Qui peut signer cet acte précis ? | Délégation, nature de l’acte, champ et exclusions | Expliquer pourquoi les pièces couvrent ou non l’acte envisagé. |
| Les versions et dates concordent-elles ? | Délibération, annexe, arrêté, dates d’effet et fait générateur | Identifier une éventuelle contradiction ou une pièce manquante. |
| Une objection change-t-elle l’issue ? | Qualification concurrente, exception, jurisprudence ou faits contestés | Répondre à l’argument le plus solide et ajuster la position. |

Pour un dossier complexe, cette justification peut être formalisée dans le schéma `Dossier`. L’outil `review_case` détecte des liens absents, empreintes divergentes ou citations introuvables. L’assistant et le juriste examinent toujours le contenu des applications et la conclusion.

## 5. Restituer une réponse directement utilisable

Une note peut suivre cette structure :

> **Position proposée.** Le périmètre du pouvoir de signature reste à confirmer sur le point identifié.
>
> **Motif décisif.** La délibération renvoie à une annexe susceptible de déterminer les actes autorisés ; cette pièce n’est pas disponible dans le dossier reçu.
>
> **Action suivante.** Retrouver l’annexe correspondant à cette version, vérifier le champ de l’autorisation et rapprocher cette pièce de la délégation produite.
>
> **Autres points.** Présenter séparément les vérifications déjà établies et celles qui dépendent encore d’une source ou d’un fait.

La note réelle inclut les références effectivement consultées et leurs passages utiles. Elle peut aussi expliquer comment adapter le projet ou quel organe saisir si une condition échoue.

## 6. Conserver le dossier pour pouvoir le réexaminer

Avec l’archive facultative, l’opérateur conserve un état du dossier et ses preuves. Une nouvelle capture peut révéler un changement de contenu ou de métadonnées. `compare_evidence` signale le besoin de réexamen ; l’analyse précise si ce changement modifie la position.

La date à laquelle une information est connue reste distincte de celle à laquelle une règle s’applique. La note historique demeure identifiable.

## Essayer la méthode

```text
Utilise $juriste-territorial pour préparer une note sur ce projet.

Objectif : déterminer les conditions à réunir avant la signature.
Acteur et qualité : […]
Dates pertinentes : […]
Pièces disponibles : […]

Distingue les faits établis des déclarations, vérifie la chaîne
compétence-signature et relie chaque condition à ses pièces.
Conserve les réserves décisives et propose une prochaine action utile.
```

[Retour à la présentation](../README.md) · [Dossiers structurés](../skills/juriste-territorial/references/dossier.md) · [Connexion aux sources](connexions-et-donnees.md).
