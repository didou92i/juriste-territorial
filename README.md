# Juriste territorial

**Passer de la recherche de textes à une position juridique motivée et utilisable.**

Un skill pour les collectivités et établissements publics locaux français,
accompagné du serveur MCP **droit-territorial**. Version **0.1.0 — pilote expérimental**.

## Ce qui fait la méthode

Le skill compare les qualifications possibles, établit la compétence et la date
pertinente, décompose les règles en conditions, les confronte aux pièces et
examine l'objection qui pourrait changer la conclusion. Il termine par une
position, ses réserves précises et une action réalisable.

```text
Question → qualifications → compétence et date → sources et pièces
         → conditions et application → objection → position et action
```

**Exemple :** une commune engage une consultation le 20 mars 2026 pour un besoin
de fournitures de 50 000 € HT. Une note écrite en septembre ne peut pas appliquer
rétroactivement le nouveau seuil de dispense. La méthode recherche le fait
générateur, la transition et le régime applicable avant de conseiller une procédure.
[R. 2122-8, version janvier–mars 2026](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000053221596/2026-01-01).

## Contenu livré

- **Un noyau canonique**, cinq références de raisonnement et de preuve,
  un contrat d'outils, des gabarits de notes, audits, actes, courriers et contentieux.
- **11 modules** : institutions, actes, FPT, dialogue social, commande publique,
  police, finances, urbanisme/patrimoine, services publics, données/numérique et contentieux.
- **11 outils MCP** : recherche fédérée, consultation, versions, jurisprudence,
  renvois, pièces privées, état des sources, méthode, preuves et règles bornées.
- **Connecteurs Légifrance/PISTE et JudiLibre**, lecteur de pages officielles,
  import local de textes, deux tests de seuils datés et tests automatisés.
- **40 scénarios de recette** et un premier essai de la méthode sur trois dossiers fictifs.

## Démarrage

### Skill

Installer le dossier [`skills/juriste-territorial/`](skills/juriste-territorial/)
dans le dossier de skills de votre client, puis demander :

> Utilise $juriste-territorial pour analyser ce dossier, ses preuves, les arguments
> contraires et la prochaine action utile.

Le skill peut employer les outils web officiels du client sans clé API.

### MCP

Avec Python 3.12+ et `uv` :

```bash
git clone https://github.com/didou92i/juriste-territorial.git
cd juriste-territorial
uv sync --frozen
uv run --frozen droit-territorial status
uv run --frozen droit-territorial serve
```

Les recherches API nécessitent les accès PISTE appropriés, fournis par
l'environnement du processus. Voir [installation et connexions](docs/compatibility.md).
Le serveur démarre sans clés et annonce précisément les capacités indisponibles.

## État de validation

Les tests techniques, l'essai indépendant par agent et les limites sont
consignés dans le [rapport de validation](docs/validation.md).
Ils ne constituent pas une validation juridique humaine ou un benchmark comparatif.

Le pilote expose un MCP **stdio** et **HTTP sur 127.0.0.1**. Il ne livre pas
de service distant partagé, d'index national XML, d'OCR ni de calcul général
des délais. Les appels API authentifiés doivent encore être validés avec des
accès PISTE. Tous les modules restent expérimentaux.

## Documentation

- [Architecture](docs/architecture.md) et [revue des dépôts sources](docs/source-review.md).
- [Plan finalisé et étapes suivantes](docs/development-plan.md).
- [Pièces locales et accès](docs/local-documents.md), [maintenance](docs/maintenance.md).
- [Évaluation](evals/README.md), [provenance](THIRD_PARTY.yml), [licences](LICENSE.md).

## Vérifier et construire

```bash
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen python scripts/check_distribution.py
uv build
uv run --frozen python scripts/package_skill.py
```

Code original sous **MIT** ; skill et documentation sous **CC BY-SA 4.0**,
avec attribution de la méthode de @brissonjo-sudo. Voir [NOTICE.md](NOTICE.md).
