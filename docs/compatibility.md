# Installation et compatibilité

## Skill autonome

Copier `skills/juriste-territorial/` dans le dossier de skills du client, sous
le nom `juriste-territorial`, en conservant références, modules, gabarits et licence.
Pour Codex : `~/.codex/skills/juriste-territorial/`.
Pour un client sans chargement de skills, appeler `get_methodology` ou lire
la ressource `juriste://methodology/core` depuis le MCP.

La disponibilité de la méthode ne prouve pas que le client la charge ou la suit.
Le test de réception doit observer un cas réel et ses appels de sources.

## Serveur MCP local

Prérequis : Python 3.12 ou plus et `uv`.

```bash
git clone https://github.com/didou92i/juriste-territorial.git
cd juriste-territorial
uv sync --frozen --extra credentials
uv run --frozen --extra credentials droit-territorial status
uv run --frozen --extra credentials droit-territorial serve
```

Pour le client MCP, employer un chemin absolu vers `uv` si son environnement
ne connaît pas votre PATH. Exemple générique à adapter au client :

```json
{
  "mcpServers": {
    "droit-territorial": {
      "command": "uv",
      "args": ["--directory", "/CHEMIN/ABSOLU/juriste-territorial", "run", "--frozen", "--extra", "credentials", "droit-territorial", "serve"],
      "env": {"JT_CREDENTIAL_STORE": "keyring", "PISTE_ENV": "production"}
    }
  }
}
```

Les valeurs `/CHEMIN/ABSOLU/…` sont des emplacements à remplacer, pas des
configurations installées. Le format exact d'enregistrement dépend du client.
Le serveur publie les annotations de lecture seule et les capacités effectives.

### Enregistrer dans Codex

Après installation des dépendances, depuis la racine du dépôt, sur macOS/Linux :

```bash
codex mcp add droit-territorial --env JT_CREDENTIAL_STORE=keyring --env PISTE_ENV=production -- "$PWD/.venv/bin/python" -m droit_territorial.cli serve
```

Sous Windows, employer le chemin absolu vers `.venv\Scripts\python.exe`.
Ne placer aucun secret dans `--env` ; les deux valeurs ci-dessus ne sont pas secrètes.
Ouvrir une nouvelle session Codex si nécessaire, puis appeler `get_source_status`.
Le client doit exposer les 14 outils. Le skill s'installe séparément comme indiqué plus haut.
Pour Claude Desktop ou un autre client stdio, adapter le JSON générique ci-dessus.
Ces exemples ne garantissent pas la compatibilité de toutes les versions des clients.

## Accès aux API

**Commencer par le [guide d'activation des sources](../skills/juriste-territorial/references/installation.md).**
Au premier usage, le MCP fournit ce guide et les accès manquants dans `get_source_status`.
Le skill et les instructions du serveur demandent à l'assistant de les présenter brièvement.

```bash
uv run --frozen --extra credentials droit-territorial configure piste
JT_CREDENTIAL_STORE=keyring uv run --frozen --extra credentials droit-territorial doctor --probe
```

La saisie masquée écrit dans le trousseau système et confirme l'enregistrement.
Le diagnostic suivant réalise une recherche publique puis une lecture. Le statut
sans `--probe` ne contacte pas les API. Redémarrer le MCP après modification des clés.

Sur un hébergement sans trousseau, l'opérateur fournit via son gestionnaire de secrets
à l'environnement du processus (`JT_CREDENTIAL_STORE=environment`, option par défaut) :

- `PISTE_CLIENT_ID`, `PISTE_CLIENT_SECRET` pour Légifrance ;
- `JUDILIBRE_KEY_ID` ou les accès OAuth de l'application abonnée à JudiLibre ;
- `PISTE_ENV=production` (défaut) ou `sandbox`, avec les accès du même environnement.

Utiliser le gestionnaire de secrets du système ou du client. Le programme ne
lit pas automatiquement les fichiers `.env` et ne contient aucun identifiant.
Ne pas placer les valeurs dans Git ni les recopier dans une conversation.
La souscription aux API et l'acceptation de leurs CGU se font sur PISTE.

Sans identifiants : méthode, règles bornées, pièces privées configurées et lecteur
de pages officielles restent disponibles ; les recherches API annoncent
`credentials_missing`. Le client peut employer sa recherche web officielle.

## HTTP local

```bash
uv run --frozen --extra credentials droit-territorial serve --transport streamable-http --port 8765
```

Adresse : `http://127.0.0.1:8765/mcp`. Le serveur reste lié à la boucle locale,
sans pièces privées. Ne pas exposer ce port par proxy ou tunnel comme service
partagé : il n'inclut pas l'authentification OAuth d'un service distant.

Une connexion distante ChatGPT nécessiterait notamment un serveur HTTPS et une
authentification adaptés. Ce déploiement n'est ni réalisé ni revendiqué ici.
Les transports sont vérifiés avec le client du SDK ; l'installation dans chaque
application reste à effectuer et à tester séparément.
