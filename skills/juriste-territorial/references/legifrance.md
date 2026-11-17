# Consulter Légifrance par la voie disponible

Charger cette fiche lorsqu'une règle, sa version ou une décision doit être
recherchée ou vérifiée. Une simple reformulation ne déclenche pas de recherche.
Appliquer aussi [recherche et preuve](preuve-et-recherche.md) et
[temporalité](temporalite.md).

## 1. Choisir une seule route adaptée

Découvrir les outils réellement exposés dans la session et lire leur description
et leur schéma avant tout appel. Les noms et paramètres ne se devinent pas.
Une entrée de configuration MCP ou un exécutable local ne prouve ni l'exposition
des outils, ni une connexion vérifiée.

1. **MCP Légifrance dédié** : le privilégier s'il est exposé et adapté au fonds,
   à la date et à la lecture nécessaires ; suivre son schéma effectif.
2. **Adaptateur `droit-territorial`** : s'il est exposé et couvre le besoin,
   commencer par `get_source_status(source_id="legifrance", probe=false)`.
   Lire les limites et `setup` ; voir [le contrat](outils.md).
3. **Skill Légifrance installé** : s'il est découvert dans le catalogue ou à
   un emplacement vérifiable, lire son `SKILL.md` et utiliser ses capacités
   disponibles. Un skill est une méthode, pas une preuve de connexion.
4. **Web officiel** : à défaut de route utilisable, rechercher puis consulter
   les pages de [Légifrance](https://www.legifrance.gouv.fr/).

Ne pas installer de serveur, lancer un script configuré ou modifier des accès
pour contourner un outil absent. Signaler brièvement le repli utile.
Ne pas interroger deux connecteurs sur le même texte pour créer une fausse
corroboration : la source demeure identique. Changer de route seulement pour
combler une limite identifiée, puis noter ce motif.

## 2. Résoudre la question, puis lire la source

- Fixer la question, le fait générateur et la date juridique avant la requête.
  Employer des termes abstraits ; ne pas transmettre de dossier RH nominatif.
- Choisir le fonds : codes/textes consolidés pour la règle datée ; JORF pour
  publication, modification et transition ; jurisprudence pour l'interprétation.
- Avec `droit-territorial`, choisir explicitement `source_types` dans `search` :
  `codes`, `legislation`, `jorf` ou `case_law` selon le besoin. Fournir
  `as_of_date` pour les textes consolidés ; préciser l'ordre juridique utile.
  Pour `get_legal_version`, `text_ref` désigne le titre exact du code.
- Un résultat de recherche est une piste. Consulter le texte de la disposition
  décisive dans son intégralité, ses exceptions, renvois et mesures d'application.
  Pour une décision, lire les motifs utiles et le dispositif.
- Avec `fetch`, employer une référence effectivement obtenue. Suivre
  `next_offset` sur le même document via sa référence `evidence:` jusqu'aux
  passages et exceptions nécessaires ; signaler toute incomplétude restante.
  Pour les autres routes, suivre leur mécanisme réel de pagination.
- Vérifier version, intervalle applicable et dispositions transitoires.
  Une version actuelle, une différence textuelle ou la date de l'arrêt ne
  suffit pas à déterminer le droit applicable au dossier.

## 3. Conserver ce qui a été vérifié

Dans le fichier de contexte du dossier et son journal de recherche, noter :
question ; route et outil utilisés ; fonds/requête ; date juridique recherchée ;
titre, article ou numéro ; identifiant et lien officiels réellement retrouvés ;
version/date du document ; passage précis ; date de consultation ; résultat,
limite et conséquence pour l'analyse. Relier la conclusion à cette source.
Conserver l'identifiant de preuve ou la copie consultée lorsqu'ils sont disponibles.
Une nouvelle consultation du même original ne constitue pas une preuve indépendante.

Distinguer **outil non exposé**, **configuration non vérifiée**, **accès refusé**,
**panne/quota**, **fonds non couvert**, **version inconnue** et **zéro résultat**.
Aucun de ces états ne démontre à lui seul l'absence de règle ou de décision.
Réserver uniquement la conclusion affectée et indiquer la vérification restante.

Ne jamais demander de secret dans le chat, les arguments d'outil ou le contexte.
Un diagnostic actif (`probe=true`) consomme le quota et exige une demande
explicite de test ; ne pas le déclencher pour cette seule fiche. Pour les accès
manquants, suivre [l'installation](installation.md), sans bloquer les travaux
possibles ni annoncer une connexion sur la seule présence d'identifiants.
