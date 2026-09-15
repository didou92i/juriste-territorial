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
uv sync --frozen
uv run --frozen droit-territorial status
uv run --frozen droit-territorial serve
```

Pour le client MCP, employer un chemin absolu vers `uv` si son environnement
ne connaît pas votre PATH. Exemple générique à adapter au client :

```json
{
  "mcpServers": {
    "droit-territorial": {
      "command": "uv",
      "args": ["--directory", "/CHEMIN/ABSOLU/juriste-territorial", "run", "--frozen", "droit-territorial", "serve"]
    }
  }
}
```

Les valeurs `/CHEMIN/ABSOLU/…` sont des emplacements à remplacer, pas des
configurations installées. Le format exact d'enregistrement dépend du client.
Le serveur publie les annotations de lecture seule et les capacités effectives.

## Accès aux API

L'opérateur fournit à l'environnement du processus :

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
uv run --frozen droit-territorial serve --transport streamable-http --port 8765
```

Adresse : `http://127.0.0.1:8765/mcp`. Le serveur reste lié à la boucle locale,
sans pièces privées. Ne pas exposer ce port par proxy ou tunnel comme service
partagé : il n'inclut pas l'authentification OAuth d'un service distant.

Une connexion distante ChatGPT nécessiterait notamment un serveur HTTPS et une
authentification adaptés. Ce déploiement n'est ni réalisé ni revendiqué ici.
Les transports sont vérifiés avec le client du SDK ; l'installation dans chaque
application reste à effectuer et à tester séparément.
