# Recette data.gouv.fr — 15 septembre 2026

## Périmètre observé

Appels réels de l'application data.gouv.fr disponible dans une session Codex.
Aucun nouveau serveur local n'a été enregistré en doublon. La recette porte sur
ces opérations à cet instant ; elle ne valide pas l'installation dans tous les
clients ni l'ensemble des fichiers du catalogue.

| Appel | Observation |
|---|---|
| Recherche `comptes individuels communes`, page de 3 résultats | 65 jeux annoncés ; 3 résultats retournés |
| Fiche et ressources du jeu `68e5aa59cf61185939ecc33b` | Producteur : Ministères économiques et financiers ; exercices 2023-2024 ; 3 ressources |
| Lecture tabulaire `6adb3821-1324-4ba8-a5e9-e805c08b9c7c`, 2 lignes demandées | Message : ressource absente de l'API tabulaire, malgré `isError=false` ; aucune ligne lue |
| Recherche `BANATIC`, page de 2 résultats | 28 jeux annoncés ; 2 résultats retournés |
| Fiche et ressources du jeu `5e1f20058b4c414d3f94460d` | Producteur : DGCL ; 7 ressources ; mise à jour de fiche au 15 septembre 2026 |
| Lecture tabulaire `25571b3e-a5ce-4567-bfb4-650504644d7b`, page 1, 2 lignes | 2 lignes retournées ; total annoncé de 9 578 ; fichier intitulé `liste-des-groupements-france-entiere-20250127.csv` |

Sources consultées : [comptes communaux](https://www.data.gouv.fr/datasets/comptes-individuels-des-communes-fichier-global-2023-2024)
et [BANATIC](https://www.data.gouv.fr/datasets/base-nationale-sur-les-intercommunalites).
Les identifiants ci-dessus proviennent des réponses du catalogue.

## Ce que la recette démontre

La connexion utilisée dans cette session permet la recherche, la consultation des
métadonnées et une lecture tabulaire. Elle expose aussi une limite réelle : un
CSV référencé n'est pas nécessairement accessible par l'API tabulaire. Le skill
demande de lire le contenu de la réponse et de suivre, si possible, le lien du
producteur. Ce repli n'a pas été testé sur le fichier de comptes communaux.

La date récente d'une fiche BANATIC ne rend pas actuel son fichier de janvier 2025.
Les deux lignes ne constituent ni une lecture exhaustive ni une preuve de la
compétence juridique actuelle d'un groupement. Aucun chiffre relatif aux personnes
physiques présentes dans le fichier n'est reproduit ici.

## Cas de réception de la méthode

Ces scénarios sont un protocole de relecture à exécuter avec le modèle du client,
pas un benchmark déjà validé :

- **Question de droit seule** : ne pas déclencher data.gouv.fr sans fait à résoudre.
- **Compétence d'un EPCI** : distinguer fiche, date du fichier, statuts et arrêtés.
- **Marché introuvable** : décrire filtres et couverture, sans déduire son inexistence.
- **CSV non pris en charge** : signaler la limite et chercher une lecture chez le producteur.
- **Comparaison de comptes** : vérifier exercices, unités et périmètres avant calcul.

Le [guide distribué](../skills/juriste-territorial/references/donnees-publiques.md)
est également accessible par `get_methodology(topic="donnees-publiques")`.
