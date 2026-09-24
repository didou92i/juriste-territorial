# Architecture et choix

## Séparer le raisonnement des outils

Le skill dirige la qualification, l'articulation, l'examen contradictoire et la
restitution. Le MCP fournit des documents et opérations contrôlées. Aucune
bibliothèque de modèle n'est obligatoire.

```mermaid
flowchart LR
  Q[Question et faits] --> K[Qualifications possibles]
  K --> C[Compétence et date]
  C --> S[Sources et pièces]
  S --> A[Conditions et application]
  A --> O[Objection et alternatives]
  O --> D[Position et action]
```

| Couche | Responsabilité |
|---|---|
| `skills/juriste-territorial/` | Méthode canonique, références à la demande, 11 modules et gabarits |
| `models.py` | Dossier, faits, document, intervalle de version, preuve, affirmation |
| `runtime.py` | HTTP borné, domaines fixes, OAuth, délais, erreurs et comptes d'appels |
| `sources.py` | Fonds Légifrance, JudiLibre, lecteur HTML officiel |
| `service.py` | Fédération, pagination par source, consultation, versions et renvois |
| `evidence.py` | Preuves émises par le serveur, empreintes et contrôles de citations |
| `local.py` + `extraction.py` | Import PDF/DOCX/texte, OCR PDF facultatif, originaux et lecture cloisonnée |
| `rules.py` + `registry/` | Tests monétaires bornés et registre des capacités |
| `dossier.py` | Fiche de décision, liens entre conditions et contrôle structurel des preuves |
| `archive.py` | Captures privées persistantes et notes immuables au niveau de l’API |
| `admin.py` | Import XML officiel, identifiants exacts et index lexical classé CE/CAA/TA |
| `evaluation.py` | Comparabilité des exécutions et contrôle des relectures déclarées |
| `server.py` | 14 outils MCP, ressources de méthode/sources et prompt d'analyse |

Le wheel embarque le même skill et le registre ; l'archive de skill est générée
à partir du même répertoire. Aucun noyau spécifique à un client n'est maintenu.

## Contrats de preuve

Le modèle ne peut pas créer une preuve officielle en transmettant un identifiant
à `check_evidence`. Les preuves proviennent de `fetch`, avec identité confirmée
dans la réponse API. Les résultats de recherche restent des pistes.

L'intervalle d'une version emploie une fin exclusive ; l'absence de fin est
distincte d'une fin explicitement ouverte. Le résultat temporel ne tranche ni
les transitions ni le champ matériel. Les dates des décisions ne deviennent
pas automatiquement les dates d'application du droit.

La consultation paginée poursuit un instantané, pas un texte changeant entre
deux appels. Taille du corps amont bornée, pages de sortie limitées, renvois
limités à 12 documents/profondeur 2, cache de preuves 32 documents/30 minutes.
La présence exacte d'une citation n'est pas une preuve de pertinence sémantique.

## Frontières de cette version

- Aucun index XML national CE/CAA/TA ni corpus vectoriel.
- Pas d'authentification HTTP multiutilisateur ni d'hébergement distant livré.
- Pas de collecte automatique de pièces privées ; l’OCR local reste une
  transcription non certifiée et les PDF/DOCX requièrent une revue visuelle.
- Pas de calcul général des délais ni de décision automatique de procédure d'achat.
- Les tests d'API simulés ne remplacent pas les recettes avec accès PISTE réel.

Ces limites sont aussi exposées dans le manifeste de sources et la méthode.
