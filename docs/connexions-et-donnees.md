# De la source à votre assistant : comprendre les connexions

**Juriste territorial fournit un serveur MCP, `droit-territorial`, et un skill qui guide son utilisation.** La méthode, les accès documentaires et le modèle qui rédige ont des fonctions distinctes.

## Qui fait quoi ?

| Élément | Fonction | Où le configurer |
|---|---|---|
| Votre client et son modèle IA | Recevoir la demande, appeler les outils, analyser et rédiger | Dans votre application d’assistance IA |
| Le skill `juriste-territorial` | Donner la méthode et les références métier pertinentes | Dans le répertoire de skills du client, ou par les ressources de méthode du MCP |
| Le MCP `droit-territorial` | Exposer 14 outils de recherche, consultation, preuve et contrôle | Comme serveur MCP dans le client |
| Les API documentaires | Répondre aux requêtes autorisées | Avec les accès et abonnements requis pour les sources |
| Le connecteur data.gouv.fr, facultatif | Rechercher des jeux de données et consulter leurs ressources | Comme application ou MCP distinct dans le client |
| Les magasins locaux | Conserver les décisions importées, pièces et captures | Sur votre poste, selon les variables activées |

Le code du serveur ne choisit et n’appelle directement aucun fournisseur de modèle IA. C’est le client qui transmet les demandes et exploite les résultats. L’installation doit être testée dans ce client : la présence d’un fichier de configuration ne prouve pas qu’un outil est effectivement utilisé.

## Connexions livrées et conditions d’accès

### Légifrance via PISTE

L’adaptateur traite séparément les fonds : codes, législation, JORF, jurisprudence administrative et recherche constitutionnelle. Les articles consolidés exigent une date de consultation juridique. La résolution d’un article contrôle notamment son identité et la correspondance attendue avant de restituer la version.

- Accès : `PISTE_CLIENT_ID` et `PISTE_CLIENT_SECRET`, application autorisée pour l’API.
- Environnement : `PISTE_ENV=production` ou `sandbox`, avec les identifiants correspondants.
- État de la livraison : contrats simulés testés ; [recherche et lecture authentifiées réussies le 15 septembre 2026](connection-probes-2026-09-15.json). Le rapport v0.2.0 conserve son état historique ; la recette complète des versions historiques et incidents reste à poursuivre.
- Limite : la découverte constitutionnelle n’inclut pas une consultation API spécialisée ; la page officielle reste nécessaire.

[Documentation référencée par le projet](https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api).

### Justice administrative : CE, CAA et TA

