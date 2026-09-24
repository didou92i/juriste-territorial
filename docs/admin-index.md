# Index administratif local

Le portail officiel distribue des ZIP de XML par mois et ordre de juridiction.
Le format lu est documenté par le producteur dans [l’aide du portail](https://opendata.justice-administrative.fr/aide.html).
Les [lots CE, CAA et TA](https://opendata.justice-administrative.fr/index.html)
complètent la sélection jurisprudentielle d’ArianeWeb. La date d’ouverture annoncée
par le portail n’est pas nécessairement la première date de décision d’un lot.

## Utiliser

Choisir une URL exacte dans l’index officiel. L’import est une commande opérateur,
jamais un outil MCP déclenché par une pièce jointe :

```bash
uv run droit-territorial import-admin \
  https://opendata.justice-administrative.fr/DCE/2021/09/CE_202109.zip \
  --db /chemin/prive/admin.sqlite
export JT_ADMIN_DB=/chemin/prive/admin.sqlite
uv run droit-territorial serve
```

Appeler `search_admin_archive(query, courts=["CE", "CAA", "TA"])`, puis
`fetch(source_ref="admin:...")`. Suivre `next_offset` avec la référence
`evidence:` reçue. Dates de décision et lots importés apparaissent dans la couverture.
Un numéro, ECLI ou identifiant XML exact est recherché avant le texte. Pour une
recherche textuelle, l’index classe les résultats par BM25 ; les mots d'une
requête doivent tous être présents, mais chaque `variants` (trois au plus)
ouvre une autre formulation. Le classement est lexical et ne juge pas la
portée d’une décision. Pour une recherche fondée sur l’apport au droit,
[le portail officiel conseille ArianeWeb](https://opendata.justice-administrative.fr/aide.html).
L’offset concerne un index stable : recommencer la recherche après un nouvel import.

## Provenance, intégrité et retrait

L’outil télécharge uniquement une URL mensuelle du domaine officiel, sans redirection.
Il conserve XML, empreinte du XML et du ZIP, URL, date d’import, identité, ECLI
si présent, type de décision et code de publication. Ces derniers ne sont pas
convertis en score d’autorité. Les paragraphes sont conservés dans le texte extrait.

Un lot invalide échoue entièrement. Limites : ZIP de 64 Mo, 200 Mo décompressés,
15 000 entrées, 2 Mo par XML ; pas d’extraction sur disque, DTD/entités refusées.
Les formats au-delà de ces limites doivent être examinés avant adaptation.
Un réimport du même lot est idempotent ; un XML modifié remplace l’entrée courante,
sans réactiver une entrée retirée. Les preuves déjà archivées restent historiques.

```bash
uv run droit-territorial withdraw-admin NOM_FICHIER.xml --db /chemin/prive/admin.sqlite
```

Le retrait bloque recherche, consultation et anciennes preuves. Il ne supprime
pas physiquement le texte ni les sauvegardes. La liste `JT_WITHDRAWN_IDS` permet
aussi un blocage au démarrage. Le suivi des corrections/retraits du producteur
reste manuel. L’index et l’archive privée sont désactivés en transport HTTP.

## Preuve de fonctionnement

`scripts/probe_admin.py --db /chemin/prive/recette.sqlite` télécharge trois petits
lots historiques, recherche trois décisions connues, lit toutes leurs pages et
contrôle une citation et les empreintes. Le [résultat conservé](admin-probes-0.2.0.json)
porte sur **522 décisions importées et trois consultations détaillées**.
Il ne mesure ni rappel, ni classement sur un corpus national, ni interprétation juridique.
