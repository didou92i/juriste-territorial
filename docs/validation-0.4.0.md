# Validation technique 0.4.0

## Observé sur cette branche

- `uv run pytest -q` : 156 réussis, 1 test en ligne ignoré par défaut.
- `uv run python scripts/check_distribution.py` : références du skill et 14
  déclarations MCP cohérentes.
- PDF/DOCX synthétiques importés, empreintes et repères relus par les tests ;
  OCR local `pdftoppm` + Tesseract français exécuté manuellement sur une page
  PDF synthétique et a restitué « DECISION FICTIVE » avec un score de 91,24.
- `uv run ruff check .`, `uv run ruff format --check .` et `git diff --check` :
  réussis lors de la validation de la branche.

## Hors de portée de ces contrôles

Les [sondes PISTE du 15 septembre 2026](connection-probes-2026-09-15.json)
constatent recherche et lecture ponctuelles en production pour Légifrance et
JudiLibre sur une installation. Elles ne prouvent ni disponibilité actuelle,
ni version historique exacte, ni robustesse en panne. Les
[sondes CE/CAA/TA](admin-probes-0.2.0.json) portent sur trois lots et 522
décisions, pas sur une couverture nationale.

Les 40 scénarios et le corpus inédit ne sont pas des résultats juridiques
mesurés. Le [manifeste](../evals/holdout-manifest.json) fige 12 cas privés,
sans publier leurs contenus. Les trois configurations et les deux
relectures humaines par réponse restent à exécuter. Les modules demeurent
expérimentaux. Une réussite technique ou un OCR lisible ne certifie aucune
conclusion de droit.