L’opérateur choisit un ZIP mensuel du [portail officiel](https://opendata.justice-administrative.fr/index.html). La commande `import-admin` le télécharge et contrôle les XML avant leur indexation. Les lots, dates, identités et empreintes sont conservés.

Le MCP recherche ensuite dans **ce corpus importé**. Il filtre CE, CAA ou TA et les dates de décision. La recherche est lexicale ; il faut varier les termes et compléter la recherche lorsque la couverture ne répond pas à la question.

- Activation : `JT_ADMIN_DB` indique l’index à utiliser.
- État testé : 522 décisions importées dans trois lots historiques ; trois recherches suivies de consultations intégrales et de vérifications de citation.
- Suivi : import, correction et retrait sont des opérations explicites de l’opérateur ; aucune collecte périodique n’est activée.

[Guide d’import](admin-index.md) · [Preuves du test réel](admin-probes-0.2.0.json).

### ArianeWeb

Le skill peut guider une recherche sur [ArianeWeb](https://www.conseil-etat.fr/arianeweb/) avec le navigateur ou le moteur de recherche du client. Le lecteur du MCP peut consulter une page officielle compatible, si elle est accessible. Le projet ne livre pas d’API de recherche ArianeWeb propre ni de copie exhaustive de son corpus.

### JudiLibre via PISTE

L’adaptateur recherche et consulte la jurisprudence de l’ordre judiciaire, avec une gestion de la taxonomie des juridictions.

- Accès : `JUDILIBRE_KEY_ID`, ou les accès OAuth de l’application abonnée à l’API.
- État de la livraison : contrats simulés testés ; [recherche et lecture authentifiées réussies le 15 septembre 2026](connection-probes-2026-09-15.json) sur une installation.
- Usage : traiter les questions relevant du juge judiciaire, selon la qualification du dossier.

[Contrat officiel référencé](https://github.com/Cour-de-cassation/judilibre-search/blob/dev/public/JUDILIBRE-public.json).

### data.gouv.fr : compléter les faits du dossier

Le client peut appeler le [MCP officiel data.gouv.fr](https://github.com/datagouv/datagouv-mcp)
ou une application data.gouv.fr déjà disponible. Cette connexion est indépendante
des 14 outils juridiques et n'est pas installée par le simple téléchargement du skill.
L'adresse officielle est `https://mcp.data.gouv.fr/mcp`, sans clé selon la documentation
du fournisseur. Les API tierces référencées dans le catalogue conservent leurs
propres conditions d'accès ; leur découverte ne les connecte pas automatiquement.

Usages ciblés : comptes locaux, marchés publiés, intercommunalités. Le skill vérifie
le producteur, le millésime et le périmètre, puis rapproche les données des textes
et pièces du dossier. Chaque publication doit être qualifiée, même sur ce portail.

Le 15 septembre 2026, l'application disponible dans Codex a permis des recherches,
lectures de fiches et listes de ressources, puis la lecture de deux lignes BANATIC.
Le fichier de comptes communaux sélectionné était absent de l'API tabulaire.
[La recette](validation-datagouv.md) détaille ces résultats et leurs limites.

Les résultats externes ne reçoivent pas automatiquement les identifiants de preuve
ni l'archivage de `droit-territorial`. Leur état ne figure pas dans `get_source_status`.
La note doit conserver les références de la ressource et les paramètres consultés.

[Activer le connecteur](compatibility.md#datagouvfr-connecteur-facultatif-du-client)
· [Méthode d'exploitation](../skills/juriste-territorial/references/donnees-publiques.md).

### Pages institutionnelles

Le lecteur accepte uniquement des domaines HTTPS explicitement autorisés : notamment Légifrance, Conseil d’État, DGCL, ministère de l’Économie/DAJ, CNIL, CADA, DINUM, Conseil constitutionnel, EUR-Lex et Curia.

Il extrait une page ; il n’exécute pas une recherche générale sur tous ces sites. Les refus d’accès et les limites d’extraction sont conservés. Une page accessible ne garantit pas que son contenu extrait soit complet, à jour ou applicable au dossier.

La [liste effective des domaines](../src/droit_territorial/runtime.py) et le [registre des sources](../registry/sources.json) rendent ce périmètre vérifiable.

## Le parcours d’une preuve

1. **Recherche.** L’outil retourne des pistes et l’état de chaque source.
2. **Consultation.** `fetch` récupère un document supporté et crée une capture identifiée.
3. **Lecture.** L’assistant poursuit les pages nécessaires sur cette même capture.
4. **Traçabilité.** Le résultat contient provenance, empreinte du texte et métadonnées disponibles ; les inconnues restent visibles.
5. **Contrôle.** `check_evidence` recherche littéralement les citations et examine les métadonnées. `review_case` contrôle les liens déclarés du dossier.
6. **Interprétation.** L’assistant explique le rapport entre la règle, les faits et la conclusion ; le juriste examine le fond.

Une citation retrouvée dans les conclusions d’une partie ne devient pas un motif du juge. La détermination du sens, de la portée et des conditions de transposition relève de l’analyse.

## Où vont les données ?

| Opération | Flux et conservation |
|---|---|
| Recherche API | La requête est envoyée au fournisseur officiel ; formuler les recherches sans noms ni données sensibles inutiles. |
| Recherche data.gouv.fr | La requête et les filtres passent par le connecteur distant ; aucun envoi de pièce privée ou d'identifiant PISTE n'est nécessaire. Les résultats reviennent au client et à son modèle. |
| Import d’un lot administratif | Le ZIP vient du portail officiel et alimente l’index local configuré. |
| Import d’une pièce privée | Le texte et ses octets originaux sont enregistrés dans la base locale choisie ; cette commande ne les téléverse pas dans une API juridique. |
| Consultation par l’assistant | Les extraits et métadonnées sont transmis au client MCP ; leur traitement dépend ensuite du modèle et du fournisseur utilisés. |
| Archive facultative | `JT_EVIDENCE_DB` conserve les preuves et états de travail sur le poste, avec le principal configuré. |
| Retrait | La restitution par les outils est bloquée ; l’original et les sauvegardes ne sont pas automatiquement effacés. |

**Un serveur local peut être utilisé par un assistant dont le modèle est distant.** Examiner les conditions de traitement de ce client avant de lui soumettre un dossier sensible. Le projet ne garantit pas à lui seul un traitement intégralement local ou une conformité RGPD de votre déploiement.

Les clés sont fournies à l’environnement du processus. Le programme ne charge pas automatiquement de fichier `.env`. Les fichiers privés et secrets doivent rester hors du dépôt public.

## Vérifier votre installation

Le [parcours d'activation](../skills/juriste-territorial/references/installation.md)
est distribué avec le skill et accessible via `get_methodology(topic="installation")`.
`get_source_status` donne les accès manquants sans secret et sans appel API implicite.
Avec `probe=true`, il réalise une recherche publique et consulte un résultat pour
l'API choisie. Les clés peuvent provenir de l'environnement ou, sur activation
explicite, du trousseau système. Un redémarrage du MCP recharge les clés modifiées.

- Lancer `droit-territorial status` pour voir la configuration reconnue.
- Dans le client, appeler `get_source_status` et vérifier la présence des 14 outils.
- Rechercher une référence connue, la consulter et lire toutes les pages utiles.
- Vérifier la provenance retournée et une citation exacte ; noter les sources indisponibles.
- Faire examiner un dossier fictif avant d’adopter un circuit de travail réel.

`get_source_status` expose la configuration et les opérations observées ; son succès ne signifie pas que toutes les API viennent de répondre à une sonde réseau. En HTTP local, les pièces, index administratif et archives locaux sont désactivés. Le mode stdio convient au pilote individuel.

[Installer le client MCP](compatibility.md) · [Gérer les pièces](local-documents.md) · [Conserver les dossiers](case-records.md).
