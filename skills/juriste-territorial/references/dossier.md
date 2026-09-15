# Dossier contrôlable et conservation de la preuve

Pour un dossier concret complexe, construire une justification explicite avant
de conclure. Une question générale ou une simple reformulation n'exige pas de JSON.

## Contrat de raisonnement

- `context` : personne morale, qualité de l'auteur, objectif, fait générateur,
  dates des événements et faits distingués par leur niveau de preuve.
- `knowledge_cutoff` : instant jusqu'auquel les informations étaient connues,
  distinct de la date à laquelle le droit s'applique. Une pièce découverte plus
  tard peut justifier une nouvelle note, sans réécrire la note historique.
- `qualifications` : branches plausibles lorsque le statut ou la nature de
  l'opération est discuté ; une qualification unique suffit si elle est établie.
- `pieces` : référence `evidence_id` réellement délivrée par `fetch`, empreinte
  attendue, rôle et identifiant court. Un fait établi renvoie à ces identifiants,
  et son contenu doit effectivement être prouvé par la pièce.
- `conditions` : question, citation de règle avec date pertinente, faits concernés,
  application motivée, appréciation, objection, conséquence et action suivante.
- `grounds` : rattacher chaque moyen aux conditions concernées ; distinguer
  recevabilité, compétence, procédure, fond et preuve. Expliquer l'effet demandé
  et ses limites : un vice ne produit pas automatiquement annulation, injonction
  ou indemnisation, et un moyen faible ne fait pas disparaître les autres.
- `decisions` : suivre [la fiche jurisprudence](jurisprudence.md).

Le schéma complet se génère avec `droit-territorial case-schema` ; le MCP expose
le même schéma dans `review_case`. Celui-ci détecte des défauts de références,
citations, dates et structure. Même sans anomalie, la vérité des faits, le sens
des citations, l'exhaustivité des conditions et la conclusion restent à examiner.

## Pièces qui se répondent

Pour une annexe, approbation, délégation, mise en œuvre ou substitution, noter les
deux pièces et le passage qui affirme leur lien. Vérifier ensuite le bon auteur,
le champ, la version, la signature, les réserves, la publicité et la date d'effet.
La présence d'un lien ou d'un visa ne prouve pas une habilitation valable.
Une signature à compléter n'est pas une signature constatée ; un accord déclaré
n'est pas une délibération retrouvée. Ne pas présumer que « bureau » désigne un
organe public : identifier d'abord la personne morale et ses règles propres.

## Historique et réexamen

L'opérateur peut activer une archive privée avec `JT_EVIDENCE_DB` et
`JT_PRINCIPAL` en stdio. Les preuves sont alors conservées au-delà de la session.
`record-case` enregistre une note et son rapport sous un nouvel identifiant ;
`read-case` restitue cet état et un contrôle actuel des accès. `compare_evidence`
compare deux captures du même document et signale un besoin de réexamen.

Une empreinte établit une différence d'octets, pas sa conséquence juridique.
Les retraits interdisent la restitution par l'outil ; la suppression physique,
les sauvegardes et la durée de conservation relèvent de l'opérateur. Aucune
surveillance périodique des sources n'est activée par cette fonctionnalité.
