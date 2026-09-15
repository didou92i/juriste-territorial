# Activer vos sources juridiques

## Au premier échange

Appeler `get_source_status`. Lire `setup`, les états des sources et les éventuelles
erreurs du trousseau. Présenter une seule fois les accès utiles au dossier qui
manquent, puis poursuivre avec les capacités disponibles. Exemple :

> La méthode est disponible. Pour interroger directement Légifrance, configurez
> vos deux identifiants PISTE dans votre terminal ou votre gestionnaire de secrets.
> Je peux vous guider ; ne les collez pas dans cette conversation.

Si le MCP est absent, expliquer son installation depuis le dépôt. Ne pas prétendre
avoir consulté `get_source_status`. Un client doit charger le skill ou suivre les
instructions MCP pour que ce rappel soit présenté ; le serveur n'ouvre aucun dialogue
de saisie à distance et ne garantit pas le comportement du modèle.

## De quels accès avez-vous besoin ?

| Besoin | Configuration |
|---|---|
| Codes, textes, JORF et fonds jurisprudentiels Légifrance | `PISTE_CLIENT_ID` + `PISTE_CLIENT_SECRET` |
| Jurisprudence judiciaire JudiLibre (facultatif) | `JUDILIBRE_KEY_ID` ou application OAuth abonnée à JudiLibre |
| Index administratif CE/CAA/TA | Aucune clé ; importer les lots et définir `JT_ADMIN_DB` |
| Méthode et lecture de pages officielles autorisées | Aucune clé API |

Sur [PISTE](https://piste.gouv.fr/), créer une application, sélectionner l'API
Légifrance et accepter ses CGU. Récupérer le couple d'identifiants OAuth dans
l'environnement choisi. Production et sandbox ont des identifiants distincts.
Voir la [FAQ officielle Légifrance](https://www.legifrance.gouv.fr/contenu/pied-de-page/foire-aux-questions-api).

## Ordinateur personnel : saisie locale protégée

Depuis le dépôt installé avec Python 3.12+ et `uv` :

```bash
uv sync --frozen --extra credentials
uv run --frozen --extra credentials droit-territorial configure piste
```

La commande masque les deux saisies et stocke le couple dans le trousseau système.
Elle n'accepte ni clés en arguments, ni saisie depuis un outil MCP. Trousseaux
pris en charge : macOS, Windows Credential Manager et Linux Secret Service avec
session déverrouillée. Aucun repli vers un fichier en clair.

Configurer ensuite ces **valeurs non secrètes** dans le processus MCP :

```text
JT_CREDENTIAL_STORE=keyring
PISTE_ENV=production
```

Pour sandbox : `configure piste --environment sandbox` et `PISTE_ENV=sandbox`.
Pour une clé JudiLibre facultative : `configure judilibre` dans le même environnement.
Relancer la commande permet de remplacer son profil. Supprimer un profil se fait
dans le gestionnaire de mots de passe du système, sous le service
`juriste-territorial.piste.production` (ou fournisseur/environnement correspondant).

Redémarrer le processus MCP après toute modification. Les identifiants sont chargés
au démarrage. Une autorisation du Trousseau macOS peut être demandée par le système.

## Hébergement, conteneur ou processus sans trousseau

Dans le gestionnaire de secrets de l'hébergeur, fournir au **processus serveur**
`PISTE_CLIENT_ID`, `PISTE_CLIENT_SECRET` et `PISTE_ENV`. Laisser
`JT_CREDENTIAL_STORE=environment` (défaut). Pour JudiLibre, ajouter si nécessaire
`JUDILIBRE_KEY_ID`. Aucun abonnement à un fournisseur de modèle IA n'est requis
par ce serveur MCP lui-même ; le client IA conserve ses propres prérequis.

Ne jamais placer les valeurs dans le dépôt, le README, des arguments de commande,
un ticket ou le chat. Les fichiers `.env` ne sont pas chargés automatiquement.
La présence d'une seule variable OAuth dans l'environnement donne priorité au
couple de cet environnement : aucun mélange avec un couple du trousseau.
Une variable vide explicite désactive donc ce repli.

Ce support de variables facilite l'hébergement du processus ; il ne fournit pas
un service MCP distant sécurisé prêt à exposer. Le HTTP livré reste sur
`127.0.0.1`, sans magasins locaux ; un service distant exige HTTPS, authentification
et isolation adaptées.

## Confirmer la connexion

Dans le client : `get_source_status(source_id="legifrance", probe=true)`.
Le diagnostic lance une recherche publique prédéfinie et consulte un
résultat ; il utilise le quota du fournisseur. Par défaut, `probe=false` ne fait
aucun appel API. La même vérification existe en terminal :

```bash
JT_CREDENTIAL_STORE=keyring uv run --frozen --extra credentials droit-territorial doctor --probe
```

| État | Signification et suite |
|---|---|
| `configured_not_verified` / `configured_not_probed` | Identifiants présents ; lancer le diagnostic |
| `not_run` + `credentials_missing` | Identifiants absents ou incomplets ; les configurer |
| `credential_store_unavailable` | Trousseau verrouillé/indisponible ou option non installée |
| `verified_search_and_fetch` | Recherche et lecture réussies à cet instant |
| `reachable_empty_result` | Réponse sans résultat ; aucune lecture de document validée |
| `authorization_required` | Vérifier identifiants, environnement, abonnement et CGU |
| `quota_exceeded` / `source_unavailable` | Attendre ou réessayer ; ne pas conclure à l'absence de droit |

Pour JudiLibre, utiliser `source_id="judilibre"` ou `doctor --probe --source judilibre`.
Un test de connexion réussi ne valide ni les versions historiques, ni l'exhaustivité,
ni une conclusion juridique. Ne jamais annoncer « toutes les API connectées » sur
la seule présence de clés.
