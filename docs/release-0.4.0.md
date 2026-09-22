# Évolution 0.4.0 — raisonnement et preuves contrôlables

Cette version renforce la traçabilité d'un dossier sensible. La fiche de
décision relie qualifications concurrentes, autorité, date, conditions
cumulatives ou alternatives, pièces, exception, objection et fait de bascule.
`review_case` détecte les références absentes, cycles et contradictions dans
le graphe **déclaré** ; il ne décide pas de la validité juridique.

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
