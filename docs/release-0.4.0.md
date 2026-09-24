# Évolution 0.4.0 — droit positif, raisonnement et preuves contrôlables

## Des modules ancrés dans le droit positif

- **Ancrages à vérifier** dans les 11 modules historiques : articles pivots du
  CGCT, CGFP, CCP, CJA, CRPA, CSI, CG3P et arrêts de principe (*Danthony*,
  *Czabaj*, *Tarn-et-Garonne*, *Benjamin*, *Dahan*…), comme points de départ
  de la recherche.
- **Pièges fréquents** par domaine : délégations devenues caduques, relevé
  d'identité, fractionnement, recours gracieux en urbanisme, subventions, CADA.
- **Deux nouveaux modules** : élus et déontologie (conflit d'intérêts, déport,
  432-12 après la loi n° 2025-1249, déontologie des agents) ; responsabilités
  administrative, pénale et des gestionnaires publics.
- **Veille datée** (`references/veille.md`) : partie réglementaire du CGFP,
  seuil de dispense 2026, L. 600-12-2 C. urb., statut de l'élu, projet de loi
  polices municipales non adopté, omnibus IA, élections professionnelles 2026.
- **Méthode** : interprétation des textes, répartition de la preuve, intensité
  du contrôle du juge et devenir du vice, échelle verbale de solidité, contrôle
  final en dix questions.

Ces références ont été relevées le 2026-09-24 à partir de sources officielles
et de fiches professionnelles ; elles n'ont pas fait l'objet d'une revue
juridique humaine indépendante. Les modules restent expérimentaux.

## Raisonnement et preuves contrôlables

La fiche de décision relie qualifications concurrentes, autorité, date,
conditions cumulatives ou alternatives, pièces, exception, objection et fait de
bascule. `review_case` détecte les références absentes, cycles et contradictions
dans le graphe **déclaré** ; il ne décide pas de la validité juridique.

La recherche CE/CAA/TA privilégie les numéros et ECLI exacts, puis classe les
termes et variantes dans les seuls lots XML importés. Elle restitue la
couverture effective et oriente vers ArianeWeb pour la portée jurisprudentielle.
Les pièces locales PDF et DOCX sont importables avec l'original et des repères
de page/paragraphe ; l'OCR PDF facultatif signale ses passages incertains.

La recherche fédérée exige un choix explicite des fonds et expose durée et
appels observés. Le coût du fournisseur reste `not_reported` faute de donnée.
Un protocole de corpus inédit à trois bras et double relecture humaine est
préparé ; aucune performance juridique comparative n'est encore revendiquée.

Voir [la validation technique](validation-0.4.0.md),
[le protocole](../evals/README.md) et [les limites de l'index](admin-index.md).
