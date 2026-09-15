# Pièces privées locales

Le pilote importe du texte UTF-8 `.txt`/`.md`. Il conserve les octets originaux,
leur empreinte et le texte dans une base SQLite privée. Il ne prétend pas
extraire ou vérifier un scan ou un PDF.

```bash
uv run droit-territorial import-local piece.md \
  --db private/dossiers.sqlite --principal juriste-a \
  --case dossier-001 --title "Délibération à vérifier"
```

Configurer le processus MCP stdio avec `JT_LOCAL_DB` (chemin absolu) et
`JT_PRINCIPAL`. L'identité est définie par l'opérateur ; elle n'est jamais un
argument d'outil modifiable par le modèle. Un processus stdio correspond à un
utilisateur de confiance. La sécurité du compte système reste nécessaire.

La recherche filtre identité et dossier avant restitution des titres et
résultats. La consultation applique à nouveau l'identité ; les références
inconnues, retirées et non autorisées ont la même erreur. La révocation est
revérifiée avant de restituer un instantané déjà consulté.

```bash
uv run droit-territorial withdraw-local \
  --db private/dossiers.sqlite --principal juriste-a --id IDENTIFIANT
```

Cette commande retire le document des recherches et consultations ; elle
**ne supprime pas l'original de la base**. L'effacement, les sauvegardes et les
durées de conservation relèvent d'une procédure opérateur adaptée. Ne pas
confondre ce retrait avec l'exercice complet d'un droit à l'effacement.

Le HTTP local désactive les pièces privées. Un service partagé avec données
privées nécessite authentification, contrôle d'accès par dossier, séparation
des sessions et tests supplémentaires ; il n'est pas livré dans cette version.
